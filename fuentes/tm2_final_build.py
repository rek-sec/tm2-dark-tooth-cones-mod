# Construye la version final en una carpeta NUEVA: SCUS_943.06 + .bin + .cue. Parte de los originales y no modifica nada existente.
import sys, os, re, zlib, time, tempfile, hashlib, shutil
T = tempfile.gettempdir(); sys.path.insert(0, T)
import tm2_caves as C, tm2_final as FN, tm2emu2, tm2cd
SRC_EXE = C.EXE
SRC_BIN = r'D:\Twisted Metal\TM2\TM2 Singletrac V3.6\Singletrac V3.6.bin'
SRC_CUE = r'D:\Twisted Metal\TM2\TM2 Singletrac V3.6\Singletrac V3.6.cue'
OUT, NAME = FN.OUT, FN.NAME
R0 = r'D:\Twisted Metal\TM2'
KEEP = [R0 + r'\TM2 Singletrac V3.6 Conos\SCUS_943.06', R0 + r'\TM2 Singletrac V3.6 Conos\Singletrac V3.6 Conos.bin',
        R0 + r'\TM2 Singletrac V3.6 Mod by Rek\SCUS_943.06', R0 + r'\TM2 Singletrac V3.6 Mod by Rek\Singletrac V3.6 Mod by Rek.bin']
log = open(os.path.join(T, 'tm2_final_build.log'), 'w', encoding='utf-8')
def out(s): log.write(time.strftime('%H:%M:%S ') + s + '\n'); log.flush()
def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 24), b''): h.update(c)
    return h.hexdigest()
try:
    TA = 0x800CDC54; fo = lambda a: a - TA + 0x800; ZA, ZE = 0x801A4DD4, 0x801BF3B4; zlen = ZE - ZA
    d = open(SRC_EXE, 'rb').read(); exe0 = hashlib.md5(d).hexdigest(); bin0 = md5f(SRC_BIN); keep0 = [md5f(p) for p in KEEP]
    out('originales: EXE md5=%s | BIN md5=%s' % (exe0, bin0))
    assert exe0 == 'be1573c5392a834733d9f2683e90ab61', 'el EXE de origen no es el analizado'
    # ---------- FASE 1: ejecutable ----------
    pay = zlib.decompressobj(-15).decompress(d[fo(ZA):fo(ZE)]); comps = FN.comps(True); new = bytearray(pay); exe = bytearray(d)
    for c in comps:
        if c['addr'] >= 0x80640000: buf, o = new, c['addr'] - 0x80640000
        else: buf, o = exe, fo(c['addr'])
        assert bytes(buf[o:o + len(c['old'])]) == c['old'], 'bytes originales inesperados en ' + c['name']
        buf[o:o + len(c['new'])] = c['new']
        out('  %-2s %08X %3d bytes -> %-34s %s' % (c['name'], c['addr'], len(c['new']), 'bloque comprimido del mod' if buf is new else 'EXE offset 0x%X (sin comprimir)' % o, c['desc']))
    new = bytes(new); defl = open(os.path.join(T, 'tm2_payload_final.deflate'), 'rb').read()
    assert zlib.decompressobj(-15).decompress(defl) == new, 'el flujo comprimido no corresponde al bloque final'
    assert len(defl) <= zlen, 'el flujo comprimido no cabe'
    exe[fo(ZA):fo(ZE)] = defl + bytes(zlen - len(defl)); exe = bytes(exe)
    R = [c for c in comps if c['name'] == 'R'][0]; ro = fo(R['addr'])
    stray = sum(1 for i in range(len(d)) if d[i] != exe[i] and not (ro <= i < ro + len(R['new']) or fo(ZA) <= i < fo(ZE)))
    out('EXE nuevo: %d bytes (original %d) | cabecera identica=%s | flujo comprimido %d de %d bytes (%d de relleno a cero) | bytes cambiados fuera de los dos tramos previstos: %d' % (len(exe), len(d), exe[:0x800] == d[:0x800], len(defl), zlen, zlen - len(defl), stray))
    assert len(exe) == len(d) and exe[:0x800] == d[:0x800] and stray == 0
    t0 = time.time(); res, steps, mem = tm2emu2.boot_payload(exe); g = lambda a, n: bytes(mem[a & 0x7FFFFF:(a & 0x7FFFFF) + n])
    okp = g(0x80640000, len(new)) == new; okc = all(g(c['addr'], len(c['new'])) == c['new'] for c in comps)
    s = [g(FN.STR_ADDR, 18), g(FN.STR_ADDR + FN.STR_SLOT, 18), g(0x8067FA6C, 12), g(0x8067FA90, 12)]
    out('arranque REAL del EXE nuevo en el interprete: %s (%d instrucciones, %.0f s) | bloque descomprimido == bloque final: %s | todos los tramos en su sitio: %s' % (res, steps, time.time() - t0, okp, okc))
    out('textos ya descomprimidos: largos %r / %r | cortos (2 jugadores) %r / %r' % (s[0], s[1], s[2], s[3]))
    assert res == 'ok' and okp and okc and s == [FN.TEXTS[0] + b'\0', FN.TEXTS[1] + b'\0', b'L3: CONE 1\0\0', b'L3: CONE 2\0\0'], 'el EXE nuevo no arranca bien en el interprete'
    pe = open(KEEP[0], 'rb').read(); ppay = zlib.decompressobj(-15).decompress(pe[fo(ZA):fo(ZE)])
    dif = [0x80640000 + i for i in range(len(new)) if ppay[i] != new[i]]
    zones = [(FN.STR_ADDR, C.T_END), (FN.SITE, FN.SITE + 28)]
    outz = sum(1 for i in range(len(pe)) if pe[i] != exe[i] and not fo(ZA) <= i < fo(ZE))
    out('respecto a la version Conos (la que probaste en partida): %d bytes distintos en el bloque descomprimido, todos dentro de %s: %s | bytes del EXE distintos fuera del flujo comprimido: %d' % (len(dif), ['%08X..%08X' % z for z in zones], all(any(l <= a < h for l, h in zones) for a in dif), outz))
    assert len(ppay) == len(new) and dif and all(any(l <= a < h for l, h in zones) for a in dif) and outz == 0
    # ---------- FASE 2: imagen de disco ----------
    os.makedirs(OUT, exist_ok=False)
    nexe = os.path.join(OUT, 'SCUS_943.06'); nbin = os.path.join(OUT, NAME + '.bin'); ncue = os.path.join(OUT, NAME + '.cue')
    open(nexe, 'wb').write(exe)
    lba, size = tm2cd.find_file(SRC_BIN, 'SCUS_943.06;1'); ns = size // 2048
    assert size == len(exe) and size % 2048 == 0
    shutil.copyfile(SRC_BIN, nbin)
    with open(nbin, 'r+b') as f:
        for k in range(ns):
            f.seek((lba + k) * 2352); sct = bytearray(f.read(2352))
            assert tm2cd.check_m2f1(sct) and bytes(sct[24:2072]) == d[k * 2048:(k + 1) * 2048], 'sector %d inesperado' % (lba + k)
            sct[24:2072] = exe[k * 2048:(k + 1) * 2048]; tm2cd.fix_m2f1(sct)
            f.seek((lba + k) * 2352); f.write(sct)
    lo, hi = lba, lba + ns; outside = inside = 0; n = 0
    with open(SRC_BIN, 'rb') as fa, open(nbin, 'rb') as fb:
        while True:
            a = fa.read(2352 * 4096); b = fb.read(2352 * 4096)
            if not a and not b: break
            if a != b:
                assert len(a) == len(b)
                for i in range(0, len(a), 2352):
                    if a[i:i + 2352] != b[i:i + 2352]:
                        if lo <= n + i // 2352 < hi: inside += 1
                        else: outside += 1
            n += len(a) // 2352
    got = bytearray(); good = hdr = 0
    with open(nbin, 'rb') as fb, open(SRC_BIN, 'rb') as fa:
        for k in range(ns):
            fb.seek((lba + k) * 2352); sct = fb.read(2352); fa.seek((lba + k) * 2352); s0 = fa.read(2352)
            got += sct[24:2072]; good += tm2cd.check_m2f1(sct); hdr += sct[:24] == s0[:24]
    l2, s2_ = tm2cd.find_file(nbin, 'SCUS_943.06;1')
    out('BIN nuevo: %d bytes | sectores distintos del original: %d dentro del EXE (LBA %d..%d), %d fuera | EDC/ECC correctos: %d de %d | cabeceras de sector intactas: %d de %d | EXE leido de la imagen == EXE nuevo: %s | entrada ISO: LBA %d, %d bytes' % (os.path.getsize(nbin), inside, lo, hi - 1, outside, good, ns, hdr, ns, bytes(got) == exe, l2, s2_))
    assert outside == 0 and good == ns and hdr == ns and bytes(got) == exe and (l2, s2_) == (lba, size) and os.path.getsize(nbin) == os.path.getsize(SRC_BIN)
    cue = open(SRC_CUE, 'rb').read(); cue2, k = re.subn(rb'^FILE "[^"]*"', b'FILE "' + (NAME + '.bin').encode() + b'"', cue, count=1)
    assert k == 1; open(ncue, 'wb').write(cue2)
    out('CUE nuevo: primera linea = %s | resto identico al original: %s' % (cue2.splitlines()[0].decode(), cue2.splitlines()[1:] == cue.splitlines()[1:]))
    src = os.path.join(OUT, 'fuentes'); os.makedirs(src)
    for fn in ('tm2asm.py', 'tm2_caves.py', 'tm2emu2.py', 'tm2cd.py', 'tm2dis.py', 'tm2_final.py', 'tm2_final_test.py', 'tm2_final_compress.py', 'tm2_final_build.py', 'tm2_final_chd.py', 'tm2_payload_final.deflate'): shutil.copyfile(os.path.join(T, fn), os.path.join(src, fn))
    out('intactos tras la construccion: EXE original=%s | BIN original=%s | versiones anteriores (Conos y Mod by Rek, EXE y BIN)=%s' % (md5f(SRC_EXE) == exe0, md5f(SRC_BIN) == bin0, [md5f(p) for p in KEEP] == keep0))
    out('salida: SCUS_943.06 md5=%s | %s.bin md5=%s' % (hashlib.md5(exe).hexdigest(), NAME, md5f(nbin)))
    out('RESULTADO: OK')
except BaseException as e:
    import traceback; out('ERROR: ' + traceback.format_exc())
out('FIN')
