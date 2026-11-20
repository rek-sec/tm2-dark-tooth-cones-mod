# Comprobaciones previas de la version final (HUD). SOLO LECTURA sobre DuckStation; el HUD se emula sobre una copia de la RAM.
import sys, os, struct, tempfile
T = tempfile.gettempdir(); sys.path.insert(0, T)
import tm2_caves as C, tm2_final as FN, tm2emu2
from tm2dis import dis, sx
M = 0xFFFFFFFF; o = lambda a: a & 0x7FFFFF
d = open(C.EXE, 'rb').read()
try:
    from tm2live import Live
    L = Live(); base = bytearray(L.rd(0x80000000, 0x800000)); print('estado de partida: RAM viva de DuckStation (PID %d), jugadores=%d' % (L.pm.process_id, base[0x164760]))
except BaseException as e:
    base = bytearray(open(os.path.join(T, 'tm2_ram_real.bin'), 'rb').read()); print('estado de partida: volcado guardado (%r)' % (e,))
u32 = lambda m, a: struct.unpack_from('<I', m, o(a))[0]
ok = [True]
def chk(c, msg): print(('  OK    ' if c else '  FALLO ') + msg); ok[0] = ok[0] and bool(c)
comps = FN.comps(True); byn = {c['name']: c for c in comps}; newn = [c['name'] for c in comps[5:]]
OB = FN.OLD_BUF; OE = OB + 4 * FN.OLD_STRIDE
print('=== 1) quien usa los buffers del HUD (%08X..%08X) y quien salta a los tramos que se reescriben' % (OB, OE))
refs = []; badj = []; reg = {}
ints = [(FN.SITE + 4, FN.SITE + 28, 'sitio del HUD'), (FN.STR_ADDR, C.T_END, 'cola muerta')]
for lo, hi in ((0x80010000, 0x80200000), (0x80600000, 0x80800000)):
    for a in range(lo, hi, 4):
        x = u32(base, a); op = x >> 26; rs = (x >> 21) & 31; rt = (x >> 16) & 31; imm = x & 0xFFFF; t = None
        if op in (4, 5, 6, 7) or (op == 1 and rt in (0, 1, 16, 17)): t = a + 4 + sx(imm) * 4
        elif op in (2, 3): t = (a & 0xF0000000) | ((x & 0x3FFFFFF) << 2)
        if t is not None:
            for l, h, nm in ints:
                inside = (C.T_ADDR - 4 <= a < C.T_END) if nm == 'cola muerta' else (l - 8 <= a < h)
                if l <= t < h and not inside: badj.append('%s: %08X %s' % (nm, a, dis(a, x)))
        if op == 15: reg[rt] = (imm << 16, a); continue
        if rs in reg and 0 < a - reg[rs][1] <= 64 and op in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43):
            v = (reg[rs][0] | imm) if op == 13 else (reg[rs][0] + sx(imm)) & M
            if OB - 0x40 <= v < OE + 0x40: refs.append((a, v, dis(a, x)))
for a, v, t in refs: print('  info  %08X %-22s -> %08X' % (a, t, v))
chk({a for a, v, t in refs if OB <= v < OE} == {0x806486AC, 0x806486E8}, 'las unicas instrucciones que apuntan a esos buffers son las dos del propio HUD (806486AC y 806486E8)')
chk(not badj, 'ningun salto externo entra en los tramos que se reescriben %s' % badj[:4])
print('  info  bytes distintos de cero en cada buffer de la sesion actual (J1 par, J1 impar, J2 par, J2 impar): %s' % [sum(1 for b in base[o(OB + i * 0xFC):o(OB + (i + 1) * 0xFC)] if b) for i in range(4)])
gps = set()
for i in range(0x800, len(d) - 8, 4):
    w0, w1 = struct.unpack_from('<II', d, i)
    if w0 >> 16 == 0x3C1C and (w1 >> 16) in (0x279C, 0x379C): gps.add((((w0 & 0xFFFF) << 16) + (sx(w1 & 0xFFFF) if w1 >> 16 == 0x279C else (w1 & 0xFFFF))) & M)
chk(len(gps) == 1, 'registro gp unico: %s' % ['%08X' % g for g in gps]); GP = min(gps)
def put(m, names, k):
    for n in names: c = byn[n]; m[o(c['addr']):o(c['addr']) + len(c[k])] = c[k]
st = bytearray(base); put(st, [c['name'] for c in comps[:5]], 'new'); put(st, newn, 'old')
st[o(0x8067FA6C):o(0x8067FA6C) + 12] = b'L3: CONE 1\x00\x00'; st[o(OB):o(OE)] = b'\xA5' * (OE - OB)
S_ORIG = st; S_NEW = bytearray(st); put(S_NEW, newn, 'new')
RET, SP = 0x1FC00000, 0x801FF000
def run_hud(state, n, p, par, lay, sel, arma):
    m = bytearray(state); m[0x164760] = n
    for q in (0, 1):
        P = 0x187B10 + q * 0x814; m[0x164764 + q] = 0x0E; m[P + 0x9C] = 0; m[0x63EA88 + q] = sel
        struct.pack_into('<i', m, P + 0x1F0, 320); struct.pack_into('<I', m, P + 0x90, arma)
    struct.pack_into('<I', m, o(0x801828D0 + p * 8 + par * 16), 0x00FFFFFF)
    before = bytes(m); r = [0] * 32; r[4], r[5], r[6], r[28], r[29], r[31] = p, par, lay, GP, SP, RET
    pc, _ = tm2emu2.run(m, 0x806484D8, r, {0x806429A0, RET}, limit=3000000)
    if pc != 0x806429A0: raise RuntimeError('el HUD no llega a su primera llamada')
    tm2emu2.run(m, 0x80648508, r, {RET}, limit=3000000); ch = []
    for off in range(0, 0x800000, 0x1000):
        if m[off:off + 0x1000] != before[off:off + 0x1000]:
            i = off
            while i < off + 0x1000:
                if m[i] != before[i]:
                    j = i
                    while j < off + 0x1000 and m[j] != before[j]: j += 1
                    ch.append((0x80000000 + i, 0x80000000 + j)); i = j
                else: i += 1
    return m, ch
cm = {}
def cmap(c):
    if c not in cm:
        m = bytearray(S_ORIG); r = [0] * 32; r[4], r[28], r[29], r[31] = c, GP, SP, RET
        tm2emu2.run(m, 0x80113500, r, {RET}, limit=200000); cm[c] = r[2] & 0xFF
    return cm[c]
tbl = u32(base, 0x801872E0 + 8); spc = struct.unpack_from('<i', base, o(0x801872C4 + 8))[0]; wsp = base[o(tbl + 0x11C)]
def model(text, Y):
    x = 2; out = []
    for i, c in enumerate(text):
        if c == 0x20: x += wsp + spc; continue
        mm = cmap(c); idx = mm - 0x30 if 0x30 <= mm < 0x7D else 0x2F
        u, v, w, h, yo = struct.unpack_from('<BBBBh', base, o(tbl + idx * 6)); out.append((i, chr(c), x, Y + yo - h, u, v, w, h)); x += w + spc
    return out, x
def check(m, ch, S, size, p, par, lay, text):
    n = (size - 12) // 20; Y = 186 if lay == 1 else 88 if lay == 2 else 210; exp, xe = model(text, Y); pb = []; uo = None; sl = []
    for i in range(n):
        raw = bytes(m[o(S + 12 + i * 20):o(S + 12 + i * 20) + 20]); sl.append(None if raw == b'\xA5' * 20 else raw)
    for i, c, x, y, u, v, w, h in exp:
        raw = sl[i] if i < n else None
        if raw is None: pb.append('falta el glifo %d %r' % (i, c)); continue
        gx, gy = struct.unpack_from('<hh', raw, 8); gw, gh = struct.unpack_from('<HH', raw, 16)
        if uo is None: uo = (raw[12] - u, raw[13] - v)
        if (raw[3], raw[7], gx, gy, gw, gh, raw[12] - uo[0], raw[13] - uo[1]) != (4, 0x64, x, y, w, h, u, v): pb.append('glifo %d %r distinto' % (i, c))
    used = {e[0] for e in exp}
    pb += ['hueco %d escrito sin caracter' % i for i, s in enumerate(sl) if s is not None and i not in used]
    if m[o(S) + 3] != 2: pb.append('falta el DR_MODE')
    ot = 0x801828D0 + p * 8 + par * 16; a = u32(m, ot) & 0xFFFFFF; seq = []
    while S <= (0x80000000 | a) < S + size and len(seq) < 40: seq.append(0x80000000 | a); a = u32(m, 0x80000000 | a) & 0xFFFFFF
    if seq != [S] + [S + 12 + e[0] * 20 for e in reversed(exp)] or a != 0xFFFFFF: pb.append('lista de primitivas distinta')
    allow = [(S, S + size), (ot, ot + 4), (GP + 0x190, GP + 0x198), (0x80187264, 0x80187268), (SP - 0x2000, SP)]
    return pb, [(a_, b_) for a_, b_ in ch if not any(l <= a_ and b_ <= h for l, h in allow)], sl, xe
TX = {(0xF0, 0): b'L3: CONE 1', (0xF0, 1): b'L3: CONE 2', (0x90, 0): b'L3: Normal', (0x90, 1): b'L3: Orbit'}
LONG = {(0xF0, 0): FN.TEXTS[0], (0xF0, 1): FN.TEXTS[1]}
code = sorted((o(c['addr']), o(c['addr']) + len(c['new'])) for c in comps[5:])
def same_data(a, b):
    pos = 0
    for l, h in code:
        if a[pos:l] != b[pos:l]: return False
        pos = h
    return a[pos:] == b[pos:]
print('=== 2) HUD emulado con el codigo real del juego: original frente a version final')
n2 = bad2 = n1 = bad1 = 0; shown = set(); maxend = 0
for arma in (0xF0, 0x90):
    for sel in (0, 1):
        for par in (0, 1):
            for lay in (0, 1, 2):
                t0 = TX[(arma, sel)]; t1 = LONG.get((arma, sel), t0)
                for p in (0, 1):
                    m0, c0 = run_hud(S_ORIG, 2, p, par, lay, sel, arma); m1, c1 = run_hud(S_NEW, 2, p, par, lay, sel, arma)
                    pb, oo, sl, xe = check(m0, c0, OB + (2 * p + par) * 0xFC, 0xFC, p, par, lay, t0); n2 += 1
                    if pb or oo or not same_data(m0, m1):
                        bad2 += 1
                        if bad2 <= 4: print('  FALLO 2 jugadores: arma=%X sel=%d jug=%d par=%d disp=%d | %s %s | memoria igual=%s' % (arma, sel, p, par, lay, pb[:2], ['%08X..%08X' % x for x in oo[:3]], same_data(m0, m1)))
                m0, c0 = run_hud(S_ORIG, 1, 0, par, lay, sel, arma); pb0, o0, sl0, x0 = check(m0, c0, OB + par * 0xFC, 0xFC, 0, par, lay, t0)
                m1, c1 = run_hud(S_NEW, 1, 0, par, lay, sel, arma); S1 = OB + par * 0x1F8; pb1, o1, sl1, x1 = check(m1, c1, S1, 0x1F8, 0, par, lay, t1)
                maxend = max(maxend, max((b for a, b in c1 if S1 <= a < S1 + 0x1F8), default=S1) - S1)
                pref = all(a == b or (a is not None and b is not None and a[4:] == b[4:]) for a, b in zip(sl0[:len(t0)], sl1[:len(t0)]))
                mq, cq = run_hud(S_NEW, 1, 1, par, lay, sel, arma); idle = all(SP - 0x2000 <= a and b <= SP for a, b in cq); n1 += 1
                if pb0 or o0 or pb1 or o1 or not pref or not idle:
                    bad1 += 1
                    if bad1 <= 6: print('  FALLO 1 jugador: arma=%X sel=%d par=%d disp=%d | orig: %s %s | final: %s %s | prefijo igual=%s | J2 no dibuja=%s' % (arma, sel, par, lay, pb0[:2], ['%08X..%08X' % x for x in o0[:3]], pb1[:2], ['%08X..%08X' % x for x in o1[:3]], pref, idle))
                elif (arma, sel) not in shown:
                    shown.add((arma, sel)); print('  info  1 jugador: %-12r -> %-19r glifos %2d -> %2d | ancho en pantalla %3d -> %3d px (x de 2 a %d)' % (t0.decode(), t1.decode(), sum(s is not None for s in sl0), sum(s is not None for s in sl1), x0 - 2, x1 - 2, x1))
chk(bad2 == 0, '2 jugadores, %d casos: el original dibuja bien y la version final deja la memoria EXACTAMENTE igual que el original' % n2)
chk(bad1 == 0, '1 jugador, %d casos: cada glifo en su sitio, lista de primitivas correcta, escrituras solo en su buffer, primeros glifos identicos al original, y el jugador 2 no dibuja nada' % n1)
chk(maxend <= 12 + 17 * 20 <= 0x1F8, '1 jugador: maximo usado de cada buffer doble = %d de %d bytes' % (maxend, 0x1F8))
print('RESULTADO PREVIO:', 'OK' if ok[0] else 'FALLA'); sys.exit(0 if ok[0] else 1)
