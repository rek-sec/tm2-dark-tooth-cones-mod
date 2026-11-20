"""
Lanzador portátil para compilar Twisted Metal 2 (Singletrac V3.6 Mod by Rek)
en cualquier computadora sin depender de rutas fijas en D:\.

Uso:
  1. Coloca tus archivos originales limpios en la carpeta ./input/ :
     - SCUS_943.06
     - Singletrac V3.6.bin
     - Singletrac V3.6.cue
  2. Ejecuta: python build_portable.py
  3. Recoge tus archivos listos en ./output/
"""

import os
import sys
import shutil
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FUENTES_DIR = os.path.join(BASE_DIR, "fuentes")
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REQUIRED_INPUTS = [
    "SCUS_943.06",
    "Singletrac V3.6.bin",
    "Singletrac V3.6.cue",
]

def main():
    print("=== Compilador Portátil: TM2 Dark Tooth Cones Mod by Rek ===\n")

    if not os.path.isdir(FUENTES_DIR):
        print(f"[ERROR] No se encontró la carpeta '{FUENTES_DIR}'.")
        sys.exit(1)

    os.makedirs(INPUT_DIR, exist_ok=True)
    missing = [f for f in REQUIRED_INPUTS if not os.path.isfile(os.path.join(INPUT_DIR, f))]
    if missing:
        print("[!] Faltan archivos base en la carpeta 'input/':")
        for m in missing:
            print(f"    - {m}")
        print("\nCopia tus archivos limpios de Singletrac V3.6 ahí y vuelve a ejecutar.")
        sys.exit(1)

    temp_dir = tempfile.gettempdir()
    print(f"[1/3] Preparando entorno temporal en {temp_dir}...")

    # Copiar fuentes al directorio temporal esperado por los scripts internos
    for fname in os.listdir(FUENTES_DIR):
        src = os.path.join(FUENTES_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(temp_dir, fname))

    # Adaptar rutas dinámicamente en tm2_caves.py, tm2_final.py y tm2_final_build.py
    caves_path = os.path.join(temp_dir, "tm2_caves.py")
    final_path = os.path.join(temp_dir, "tm2_final.py")
    build_path = os.path.join(temp_dir, "tm2_final_build.py")

    exe_in = os.path.join(INPUT_DIR, "SCUS_943.06").replace("\\", "\\\\")
    bin_in = os.path.join(INPUT_DIR, "Singletrac V3.6.bin").replace("\\", "\\\\")
    cue_in = os.path.join(INPUT_DIR, "Singletrac V3.6.cue").replace("\\", "\\\\")
    out_target = os.path.join(OUTPUT_DIR, "Singletrac V3.6 Mod by Rek Final").replace("\\", "\\\\")

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Parchear rutas en archivos temporales
    for path, replacements in [
        (caves_path, [(r"D:\\Twisted Metal\\TM2\\Extraccion\\Singletrac\\SCUS_943.06", exe_in)]),
        (final_path, [(r"D:\\Twisted Metal\\TM2\\Singletrac V3.6 Mod by Rek Final", out_target)]),
        (build_path, [
            (r"D:\\Twisted Metal\\TM2\\TM2 Singletrac V3.6\\Singletrac V3.6.bin", bin_in),
            (r"D:\\Twisted Metal\\TM2\\TM2 Singletrac V3.6\\Singletrac V3.6.cue", cue_in),
        ]),
    ]:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            for old, new in replacements:
                content = content.replace(old, new)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    print("[2/3] Construyendo ejecutable parcheado, verificando en emulador MIPS y generando BIN/CUE...")
    res = subprocess.run([sys.executable, build_path], cwd=temp_dir)
    if res.returncode != 0:
        print("[ERROR] Falló la construcción del binario. Revisa tm2_final_build.log en %TEMP%.")
        sys.exit(1)

    chd_script = os.path.join(temp_dir, "tm2_final_chd.py")
    if shutil.which("chdman") and os.path.isfile(chd_script):
        print("[3/3] chdman detectado. Comprimiendo imagen a formato .chd...")
        subprocess.run([sys.executable, chd_script], cwd=temp_dir)
    else:
        print("[3/3] chdman no detectado en el PATH; omitiendo conversión a .chd (BIN/CUE listos).")

    print(f"\n[OK] ¡Proceso finalizado! Tus archivos están en:\n     {OUTPUT_DIR}")

if __name__ == "__main__":
    main()