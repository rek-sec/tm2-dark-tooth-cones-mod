# Interprete MIPS I (R3000, little-endian) con delay slots, para ejecutar el arranque real del EXE fuera del emulador.
import struct
M = 0xFFFFFFFF
def sg(x): return x - 0x100000000 if x & 0x80000000 else x
def run(mem, pc, r, stops, limit=600_000_000):
    """mem: bytearray de 8 MB. r: lista de 32 registros. Devuelve (pc_final, pasos)."""
    up = struct.unpack_from; pk = struct.pack_into; cache = {}; hi = lo = 0; npc = pc + 4; steps = 0
    while pc not in stops:
        d = cache.get(pc)
        if d is None:
            w = up('<I', mem, pc & 0x7FFFFF)[0]; imm = w & 0xFFFF
            d = cache[pc] = (w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63, imm, imm - 0x10000 if imm & 0x8000 else imm, w & 0x3FFFFFF)
        op, rs, rt, rd, sh, fn, imm, si, tg = d
        steps += 1
        if steps > limit: raise RuntimeError('limite de pasos en %08X' % pc)
        nn = npc + 4
        if op == 0:
            a = r[rs]; b = r[rt]
            if fn == 33 or fn == 32: r[rd] = (a + b) & M
            elif fn == 35 or fn == 34: r[rd] = (a - b) & M
            elif fn == 0: r[rd] = (b << sh) & M
            elif fn == 2: r[rd] = b >> sh
            elif fn == 3: r[rd] = (sg(b) >> sh) & M
            elif fn == 4: r[rd] = (b << (a & 31)) & M
            elif fn == 6: r[rd] = b >> (a & 31)
            elif fn == 7: r[rd] = (sg(b) >> (a & 31)) & M
            elif fn == 37: r[rd] = a | b
            elif fn == 36: r[rd] = a & b
            elif fn == 38: r[rd] = a ^ b
            elif fn == 39: r[rd] = ~(a | b) & M
            elif fn == 43: r[rd] = 1 if a < b else 0
            elif fn == 42: r[rd] = 1 if sg(a) < sg(b) else 0
            elif fn == 8: nn = a
            elif fn == 9: r[rd] = (npc + 4) & M; nn = a
            elif fn == 16: r[rd] = hi
            elif fn == 18: r[rd] = lo
            elif fn == 17: hi = a
            elif fn == 19: lo = a
            elif fn == 25: p = a * b; lo = p & M; hi = (p >> 32) & M
            elif fn == 24: p = sg(a) * sg(b); lo = p & M; hi = (p >> 32) & M
            elif fn == 27:
                if b: lo = a // b; hi = a % b
                else: lo = M; hi = a
            elif fn == 26:
                x = sg(a); y = sg(b)
                if y: q = abs(x) // abs(y) * (1 if (x < 0) == (y < 0) else -1); lo = q & M; hi = (x - q * y) & M
                else: lo = (1 if x < 0 else M); hi = a
            else: raise RuntimeError('SPECIAL %d no soportado en %08X' % (fn, pc))
        elif op == 9 or op == 8: r[rt] = (r[rs] + si) & M
        elif op == 35: r[rt] = up('<I', mem, (r[rs] + si) & 0x7FFFFF)[0]
        elif op == 43: pk('<I', mem, (r[rs] + si) & 0x7FFFFF, r[rt])
        elif op == 36: r[rt] = mem[(r[rs] + si) & 0x7FFFFF]
        elif op == 40: mem[(r[rs] + si) & 0x7FFFFF] = r[rt] & 0xFF
        elif op == 4:
            if r[rs] == r[rt]: nn = npc + si * 4
        elif op == 5:
            if r[rs] != r[rt]: nn = npc + si * 4
        elif op == 37: r[rt] = up('<H', mem, (r[rs] + si) & 0x7FFFFF)[0]
        elif op == 33: r[rt] = up('<h', mem, (r[rs] + si) & 0x7FFFFF)[0] & M
        elif op == 41: pk('<H', mem, (r[rs] + si) & 0x7FFFFF, r[rt] & 0xFFFF)
        elif op == 32: r[rt] = up('<b', mem, (r[rs] + si) & 0x7FFFFF)[0] & M
        elif op == 13: r[rt] = r[rs] | imm
        elif op == 12: r[rt] = r[rs] & imm
        elif op == 14: r[rt] = r[rs] ^ imm
        elif op == 15: r[rt] = imm << 16
        elif op == 11: r[rt] = 1 if r[rs] < (si & M) else 0
        elif op == 10: r[rt] = 1 if sg(r[rs]) < si else 0
        elif op == 2: nn = (npc & 0xF0000000) | (tg << 2)
        elif op == 3: r[31] = (npc + 4) & M; nn = (npc & 0xF0000000) | (tg << 2)
        elif op == 6:
            if sg(r[rs]) <= 0: nn = npc + si * 4
        elif op == 7:
            if sg(r[rs]) > 0: nn = npc + si * 4
        elif op == 1:
            a = sg(r[rs])
            if rt & 0x10: r[31] = (npc + 4) & M
            if (a >= 0) if (rt & 1) else (a < 0): nn = npc + si * 4
        else: raise RuntimeError('opcode %d no soportado en %08X' % (op, pc))
        r[0] = 0; pc = npc & M; npc = nn & M
    return pc, steps

def boot_payload(exe_bytes):
    """Carga un PS-X EXE en 8 MB a cero y ejecuta su arranque hasta que termina de descomprimir el bloque del mod.
    Devuelve (resultado, pasos, memoria). resultado: 'ok' | 'fallo_descompresion' | 'sin_8MB'."""
    pc0, _gp, taddr, tsize = struct.unpack_from('<4I', exe_bytes, 0x10)
    mem = bytearray(0x800000); mem[taddr & 0x7FFFFF:(taddr & 0x7FFFFF) + tsize] = exe_bytes[0x800:0x800 + tsize]
    r = [0] * 32; r[29] = struct.unpack_from('<I', exe_bytes, 0x30)[0]
    stops = {0x8011DF70: 'ok', 0x801A3CEC: 'fallo_descompresion', 0x80183454: 'sin_8MB'}
    pc, steps = run(mem, pc0, r, set(stops))
    return stops[pc], steps, mem
