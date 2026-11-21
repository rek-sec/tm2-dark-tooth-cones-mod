# Twisted Metal 2 — Dark Tooth Boss AI Cones Mod (by Rek)

Modificación de ingeniería inversa para **Twisted Metal 2: World Tour (NTSC-U / `SCUS-943.06`)** sobre la base *Singletrac V3.6* de **[@inSAMity](https://www.youtube.com/@inSAMity)**.

Este mod reemplaza los disparos de la metralleta estándar (**R2**) por los conos de helado teledirigidos de **Dark Tooth** (proyectil tipo `0x3D`), dotándolos de la inteligencia artificial agresiva del jefe final, tiempo de vida extendido sin romper las físicas de vuelo, reciclaje inteligente de memoria y selector dinámico en el HUD.

---

## Demostración en YouTube

[![Ver demostración del mod en YouTube](https://img.youtube.com/vi/idx5JnMQbI4/hqdefault.jpg)](https://youtu.be/idx5JnMQbI4?si=klEMk667Yd6HLpYy)

*(Haz clic en la imagen para ver la demostración del mod en YouTube).*

## Características Principales

- **Doble Modo de Disparo (`L3` + `R2`):**
  - **`L3: CONE 1 by rek`**: Conos estándar con trayectoria sinusoidal (serpenteo) intacta y duración extendida a ~26 minutos.
  - **`L3: CONE 2 by rek`**: Conos con **IA de Jefe Final**:
    - Velocidad de giro máxima (`+0x08 = 99`) para reorientarse al instante si el enemigo esquiva.
    - **Órbita desactivada:** Los conos ya no se quedan dando vueltas alrededor de los objetivos sin impactar.
    - **Auto-Targeting garantizado:** Si disparas sin tener un objetivo fijado, el cono busca y fija automáticamente al enemigo vivo más cercano.
- **Sistema Anti-Saturación (Reciclaje de Slots):** El motor de PS1 solo admite **16 proyectiles simultáneos**. Se inyectó una rutina en ensamblador MIPS que recicla automáticamente el cono más antiguo cuando los 16 slots están llenos, evitando que la metralleta se atasque jamás.
- **Compatibilidad Total:** Verificado en emulador MIPS y DuckStation (modo *Recompiler* con 8 MB de RAM activados). Mantiene intactas las cabeceras y códigos **EDC/ECC** de los 484 sectores del ejecutable en el CD-ROM.

---

## Estructura del Repositorio

```text
├── README.md                 # Esta guía
├── DOCS_TECNICA.md           # Mapa de memoria MIPS, offsets y física del motor
├── build_portable.py         # Script lanzador con rutas relativas para cualquier PC
└── fuentes/                  # Herramientas originales de ensamblado, emulación y parches
    ├── tm2_final_build.py
    ├── tm2_final_chd.py
    ├── tm2_final.py
    ├── tm2_caves.py
    ├── tm2asm.py
    ├── tm2cd.py
    ├── tm2dis.py
    ├── tm2emu2.py
    └── tm2_payload_final.deflate
```

---

## Requisitos y Construcción

Para compilar tu propia imagen `.bin/.cue` y `.chd` sin depender de rutas absolutas:

1. **Requisitos previos:**
   - **Python 3.10+**
   - Copia base limpia de *Twisted Metal 2 (Singletrac V3.6)* en formato `.bin` y `.cue` junto con su ejecutable `SCUS_943.06` extraído.
   - *(Opcional)* `chdman.exe` (de MAME) en la carpeta o en el PATH del sistema para generar el archivo `.chd`.

2. **Verificación de archivos base (MD5):**
   - `SCUS_943.06` (Original): `be1573c5392a834733d9f2683e90ab61`
   - `Singletrac V3.6.bin` (Original): `83be2efebab74f34cdbaaca164906165`

3. **Ejecución:**
   Coloca tu `.bin`, `.cue` y `SCUS_943.06` originales dentro de una carpeta llamada `input/` en la raíz de este proyecto y ejecuta:
   ```bash
   python build_portable.py
   ```
   Los archivos finales parcheados se generarán automáticamente en la carpeta `output/`.

---

## Configuración Recomendada en Emulador (DuckStation)

- **Memoria RAM:** Activar **8 MB de RAM** (requerido por el bloque descomprimido del mod base en `0x80640000`).
- **CPU Execution Mode:** *Recompiler* (funciona nativamente sin necesidad de *Interpreter*).
- **Partidas:** Iniciar partida limpia o cargar desde *Memory Card* (los *Save States* antiguos sobrescribirán la RAM con el código sin parches).

---

## Uso, Modificación y Créditos

- **Base original:** Este mod está construido sobre la base *Singletrac V3.6* de **[@inSAMity](https://www.youtube.com/@inSAMity)** y la imagen base de *Twisted Metal 2: World Tour (NTSC-U / `SCUS-943.06`)*.
- **Libertad para modificar:** Eres libre de estudiar, ajustar, experimentar o modificar el código, scripts y configuraciones para crear tus propias variantes o pruebas.
- **Condición obligatoria:** Se debe respetar y conservar la autoría y mención a **Rek** (`rek`) en las partes o rutinas desarrolladas por mí, sin borrar ni atribuirse mi trabajo como propio.

## Contacto y Comunidad

- **Email:** reksecsys@gmail.com
- **Nick Discord:** `rek`
- **Servidores Discord donde encontrarme:**
  - [Twisted Metal Federation](https://discord.gg/28ryMjfr)
  - [Twisteros metaleros](https://discord.gg/N5PF9KHqx)
- **GitHub:** `https://github.com/rek-sec/tm2-dark-tooth-cones-mod`

---

*Desarrollado mediante análisis estático/dinámico en Ghidra y parcheo binario MIPS por **Rek**.*