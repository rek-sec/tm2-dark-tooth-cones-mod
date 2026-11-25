# Twisted Metal 2 — Dark Tooth Boss AI Cones Mod R6 (by Rek)

Modificación de ingeniería inversa para **Twisted Metal 2: World Tour (NTSC-U / `SCUS-943.06`)** sobre la base *Singletrac V3.6* de **[@inSAMity](https://www.youtube.com/@inSAMity)**.

Con **Dark Tooth**, `R2` dispara los conos de helado del personaje (proyectil tipo `0x3D`). **R6** se instala sobre la edición **R2 - Tema Dark Tooth**.

---

## Demostración de la versión anterior en YouTube

[![Ver demostración del mod en YouTube](https://img.youtube.com/vi/idx5JnMQbI4/hqdefault.jpg)](https://youtu.be/idx5JnMQbI4?si=klEMk667Yd6HLpYy)

*(Haz clic en la imagen para ver la demostración del mod en YouTube).*

## Características de R6

- **Ráfaga en abanico**. Una pulsación de `R2` llena los slots libres. La ráfaga completa lanza **12 Conos 2 guiados** y **4 Conos 1 estándar** en ángulos distintos.
- **Disparo sostenido y Rapid Fire**. Cada disparo individual lanza un Cono 2. Al mantener `R2` con el arreglo lleno, cada disparo libera el cono propio con menos tiempo de vida. Rapid Fire acelera esa cadencia.
- **Slots compartidos**. Las demás armas y los proyectiles de otros vehículos ocupan espacio en el mismo arreglo. Si los 16 slots están ocupados y Dark Tooth carece de conos propios, el siguiente disparo requiere un slot libre.
- **Conos**. La trayectoria sinusoidal conserva su fase inicial y la duración máxima es de unos 26 minutos. El modo con IA de jefe desactiva la órbita y selecciona al enemigo vivo más cercano cuando el cono sale sin blanco.
- **HUD**. El indicador `R2: CONES` muestra el botón de disparo.

---

## Fuentes

```text
├── DOCS_TECNICA.md        # Mapa de memoria y parches MIPS
├── build_portable.py     # Construcción de la edición anterior a R2
└── fuentes/
    ├── tm2_r6.py         # Parche R2 → R6 y generación del BIN/CUE
    ├── tm2asm.py         # Ensamblador MIPS
    └── tm2cd.py          # Utilidades de ISO 9660 y EDC/ECC
```

---

## Construcción de R6

Necesitas **Python 3.10+**, **Zopfli** y el par `.bin/.cue` de **Singletrac V3.6 Mod by Rek R2 - Tema Dark Tooth** en el mismo directorio. El script comprueba la identidad del ejecutable de R2 y localiza el BIN a partir del CUE.

Desde la raíz del repositorio, indica la ruta a tu CUE de R2.

```powershell
python -m pip install zopfli
python fuentes/tm2_r6.py "Mod_nuevo/Singletrac V3.6 Mod by Rek R2 - Tema Dark Tooth.cue"
```

El BIN y el CUE de R6 se generan en `output/Singletrac V3.6 Mod by Rek R6 - Tema Dark Tooth/`. `--salida` permite elegir otro directorio padre. Carga el CUE de R6 en DuckStation.

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
