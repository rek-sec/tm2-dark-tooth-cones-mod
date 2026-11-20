# Version final: parches de los conos + texto largo "L3: CONE n by rek" en el HUD (partidas de 1 jugador).
import sys, struct, zlib, tempfile
sys.path.insert(0, tempfile.gettempdir())
import tm2_caves as C
from tm2asm import assemble
OUT = r'D:\Twisted Metal\TM2\Singletrac V3.6 Mod by Rek Final'; NAME = 'Singletrac V3.6 Mod by Rek Final'
PREV = r'D:\Twisted Metal\TM2\TM2 Singletrac V3.6 Conos'      # version anterior (solo se lee, para comparar)
TEXTS = (b'L3: CONE 1 by rek', b'L3: CONE 2 by rek')
STR_ADDR, STR_SLOT = 0x80647C0C, 20            # cola del codigo de orbita (inalcanzable con el parche A), tras la rutina T
HLP = STR_ADDR + 2 * STR_SLOT
SITE = 0x80648674
OLD_BUF, OLD_STRIDE = 0x80631428, 0xFC         # 4 buffers del HUD: 2 jugadores x 2 fotogramas, 12 huecos de sprite cada uno
SRC_HLP = '''
hud_buf:                        ; entra: s2 jugador, v1 paridad de fotograma, at = jugador*8, s3 texto. Sale: v0, s3
    sll   v0,s2,9
    subu  v0,v0,at              ; jugador * 0x1F8
    sll   a0,v1,2
    sll   a1,v1,8
    subu  a0,a1,a0              ; paridad * 0xFC
    lui   a1,0x8016
    lbu   a1,0x4760(a1)         ; numero de jugadores
    addu  v0,v0,a0              ; desplazamiento original del buffer
    addiu a1,a1,-1
    bne   a1,zero,hb_ret        ; 2 jugadores: todo como en el original
    lui   a2,0x8068
    sll   v0,a0,1               ; 1 jugador: paridad * 0x1F8 (ocupa tambien los buffers del jugador 2, sin uso)
    addiu a2,a2,-1428           ; 8067FA6C = "L3: CONE 1"
    subu  a2,s3,a2
    beq   a2,zero,hb_c1
    addiu a3,zero,36            ; 8067FA90 = "L3: CONE 2"
    bne   a2,a3,hb_ret
    nop
    lui   s3,0x8064
    jr    ra
    addiu s3,s3,0x7C20
hb_c1:
    lui   s3,0x8064
    addiu s3,s3,0x7C0C
hb_ret:
    jr    ra
    nop
'''
SRC_SITE = '''
    jal   0x%08X
    andi  v1,s1,1
    nop
    nop
    nop
    nop
    nop
''' % HLP
def comps(zero_fill=True):
    assert all(len(t) < STR_SLOT for t in TEXTS) and (STR_ADDR & 0xFFFF, (STR_ADDR + STR_SLOT) & 0xFFFF) == (0x7C0C, 0x7C20)
    d = open(C.EXE, 'rb').read()
    pay = zlib.decompressobj(-15).decompress(d[0x801A4DD4 - 0x800CDC54 + 0x800:0x801BF3B4 - 0x800CDC54 + 0x800])
    p = lambda a, n: pay[a - 0x80640000:a - 0x80640000 + n]
    pk = lambda code: b''.join(struct.pack('<I', w) for _, w, _ in code)
    hlp, _ = assemble(SRC_HLP, HLP); site, _ = assemble(SRC_SITE, SITE); hend = HLP + 4 * len(hlp)
    assert hend <= C.T_END and len(site) == 7
    out = C.build()['comps'] + [
        dict(name='St', addr=STR_ADDR, old=p(STR_ADDR, 2 * STR_SLOT), new=b''.join(t + bytes(STR_SLOT - len(t)) for t in TEXTS), desc='textos largos, en codigo muerto'),
        dict(name='Hh', addr=HLP, old=p(HLP, hend - HLP), new=pk(hlp), desc='rutina: buffer doble y texto largo con 1 jugador'),
        dict(name='Hj', addr=SITE, old=struct.pack('<7I', 0x00121240, 0x00411023, 0x32230001, 0x00032080, 0x00032A00, 0x00A42023, 0x00441021), new=pk(site), desc='HUD: llamada a la rutina'),
    ]
    if zero_fill and hend < C.T_END: out.append(dict(name='Zf', addr=hend, old=p(hend, C.T_END - hend), new=bytes(C.T_END - hend), desc='resto del codigo muerto a cero (comprime mejor)'))
    for c in out[5:]: assert p(c['addr'], len(c['old'])) == c['old'] and len(c['old']) == len(c['new']), c['name']
    return out
