# Documentación Técnica: Arquitectura y Mapa de Memoria (TM2)

Este documento detalla los hallazgos de ingeniería inversa realizados sobre `SCUS_943.06` (NTSC-U) y el bloque extendido *Singletrac V3.6* para que otros modders puedan reutilizar las estructuras y evitar errores críticos del motor.

---

## 1. Arquitectura del Ejecutable y Compresión

El ejecutable principal (`991,232` bytes) carga en RAM base `0x800CDC54` (offset de archivo `0x800`). Sin embargo, el código extendido del mod reside en un bloque comprimido con **Deflate/Zlib** ubicado dentro del binario:

* **Rango en RAM del flujo comprimido:** `0x801A4DD4` — `0x801BF3B4` (`108,000` bytes exactos).
* **Destino en RAM al descomprimir:** `0x80640000` (`262,136` bytes descomprimidos).
* **Restricción crítica de tamaño:** Para evitar reconstruir la tabla de archivos ISO (LBA) del CD-ROM, el bloque recomprimido **no puede exceder los `108,000` bytes**. La compresión estándar de `zlib` supera este límite; es obligatorio utilizar **`zopfli`** (`iterations >= 60`) para lograr un tamaño de `~107,958` bytes con relleno de ceros al final.

---

## 2. Estructura del Proyectil Tipo `0x3D` (Cono de Dark Tooth)

El motor gestiona un arreglo fijo de **16 slots de proyectiles** en RAM a partir de `0x801A5B08`. Cada estructura mide `0x3D4` bytes:

| Offset | Tipo | Descripción | Comportamiento / Notas |
| :--- | :--- | :--- | :--- |
| `+0x02` | `uint16` | Tipo de proyectil | `0x003D` corresponde al cono de helado de Dark Tooth. |
| `+0x04` | `int16` | **TTL (Time-To-Live)** | **¡Cuidado!** No es solo un temporizador. Controla la fase del movimiento sinusoidal (`sin(TTL * 300)`). |
| `+0x06` | `int16` | Velocidad lineal | Velocidad de avance del proyectil. |
| `+0x08` | `int16` | **Factor de Giro** | `20` para el jugador por defecto; **`99`** para la IA de Dark Tooth (giro cerrado instantáneo). |
| `+0x34` | `uint32` | Puntero al objeto | Instancia 3D en el mundo. |
| `+0x38` | `uint32` | Puntero al blanco | Dirección en RAM del vehículo objetivo (`0x00000000` = vuelo recto). |
| `+0x42` | `int16` | ID del Dueño | `1` = Jugador 1; `50` = Jefe / IA. |

### Regla de Oro del TTL (`+0x04`)
* El valor original de `60` ticks equivale a ~3 segundos (el juego corre a ~20 ticks/s).
* **No congelar el TTL:** Si se impide que el TTL decremente, `sin(TTL * 300)` queda constante y el cono pierde su trayectoria errática, volviéndose fácil de esquivar.
* **Valor óptimo (`31,804` / `0x7C3C`):** Extiende la vida del cono a ~26 minutos manteniendo exactamente la misma fase inicial de serpenteo y evitando desbordamientos de signo (`int16` máximo = `32,767`).

---

## 3. Resumen de Parches Aplicados

### A. Anulación de Órbita (`0x80647168`)
* **Problema:** Cuando un cono con giro `99` se acercaba demasiado a un objetivo en movimiento, entraba en un estado de órbita perpetua alrededor del coche sin detonar (controlado por tabla de estado en `0x8063E978 + slot*16 + 12`).
* **Solución:** Se parcheó con `nop` (`0x00000000`) el salto condicional en `0x80647168` dentro del bloque descomprimido. Esto libera además el código muerto de la rutina de órbita (`0x806477CC` — `0x80647CE4`) para alojar nuevas subrutinas.

### B. Reciclaje de Slots en Metralleta (`0x800D91DC` / Offset `0xBD88`)
* **Problema:** La función asignadora de slots (`0x800D91DC`, 23 instrucciones MIPS) devuelve `-1` cuando los 16 slots tienen `TTL > 0`. Con disparos rápidos de `R2` y conos de larga duración, los 16 slots se saturan y el arma deja de disparar en silencio.
* **Solución:** Se reescribió `0x800D91DC` en sus mismas 23 instrucciones: si no hay huecos libres, recorre los 16 slots buscando el proyectil de tipo `0x3D` con el **menor TTL restante** (el más antiguo) y lo sobrescribe limpiamente sin afectar misiles ni otras armas activas.

### C. Auto-Targeting para CONE 2 (`0x80649028` $\rightarrow$ `0x80647A28`)
* **Lógica:** Al disparar con el selector (`0x8063EA88`) en modo `CONE 2`, si el puntero de blanco (`+0x38`) es nulo, la subrutina inyectada en `0x80647A28` escanea la lista de vehículos activos, filtra al propio dueño y coches destruidos, y asigna el objetivo vivo más cercano por distancia Manhattan/Euclidiana.

### D. Cueva de Textos en el HUD (`0x80648674` $\rightarrow$ `0x80647C0C`)
* **Problema:** Las cadenas originales `L3: CONE 1` (`0x8067FA6C`) y `L3: CONE 2` (`0x8067FA90`) están empaquetadas con un límite estricto de 10 caracteres + terminador nulo.
* **Solución:** Se almacenaron las cadenas extendidas (`L3: CONE 1 by rek\0` y `L3: CONE 2 by rek\0`) en la zona de código muerto de órbita (`0x80647C0C`) y se enganchó el renderizado del HUD en `0x80648674` para cargar estos punteros en modo 1 jugador, conservando las cadenas cortas originales en pantalla dividida de 2 jugadores para no invadir el HUD vecino.

---

## 4. Integridad de Sectores CD-ROM (Mode 2 / Form 1)

El ejecutable `SCUS_943.06` ocupa exactamente **484 sectores** en la imagen `.bin` (`LBA 201385` a `201868`). Al modificar bytes dentro de estos sectores, DuckStation y consolas reales rechazarán la lectura si no se recalculan los campos **EDC** (Error Detection Code) y **ECC** (Error Correction Code) de cada sector de `2352` bytes (bytes `2072` a `2351`). El módulo `tm2cd.py` automatiza este cálculo sector por sector.