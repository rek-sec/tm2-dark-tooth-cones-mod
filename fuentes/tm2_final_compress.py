# Recomprime el bloque del mod (80640000) con los parches de conos + la firma. Solo escribe en %TEMP%.
import sys, os, zlib, time, tempfile, hashlib
T = tempfile.gettempdir(); sys.path.insert(0, T); sys.path.insert(0, os.path.join(T, 'tm2_pydeps'))
import tm2_caves as C, tm2_final as RL
log = open(os.path.join(T, 'tm2_final_compress.log'), 'w', encoding='utf-8')
def out(s): log.write(time.strftime('%H:%M:%S ') + s + '\n'); log.flush()
try:
    d = open(C.EXE, 'rb').read(); TA = 0x800CDC54
    src = d[0x801A4DD4 - TA + 0x800:0x801BF3B4 - TA + 0x800]; pay = zlib.decompressobj(-15).decompress(src)
    new = bytearray(pay)
    for c in RL.comps():
        if c['addr'] >= 0x80640000:
            o = c['addr'] - 0x80640000; assert bytes(new[o:o + len(c['old'])]) == c['old'], c['name']; new[o:o + len(c['new'])] = c['new']
    new = bytes(new); open(os.path.join(T, 'tm2_payload_final.bin'), 'wb').write(new)
    out('bloque final: %d bytes md5=%s | hueco en el EXE: %d bytes | texto en 8067FA6C: %r' % (len(new), hashlib.md5(new).hexdigest(), len(src), new[0x3FA6C:0x3FA78]))
    import zopfli
    def comp(it, bsmax):
        try:
            z = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_DEFLATE, iterations=it, block_splitting=True, block_splitting_max=bsmax)
            return z.compress(new) + z.flush()
        except Exception as e:
            import zopfli.zlib as zz
            return zz.compress(new, numiterations=it, blocksplittingmax=bsmax)[2:-4]
    best = None
    for it, bs in ((60, 0), (250, 0), (1000, 0), (2500, 0)):
        t0 = time.time(); c = comp(it, bs); ok = zlib.decompressobj(-15).decompress(c) == new
        out('zopfli iteraciones=%d -> %d bytes en %.0f s | descomprime bien=%s | %s' % (it, len(c), time.time() - t0, ok, 'CABE (sobran %d)' % (len(src) - len(c)) if len(c) <= len(src) else 'no cabe (faltan %d)' % (len(c) - len(src))))
        if ok and (best is None or len(c) < len(best)): best = c; open(os.path.join(T, 'tm2_payload_final.deflate'), 'wb').write(c)
        if best is not None and len(best) <= len(src): break
    out('MEJOR=%d bytes | %s' % (len(best), 'CABE' if len(best) <= len(src) else 'NO CABE'))
except Exception as e:
    import traceback; out('ERROR: ' + traceback.format_exc())
out('FIN')
