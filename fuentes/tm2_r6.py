"""Construye R6 sobre la imagen R2 con el tema de Dark Tooth."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zlib

import tm2cd
from tm2asm import assemble


NAME = "Singletrac V3.6 Mod by Rek R6 - Tema Dark Tooth"
R2_EXE_SHA256 = "8bb46380ab561d0c1ed688575133e6681c1c89dfd70c8f617611b9b22a89e759"
EXE_BASE = 0x800CDC54
PAYLOAD_BASE = 0x80640000
DEFLATE_START = 0x801A4DD4 - EXE_BASE + 0x800
DEFLATE_END = 0x801BF3B4 - EXE_BASE + 0x800
LOADER_END = 0x801A3CC0
ALLOC = 0x800D91DC
FIRE_CHECK = 0x806482C4
FIRE_READY = 0x80648300
FIRE_BLOCKED = 0x80648310
FIRE_WRAPPER = 0x80648320
RECYCLE = 0x80648450
SPREAD = 0x80647C98

# Asignador original de Singletrac V3.6, incluidas las ranuras de retardo.
SRC_ALLOC = """
    addu  v1,a0,zero
    slti  v0,v1,16
    beq   v0,zero,full
    sll   v0,v1,4
    subu  v0,v0,a0
    sll   v0,v0,2
    addu  v0,v0,a0
    sll   v0,v0,2
    addu  v0,v0,a0
    sll   a0,v0,2
slot_loop:
    lui   at,0x801A
    addu  at,at,a0
    lh    v0,0x5B0C(at)
    nop
    blez  v0,done
    addu  v0,v1,zero
    addiu v1,v1,1
    slti  v0,v1,16
    bne   v0,zero,slot_loop
    addiu a0,a0,0x3D4
full:
    addiu v0,zero,-1
done:
    jr    ra
    nop
"""

SRC_FIRE_CHECK = f"""
    lui   t0,0x801A
    ori   t0,t0,0x5B08
    addiu t1,zero,16
    addu  t2,zero,zero
slot_loop:
    lh    t3,4(t0)
    addiu t1,t1,-1
    bgtz  t3,slot_next         ; TTL positivo: slot ocupado
    addiu t0,t0,0x3D4
    addiu t2,t2,0x100         ; un slot libre
slot_next:
    bgtz  t1,slot_loop
    nop
    bne   t2,zero,ready
    nop
    j     {RECYCLE:#x}
    nop
ready:
    ori   t2,t2,1             ; signo inicial del ángulo de salida
    addu  s2,s5,s1
    j     0x80670680
    lbu   s5,7(s2)
blocked:
    j     0x80670508
    nop
    nop
    nop
"""

# Solo se ejecuta tras comprobar que los 16 TTL son positivos.
# Obtiene el ID de la misma tabla de objetos que usa el disparo.
SRC_RECYCLE = f"""
    lui   t0,0x8018
    sll   t1,s7,2
    addu  t0,t0,t1
    lw    t0,0x0FEC(t0)
    nop
    beq   t0,zero,{FIRE_BLOCKED:#x}
    lui   t1,0x801A
    lw    t8,0x118(t0)
    ori   t0,t1,0x5B08
    addu  t1,zero,zero
    ori   t2,zero,0x8000       ; TTL menor visto
    addiu t3,zero,-1           ; índice del cono elegido
loop:
    lhu   t4,2(t0)
    lhu   t5,0x42(t0)
    xori  t4,t4,0x3D
    bne   t4,zero,next
    lh    t6,4(t0)
    bne   t5,t8,next
    slt   t7,t6,t2
    beq   t7,zero,next
    nop
    addu  t2,t6,zero
    addu  t3,t1,zero
next:
    addiu t1,t1,1
    slti  t7,t1,16
    bne   t7,zero,loop
    addiu t0,t0,0x3D4
    bltz  t3,{FIRE_BLOCKED:#x}
    addu  a0,t3,zero
    jal   0x800D914C           ; fxRecordFree limpia TTL y visibilidad
    addu  a1,zero,zero
    j     {FIRE_READY:#x}
    addiu t2,zero,0x100       ; una sola reposición con el arreglo lleno
"""

SRC_FIRE_WRAPPER = f"""
    addiu sp,sp,-32
    sw    ra,28(sp)
    sw    a0,24(sp)
    j     {SPREAD:#x}
    lw    t0,0x708(a0)         ; giro horizontal original del vehículo
restore:
    lw    a0,24(sp)
    lw    t0,20(sp)
    lw    ra,28(sp)
    sw    t0,0x708(a0)
    jr    ra
    addiu sp,sp,32
"""

SRC_SPREAD = f"""
    srl   t1,fp,8
    sw    t0,20(sp)
    addiu t1,t1,-1
    andi  t2,t1,3             ; uno de cada cuatro usa CONE 1
    sll   t1,t1,4             ; 16 unidades de ángulo por disparo pendiente
    andi  t3,fp,1
    bne   t3,zero,apply_yaw
    sltiu t2,t2,3             ; 1 = CONE 2, también cuando queda un solo disparo
    subu  t1,zero,t1
apply_yaw:
    addu  t0,t0,t1
    sw    t0,0x708(a0)
    lui   t0,0x8064
    jal   0x80673D50
    sb    t2,-0x1578(t0)      ; 0x8063EA88
    lui   t0,0x8064
    j     {FIRE_WRAPPER + 20:#x}
    sb    zero,-0x1578(t0)
"""

# fp guarda los disparos restantes desde el bit 8 y el signo del ángulo en el bit 0.
SRC_FIRE_LOOP = """
    addiu fp,fp,-0x100
    sltiu at,fp,0x100
    beq   at,zero,0x806706A8
    xori  fp,fp,1
"""


def write_code(data, base, address, source, words):
    code, _ = assemble(source, address)
    assert len(code) == words
    offset = address - base
    data[offset:offset + words * 4] = b"".join(
        struct.pack("<I", word) for _, word, _ in code
    )


def patch_executable(executable):
    if hashlib.sha256(executable).hexdigest() != R2_EXE_SHA256:
        raise ValueError("SCUS_943.06 debe corresponder a R2 - Tema Dark Tooth.")

    try:
        from zopfli.zlib import compress
    except ModuleNotFoundError as error:
        raise ValueError("Instala Zopfli con python -m pip install zopfli.") from error

    payload = bytearray(zlib.decompress(executable[DEFLATE_START:DEFLATE_END], -15))
    _, fire_labels = assemble(SRC_FIRE_CHECK, FIRE_CHECK)
    assert fire_labels["ready"] == FIRE_READY and fire_labels["blocked"] == FIRE_BLOCKED
    write_code(payload, PAYLOAD_BASE, FIRE_CHECK, SRC_FIRE_CHECK, 23)
    write_code(payload, PAYLOAD_BASE, FIRE_WRAPPER, SRC_FIRE_WRAPPER, 11)
    write_code(payload, PAYLOAD_BASE, RECYCLE, SRC_RECYCLE, 33)
    write_code(payload, PAYLOAD_BASE, SPREAD, SRC_SPREAD, 17)
    write_code(payload, PAYLOAD_BASE, 0x806706A0, "addu fp,t2,zero", 1)
    write_code(payload, PAYLOAD_BASE, 0x806706C4, SRC_FIRE_LOOP, 4)
    payload = bytes(payload)

    # El EXE R2 termina con 160 bytes de relleno cargados en RAM.
    stream_end = len(executable)
    assert executable[DEFLATE_END:stream_end] == bytes(160)
    capacity = stream_end - DEFLATE_START
    for iterations in (60, 250, 1000):
        stream = compress(payload, numiterations=iterations, blocksplittingmax=0)[2:-4]
        if len(stream) <= capacity:
            break
    else:
        raise ValueError(f"El bloque R6 comprimido supera los {capacity} bytes disponibles.")
    assert zlib.decompress(stream, -15) == payload

    patched = bytearray(executable)
    write_code(patched, EXE_BASE - 0x800, ALLOC, SRC_ALLOC, 23)
    end_address = EXE_BASE + stream_end - 0x800
    write_code(patched, EXE_BASE - 0x800, LOADER_END, f"addiu a1,a1,{end_address - 0x801C0000}", 1)
    patched[DEFLATE_START:stream_end] = stream.ljust(capacity, b"\0")
    return patched


def build(source_cue, output_root):
    cue = source_cue.read_bytes()
    entry = re.search(rb'(?im)^[ \t]*FILE[ \t]+"([^"\r\n]+)"[ \t]+BINARY[ \t]*\r?$', cue)
    if entry is None or len(re.findall(rb"(?im)^[ \t]*FILE[ \t]+", cue)) != 1:
        raise ValueError("El CUE debe identificar un solo BIN que contenga todas las pistas.")
    source_bin = source_cue.parent / os.fsdecode(entry[1])
    output = output_root / NAME
    if output.exists():
        raise FileExistsError(f"Ya existe la salida {output}")

    lba, size = tm2cd.find_file(source_bin, "SCUS_943.06;1")
    if size != 484 * 2048:
        raise ValueError("El ejecutable R2 debe ocupar 484 sectores de datos.")
    with source_bin.open("rb") as image:
        image.seek(lba * 2352)
        sectors = [image.read(2352) for _ in range(size // 2048)]
    if not all(tm2cd.check_m2f1(sector) for sector in sectors):
        raise ValueError("Error de integridad EDC/ECC en los sectores del ejecutable R2.")
    patched = patch_executable(b"".join(sector[24:2072] for sector in sectors))

    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_root) as work_dir:
        work = Path(work_dir) / NAME
        work.mkdir()
        target_bin = work / (NAME + ".bin")
        shutil.copyfile(source_bin, target_bin)
        with target_bin.open("r+b") as image:
            for index, sector in enumerate(sectors):
                data = patched[index * 2048:(index + 1) * 2048]
                if data != sector[24:2072]:
                    updated = bytearray(sector)
                    updated[24:2072] = data
                    tm2cd.fix_m2f1(updated)
                    image.seek((lba + index) * 2352)
                    image.write(updated)

        start, end = entry.span(1)
        target_cue = work / (NAME + ".cue")
        target_cue.write_bytes(cue[:start] + target_bin.name.encode("ascii") + cue[end:])
        work.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cue", type=Path, help="archivo CUE de R2 - Tema Dark Tooth")
    parser.add_argument("--salida", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        output = build(args.cue, args.salida)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Error al construir R6. {error}\n")
    print(f"BIN y CUE de R6 generados en {output}")


if __name__ == "__main__":
    main()
