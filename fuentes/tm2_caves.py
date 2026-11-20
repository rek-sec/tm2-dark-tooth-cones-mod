# Rutinas para los conos de Dark Tooth. tm2_cone_mod.py las instala; tm2_cave_test.py las prueba.
#   R: reparto de slot con reciclaje, reescrito EN SU SITIO (800D91DC, 23 palabras = tamano del original).
#   T: giro + blanco garantizado para CONE 2. Se aloja sobre el codigo de orbita (modo 1) de 806477CC,
#      que es inalcanzable mientras el parche A este puesto; por eso T exige A.
import sys, struct, zlib, tempfile
sys.path.insert(0, tempfile.gettempdir())
from tm2asm import assemble
EXE = r'D:\Twisted Metal\TM2\Extraccion\Singletrac\SCUS_943.06'
R_ADDR, R_WORDS = 0x800D91DC, 23
T_ADDR, T_END = 0x80647A28, 0x80647CE4
HOOK = 0x80649028

SRC_R = '''
alloc:                          ; los 5 llamadores pasan a0 = 0
    lui   t0,0x801A
    ori   t0,t0,0x5B08          ; &proj[0]
    addu  v1,zero,zero          ; i
    addiu t4,zero,-1            ; mejor = -1
    ori   t1,zero,0x8000        ; menor TTL visto
a_loop:
    lhu   t2,2(t0)              ; tipo
    lh    a0,4(t0)              ; TTL
    xori  t2,t2,0x3D
    blez  a0,a_end              ; slot libre: devuelve i (igual que el original)
    addu  v0,v1,zero
    bne   t2,zero,a_next        ; solo se reciclan conos (tipo 0x3D)
    slt   t3,a0,t1
    beq   t3,zero,a_next
    nop
    addu  t1,a0,zero
    addu  t4,v1,zero
a_next:
    addiu v1,v1,1
    slti  t3,v1,16
    bne   t3,zero,a_loop
    addiu t0,t0,0x3D4
    addu  v0,t4,zero            ; lleno: cono con menos vida, o -1 si no hay conos
a_end:
    jr    ra
    nop
'''

SRC_T = '''
guard:                          ; si algun dia se llegara aqui en modo orbita: salir por la ruta normal
    j     0x80647CE4
    nop
giro_tgt:                       ; a0 = struct del jugador dueno, s2 = idx*0x3D4. Devuelve v0 = giro
    addiu sp,sp,-24
    sw    ra,20(sp)
    sw    a0,16(sp)
    jal   0x80648430            ; original: 99 si CONE 2, 20 si CONE 1
    nop
    lw    a0,16(sp)
    addiu at,zero,99
    bne   v0,at,g_done          ; solo CONE 2
    lui   t0,0x801A
    ori   t0,t0,0x5B08
    addu  t0,t0,s2              ; &proj[idx]
    lw    at,0x38(t0)
    lw    t1,0x34(t0)           ; objeto del cono
    bne   at,zero,g_done        ; ya tiene blanco: no se toca
    nop
    lw    a1,0xA8(t1)
    lw    a2,0xAC(t1)
    lw    a3,0xB0(t1)
    lui   t8,0x7FFF             ; mejor distancia
    addu  t9,zero,zero          ; mejor objeto
    lui   t7,0x8016
    addu  t2,zero,zero
    lui   t3,0x8018
    ori   t4,t3,0x7B10          ; structs de jugador
    ori   t5,t3,0x0FEC          ; tabla de objetos de jugador
g_ploop:
    lbu   at,0x4760(t7)         ; n jugadores
    sltiu t6,t2,2
    beq   t6,zero,g_ai
    sltu  t6,t2,at
    beq   t6,zero,g_ai
    nop
    beq   t4,a0,g_pnext         ; el propio dueno
    addiu t6,zero,2
    bne   at,t6,g_pok           ; mismo filtro que 806477CC: con 2 jugadores,
    nop
    lw    at,0x475C(t7)         ; el otro humano solo es blanco si [8016475C] == 3
    addiu t6,zero,3
    bne   at,t6,g_pnext
    nop
g_pok:
    lw    at,0x1F0(t4)          ; salud
    lbu   t6,0x9C(t4)
    blez  at,g_pnext
    nop
    bne   t6,zero,g_pnext
    nop
    lw    v1,0(t5)
    jal   g_cand
    nop
g_pnext:
    addiu t2,t2,1
    addiu t4,t4,0x814
    j     g_ploop
    addiu t5,t5,4
g_ai:
    addu  t2,zero,zero
    lui   t3,0x8018
    ori   t4,t3,0x8B5C          ; structs de IA
    ori   t5,t3,0x8B38          ; tabla de objetos de IA
g_aloop:
    lbu   at,0x4761(t7)         ; n IA
    sltiu t6,t2,9
    beq   t6,zero,g_fin
    sltu  t6,t2,at
    beq   t6,zero,g_fin
    lui   t3,0x8063
    lw    at,0x0450(t3)         ; mismo filtro que 806477CC: se salta la IA [8061B398]
    addiu t6,zero,1             ; cuando [80630450] == 1
    bne   at,t6,g_aok
    lui   t3,0x8062
    lw    at,-0x4C68(t3)
    nop
    beq   at,t2,g_anext
    nop
g_aok:
    lw    at,0x5A0(t4)          ; salud
    lbu   t6,0x6C(t4)
    blez  at,g_anext
    nop
    bne   t6,zero,g_anext
    nop
    lw    v1,0(t5)
    jal   g_cand
    nop
g_anext:
    addiu t2,t2,1
    addiu t4,t4,0x854
    j     g_aloop
    addiu t5,t5,4
g_fin:
    beq   t9,zero,g_done        ; ningun enemigo valido: se queda sin blanco
    nop
    addiu t9,t9,0xA8
    sw    t9,0x38(t0)           ; proj.blanco = &objeto.posicion
g_done:
    lw    ra,20(sp)
    nop
    jr    ra
    addiu sp,sp,24
g_cand:                         ; v1 = objeto candidato; actualiza t8/t9 si esta mas cerca
    lui   at,0x8080
    slt   at,v1,at              ; valido solo si 0x80000000 <= v1 < 0x80800000
    beq   at,zero,g_cret
    nop
    lw    at,0xA8(v1)
    lw    t6,0xAC(v1)
    subu  at,at,a1
    bgez  at,g_c1
    subu  t6,t6,a2
    subu  at,zero,at
g_c1:
    bgez  t6,g_c2
    nop
    subu  t6,zero,t6
g_c2:
    addu  at,at,t6
    lw    t6,0xB0(v1)
    nop
    subu  t6,t6,a3
    bgez  t6,g_c3
    nop
    subu  t6,zero,t6
g_c3:
    addu  at,at,t6
    slt   t6,at,t8
    beq   t6,zero,g_cret
    nop
    addu  t8,at,zero
    addu  t9,v1,zero
g_cret:
    jr    ra
    nop
'''

def build():
    d = open(EXE, 'rb').read()
    f = lambda a, n: d[a - 0x800CDC54 + 0x800:a - 0x800CDC54 + 0x800 + n]              # EXE en disco
    pay = zlib.decompressobj(-15).decompress(f(0x801A4DD4, 0x801BF3B4 - 0x801A4DD4))   # bloque del mod -> 80640000
    p = lambda a, n: pay[a - 0x80640000:a - 0x80640000 + n]
    cr, lr = assemble(SRC_R, R_ADDR); ct, lt = assemble(SRC_T, T_ADDR)
    assert len(cr) == R_WORDS and ct[-1][0] + 4 <= T_END
    pk = lambda c: b''.join(struct.pack('<I', w) for _, w, _ in c)
    jal = struct.pack('<I', 0x0C000000 | ((lt['giro_tgt'] & 0x0FFFFFFF) >> 2))
    comps = [
        dict(name='A', addr=0x80647168, old=p(0x80647168, 4), new=bytes(4), desc='CONE 2 no entra en modo orbita'),
        dict(name='B', addr=0x80648FD8, old=p(0x80648FD8, 4), new=bytes.fromhex('3C7C0224'), desc='TTL inicial de los conos = 31804'),
        dict(name='R', addr=R_ADDR, old=f(R_ADDR, R_WORDS * 4), new=pk(cr), desc='sin slot libre: reciclar el cono con menos vida'),
        dict(name='Tc', addr=T_ADDR, old=p(T_ADDR, len(ct) * 4), new=pk(ct), desc='rutina de blanco (sobre el codigo de orbita, muerto con A)'),
        dict(name='Th', addr=HOOK, old=p(HOOK, 4), new=jal, desc='enganche: CONE 2 sin blanco -> enemigo vivo mas cercano'),
    ]
    assert comps[0]['old'].hex() == '0a002210' and comps[1]['old'].hex() == '3c000224' and comps[4]['old'].hex() == '0c21190c'
    return dict(comps=comps, code_r=cr, code_t=ct, labels=lt)
