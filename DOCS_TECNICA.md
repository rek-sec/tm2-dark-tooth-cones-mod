# Documentación Técnica: Arquitectura y Mapa de Memoria (TM2)

Este documento describe `SCUS_943.06` (NTSC-U), el bloque extendido de *Singletrac V3.6* y el parche de **R6** sobre la imagen **R2 - Tema Dark Tooth**.

---

## 1. Arquitectura del Ejecutable y Compresión

El ejecutable principal (`991,232` bytes) carga en RAM base `0x800CDC54` (offset de archivo `0x800`). Sin embargo, el código extendido del mod reside en un bloque comprimido con **Deflate/Zlib** ubicado dentro del binario:

* **Rango en RAM del flujo comprimido**. R2 usa `0x801A4DD4` a `0x801BF3B4` como intervalo con extremo superior excluido. Desde R5, el extremo pasa a `0x801BF454` mediante la instrucción en `0x801A3CC0`.
* **Destino en RAM al descomprimir:** `0x80640000` (`262,136` bytes descomprimidos).
* **Capacidad del bloque**. `tm2_r6.py` verifica los 160 bytes de relleno al final del ejecutable de R2 y los incorpora al espacio de `108,160` bytes reservado para Deflate.

---

## 2. Estructura del Proyectil Tipo `0x3D` (Cono de Dark Tooth)

El motor gestiona un arreglo compartido de **16 slots de proyectiles** en RAM a partir de `0x801A5B08`. Cada estructura mide `0x3D4` bytes. El asignador considera libre un slot con `TTL <= 0`. El tipo y el dueño identifican el proyectil, y las armas comparten la capacidad del arreglo.

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

### B. Asignación de slots, ráfaga y Rapid Fire en R6
R4 llenaba el arreglo con una sola ráfaga. Los conos repetían los dos puntos de salida y el mismo ángulo inicial, lo que podía ocultar unos detrás de otros. Al llenarse el arreglo, el chequeo previo bloqueaba todos los disparos hasta que se liberara un slot.

- **Asignador `0x800D91DC` (offset `0xBD88` del EXE)**. El mod usa las 23 instrucciones originales de *Singletrac V3.6*. La rutina devuelve el primer índice con `TTL <= 0` o `-1` si todos los slots están ocupados.
- **Chequeo de ráfaga `0x806482C4`**. Tras pasar el control de cadencia, la ruta de Dark Tooth recorre los 16 slots y hace un intento de lanzamiento por slot libre durante la misma llamada.
- **Arreglo lleno**. La rutina en `0x80648450` busca el cono `0x3D` del jugador con menor TTL. Usa el ID que lee el disparo desde el objeto del vehículo y llama a `fxRecordFree` en `0x800D914C` para liberar un slot y su visibilidad antes de lanzar un cono nuevo.
- **Bucle de lanzamiento `0x806706A8`**. `fp` guarda el número de intentos pendientes desde el bit 8 y el signo del ángulo en el bit 0. El bucle resta `0x100` y alterna el signo tras cada intento.
- **Selección y ángulo de salida `0x80647C98`**. Si el número de intentos pendientes es múltiplo de cuatro, la rutina escribe `0` en el selector `0x8063EA88` para disparar Cono 1. En los demás casos escribe `1` para disparar Cono 2. El disparo individual es siempre guiado y sale centrado. En las ráfagas, la desviación alterna de signo y reduce su magnitud en 16 unidades por cono. La rutina restaura el ángulo original del vehículo al volver del disparo.
- **Rapid Fire `0x80652BD8`**. El juego lee el bit 9 en `0x8063F608 + 4 * jugador`. La cadencia de la ráfaga es de 12 ticks en modo normal o 3 con Rapid Fire en un jugador. El juego usa 4 ticks con Rapid Fire en dos jugadores.

### C. Auto-Targeting para CONE 2 (`0x80649028` $\rightarrow$ `0x80647A28`)
* **Lógica**. Al disparar con el selector (`0x8063EA88`) en modo `CONE 2`, si el puntero de blanco (`+0x38`) es nulo, la subrutina inyectada en `0x80647A28` escanea la lista de vehículos activos, filtra al propio dueño y coches destruidos, y asigna el objetivo vivo más cercano por distancia Manhattan.

### D. Cueva de Textos en el HUD (`0x80648674` $\rightarrow$ `0x80647C0C`)
* **Edición anterior a R2**. El enganche en `0x80648674` carga las cadenas extendidas desde la cueva en `0x80647C0C` para un jugador y usa cadenas cortas en pantalla dividida.
* **Desde R2**. El indicador de disparo usa `R2: CONES by rek` en `0x80647C0C` y `R2: CONES` en `0x8067FA6C` para la variante corta.

---

## 4. Integridad de Sectores CD-ROM (Mode 2 / Form 1)

El ejecutable `SCUS_943.06` ocupa **484 sectores** en el BIN (`LBA 201385` a `201868`). El parche verifica los campos **EDC** y **ECC** con `tm2cd.py` y los recalcula en cada sector modificado. El resto del disco se copia desde R2, incluidas las pistas de audio. En el CUE de salida solo cambia el nombre del BIN.

## 5. Verificación de R6

- **Arranque**. El intérprete MIPS ejecutó la rutina de arranque y confirmó que el bloque cargado en RAM coincide con el bloque parcheado. El Deflate ocupa `108,144` bytes y deja `16` bytes de relleno.
- **Ráfaga y seguimiento**. En un escenario controlado del intérprete MIPS se probaron de 0 a 16 slots libres. La ráfaga completa creó 12 Conos 2 y 4 Conos 1. Los Conos 2 sin blanco previo adquirieron al enemigo vivo más cercano y conservaron el factor de giro `99`.
- **Disparo sostenido**. Con el arreglo lleno se verificaron 64 disparos consecutivos en modo normal y otros 64 con Rapid Fire. Cada disparo lanzó un Cono 2 en un slot propio. También se comprobó el bloqueo cuando el arreglo lleno carecía de conos propios.
- **Imagen de disco**. Los 484 sectores del ejecutable pasaron la verificación EDC/ECC. Se comprobaron el contenido del resto del BIN y los índices de pista del CUE contra la imagen R2.
