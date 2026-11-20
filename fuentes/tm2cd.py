# Utilidades de imagen de CD (sectores crudos de 2352 bytes, Mode 2 Form 1): EDC/ECC e ISO9660 minimo.
import struct
F = [0] * 256; Bk = [0] * 256; E = [0] * 256
for i in range(256):
    j = ((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xFF; F[i] = j; Bk[i ^ j] = i
    x = i
    for _ in range(8): x = (x >> 1) ^ (0xD8018001 if x & 1 else 0)
    E[i] = x
def edc(b):
    x = 0
    for c in b: x = (x >> 8) ^ E[(x ^ c) & 0xFF]
    return x
def _ecc(src, major, minor, mult, inc):
    size = major * minor; out = bytearray(major * 2)
    for mj in range(major):
        idx = (mj >> 1) * mult + (mj & 1); a = b = 0
        for _ in range(minor):
            t = src[idx]; idx += inc
            if idx >= size: idx -= size
            a ^= t; b ^= t; a = F[a]
        a = Bk[F[a] ^ b]; out[mj] = a; out[mj + major] = a ^ b
    return bytes(out)
def _codes(s):
    e = struct.pack('<I', edc(s[16:2072]))
    z = bytearray(s[12:2072]) + e; z[0:4] = b'\0\0\0\0'
    p = _ecc(z, 86, 24, 2, 86); q = _ecc(bytes(z) + p, 52, 43, 86, 88)
    return e, p, q
def fix_m2f1(s):
    """Recalcula EDC y ECC (P y Q) de un sector Mode 2 Form 1, en el propio bytearray."""
    e, p, q = _codes(s); s[2072:2076] = e; s[2076:2248] = p; s[2248:2352] = q
def check_m2f1(s):
    if s[:12] != bytes([0] + [255] * 10 + [0]) or s[15] != 2 or (s[18] & 0x20): return False
    e, p, q = _codes(s); return bytes(s[2072:2076]) == e and bytes(s[2076:2248]) == p and bytes(s[2248:2352]) == q
def find_file(path, name):
    """Busca un fichero en la raiz ISO9660 de una imagen cruda. Devuelve (LBA, tamano)."""
    with open(path, 'rb') as f:
        def user(n): f.seek(n * 2352 + 24); return f.read(2048)
        pvd = user(16); assert pvd[0] == 1 and pvd[1:6] == b'CD001'
        rl, rs = struct.unpack_from('<I', pvd, 158)[0], struct.unpack_from('<I', pvd, 166)[0]
        data = b''.join(user(rl + i) for i in range((rs + 2047) // 2048)); p = 0
        while p < len(data):
            n = data[p]
            if n == 0: p = (p // 2048 + 1) * 2048; continue
            nl = data[p + 32]
            if data[p + 33:p + 33 + nl] == name.encode(): return struct.unpack_from('<I', data, p + 2)[0], struct.unpack_from('<I', data, p + 10)[0]
            p += n
    raise KeyError(name)
