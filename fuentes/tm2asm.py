# Mini ensamblador MIPS I + emulador (subconjunto) para verificar rutinas antes de escribirlas en RAM.
import re, struct
RN = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
      's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
REG = {n: i for i, n in enumerate(RN)}
M = 0xFFFFFFFF
def sg(x): return x - 0x100000000 if x & 0x80000000 else x

def assemble(src, base):
    labels = {}; ins = []; pc = base
    for raw in src.splitlines():
        l = raw.split(';')[0].strip()
        if not l: continue
        if l.endswith(':'): labels[l[:-1]] = pc; continue
        ins.append((pc, l)); pc += 4
    def val(s):
        s = s.strip(); return labels[s] if s in labels else int(s, 0)
    out = []
    for pc, l in ins:
        p = l.split(None, 1); op = p[0]; A = [a.strip() for a in p[1].split(',')] if len(p) > 1 else []
        R = lambda i: REG[A[i]]
        def mem(i):
            mm = re.fullmatch(r'(-?\w+)\((\w+)\)', A[i]); off = int(mm.group(1), 0)
            assert -32768 <= off <= 32767, l
            return off & 0xFFFF, REG[mm.group(2)]
        def br(i):
            d = val(A[i]) - (pc + 4); assert d % 4 == 0 and -131072 <= d < 131072, l
            return (d >> 2) & 0xFFFF
        if op == 'nop': w = 0
        elif op in ('addu','subu','slt','sltu','and','or','xor'):
            fn = {'addu':0x21,'subu':0x23,'slt':0x2A,'sltu':0x2B,'and':0x24,'or':0x25,'xor':0x26}[op]
            w = (R(1) << 21) | (R(2) << 16) | (R(0) << 11) | fn
        elif op in ('sll','srl','sra'):
            w = (R(1) << 16) | (R(0) << 11) | ((int(A[2], 0) & 31) << 6) | {'sll':0,'srl':2,'sra':3}[op]
        elif op in ('addiu','slti','sltiu','andi','ori','xori'):
            imm = int(A[2], 0)
            if op in ('andi','ori','xori'): assert 0 <= imm <= 0xFFFF, l
            else: assert -32768 <= imm <= 32767, l
            w = ({'addiu':9,'slti':10,'sltiu':11,'andi':12,'ori':13,'xori':14}[op] << 26) | (R(1) << 21) | (R(0) << 16) | (imm & 0xFFFF)
        elif op == 'lui':
            imm = int(A[1], 0); assert 0 <= imm <= 0xFFFF, l
            w = (15 << 26) | (R(0) << 16) | imm
        elif op in ('lb','lh','lw','lbu','lhu','sb','sh','sw'):
            off, b = mem(1)
            w = ({'lb':32,'lh':33,'lw':35,'lbu':36,'lhu':37,'sb':40,'sh':41,'sw':43}[op] << 26) | (b << 21) | (R(0) << 16) | off
        elif op in ('beq','bne'): w = ((4 if op == 'beq' else 5) << 26) | (R(0) << 21) | (R(1) << 16) | br(2)
        elif op in ('blez','bgtz'): w = ((6 if op == 'blez' else 7) << 26) | (R(0) << 21) | br(1)
        elif op in ('bltz','bgez'): w = (1 << 26) | (R(0) << 21) | ((0 if op == 'bltz' else 1) << 16) | br(1)
        elif op in ('j','jal'):
            t = val(A[0]); assert t % 4 == 0 and (t & 0xF0000000) == ((pc + 4) & 0xF0000000), l
            w = ((2 if op == 'j' else 3) << 26) | ((t & 0x0FFFFFFF) >> 2)
        elif op == 'jr': w = (R(0) << 21) | 8
        else: raise ValueError('instruccion no soportada: ' + l)
        out.append((pc, w, l))
    return out, labels

class Emu:
    """Interprete MIPS I minimo con delay slots. Trabaja sobre un bytearray de 8 MB (copia de la RAM)."""
    def __init__(self, mem):
        self.m = mem; self.r = [0] * 32; self.hi = 0; self.lo = 0; self.steps = 0
    def u32(self, a): return struct.unpack_from('<I', self.m, a & 0x7FFFFF)[0]
    def run(self, pc, stop=None, hazard=None, limit=200000):
        r = self.r
        if stop is None: stop = 0x1FC00000; r[31] = stop
        npc = pc + 4; last = None
        def setr(i, v):
            if i: r[i] = v & M
        while pc != stop:
            w = self.u32(pc); self.steps += 1
            if self.steps > limit: raise RuntimeError('limite de pasos superado en %08X' % pc)
            op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; sh = (w >> 6) & 31; fn = w & 63
            imm = w & 0xFFFF; si = imm - 0x10000 if imm & 0x8000 else imm
            if op == 0: reads = (rt,) if fn in (0, 2, 3) else (rs,) if fn == 8 else () if fn in (16, 18) else (rs, rt)
            elif op in (4, 5, 40, 41, 43): reads = (rs, rt)
            elif op in (2, 3, 15): reads = ()
            else: reads = (rs,)
            if hazard and hazard(pc) and last and last in reads:
                raise RuntimeError('uso de un registro recien cargado (load delay) en %08X' % pc)
            a = r[rs]; b = r[rt]; nn = npc + 4; ld = None
            if op == 0:
                if fn == 0: setr(rd, b << sh)
                elif fn == 2: setr(rd, b >> sh)
                elif fn == 3: setr(rd, sg(b) >> sh)
                elif fn == 8: nn = a
                elif fn == 9: setr(rd, npc + 4); nn = a
                elif fn == 16: setr(rd, self.hi)
                elif fn == 18: setr(rd, self.lo)
                elif fn == 24: p = sg(a) * sg(b); self.lo = p & M; self.hi = (p >> 32) & M
                elif fn == 25: p = a * b; self.lo = p & M; self.hi = (p >> 32) & M
                elif fn == 27: self.lo = (a // b if b else M) & M; self.hi = (a % b if b else a) & M
                elif fn in (32, 33): setr(rd, a + b)
                elif fn in (34, 35): setr(rd, a - b)
                elif fn == 36: setr(rd, a & b)
                elif fn == 37: setr(rd, a | b)
                elif fn == 38: setr(rd, a ^ b)
                elif fn == 42: setr(rd, 1 if sg(a) < sg(b) else 0)
                elif fn == 43: setr(rd, 1 if a < b else 0)
                else: raise RuntimeError('SPECIAL %d no soportado en %08X' % (fn, pc))
            elif op == 1:
                if rt & 0x10: r[31] = (npc + 4) & M
                if (sg(a) >= 0) if (rt & 1) else (sg(a) < 0): nn = npc + si * 4
            elif op == 2: nn = (npc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
            elif op == 3: r[31] = (npc + 4) & M; nn = (npc & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
            elif op == 4: nn = npc + si * 4 if a == b else nn
            elif op == 5: nn = npc + si * 4 if a != b else nn
            elif op == 6: nn = npc + si * 4 if sg(a) <= 0 else nn
            elif op == 7: nn = npc + si * 4 if sg(a) > 0 else nn
            elif op in (8, 9): setr(rt, a + si)
            elif op == 10: setr(rt, 1 if sg(a) < si else 0)
            elif op == 11: setr(rt, 1 if a < (si & M) else 0)
            elif op == 12: setr(rt, a & imm)
            elif op == 13: setr(rt, a | imm)
            elif op == 14: setr(rt, a ^ imm)
            elif op == 15: setr(rt, imm << 16)
            elif op in (32, 33, 35, 36, 37):
                o = (a + si) & 0x7FFFFF
                setr(rt, struct.unpack_from({32: '<b', 33: '<h', 35: '<I', 36: '<B', 37: '<H'}[op], self.m, o)[0]); ld = rt
            elif op in (40, 41, 43):
                o = (a + si) & 0x7FFFFF
                struct.pack_into({40: '<B', 41: '<H', 43: '<I'}[op], self.m, o, b & {40: 0xFF, 41: 0xFFFF, 43: M}[op])
            else: raise RuntimeError('opcode %d no soportado en %08X' % (op, pc))
            last = ld; pc = npc & M; npc = nn & M
        return r[2]
