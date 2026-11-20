# Crea el .chd de la version "Mod by Rek" y comprueba que al extraerlo sale el mismo .bin.
import sys, os, time, tempfile, hashlib, subprocess
T = tempfile.gettempdir(); sys.path.insert(0, T)
import tm2_final as RL
CHDMAN = r'D:\Twisted Metal\TM2\chdman.exe'; OUT, NAME = RL.OUT, RL.NAME
log = open(os.path.join(T, 'tm2_final_chd.log'), 'w', encoding='utf-8')
def out(s): log.write(time.strftime('%H:%M:%S ') + s + '\n'); log.flush()
def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 24), b''): h.update(c)
    return h.hexdigest()
def run(args):
    r = subprocess.run([CHDMAN] + args, cwd=OUT, capture_output=True, text=True, errors='replace')
    tail = [l for l in (r.stdout + '\n' + r.stderr).replace('\r', '\n').splitlines() if l.strip()][-2:]
    out('chdman %s -> codigo %d | %s' % (args[0], r.returncode, ' / '.join(tail))); return r.returncode
try:
    cue = NAME + '.cue'; binp = os.path.join(OUT, NAME + '.bin'); chd = os.path.join(OUT, NAME + '.chd')
    if os.path.exists(chd): raise RuntimeError('ya existe ' + chd)
    if run(['createcd', '-i', cue, '-o', NAME + '.chd']) != 0 or not os.path.exists(chd): raise RuntimeError('createcd ha fallado')
    if run(['verify', '-i', NAME + '.chd']) != 0: raise RuntimeError('verify ha fallado')
    tc, tb = os.path.join(OUT, '_verif.cue'), os.path.join(OUT, '_verif.bin')
    try:
        if run(['extractcd', '-i', NAME + '.chd', '-o', '_verif.cue', '-ob', '_verif.bin']) != 0: raise RuntimeError('extractcd ha fallado')
        a, b = md5f(binp), md5f(tb)
        out('bin nuevo md5=%s | bin extraido del chd md5=%s | iguales=%s | tamanos %d / %d' % (a, b, a == b, os.path.getsize(binp), os.path.getsize(tb)))
        if a != b: raise RuntimeError('el chd no reproduce el bin')
    finally:
        for p in (tc, tb):
            if os.path.exists(p): os.remove(p)
    out('CHD: %s (%d bytes) md5=%s' % (chd, os.path.getsize(chd), md5f(chd)))
    out('RESULTADO CHD: OK')
except BaseException as e:
    import traceback; out('ERROR: ' + traceback.format_exc())
out('FIN')
