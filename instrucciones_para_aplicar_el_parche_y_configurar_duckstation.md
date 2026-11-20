# Instrucciones para Aplicar el Parche — TM2 Dark Tooth Boss AI Cones Mod (by Rek)

Esta guía explica cómo aplicar el archivo de parche `.xdelta` sobre tu copia base de **Twisted Metal 2 (Singletrac V3.6)** y cómo configurar **DuckStation** para jugar sin problemas.

## 1. Requisitos Previos

* Tu copia limpia de **Twisted Metal 2 (Singletrac V3.6)** en formato `.bin` y `.cue`.

* El archivo de parche `.xdelta` descargado desde la sección **Releases** del repositorio.

* [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) (para aplicar el parche `.xdelta` sobre el `.bin`).

* **DuckStation** (emulador recomendado).

## 2. Cómo Aplicar el Parche (`.xdelta`)

1. **Haz una copia de seguridad:**
   Duplica tu archivo `.bin` original limpio y trabaja sobre la copia (o asegúrate de tener un respaldo intacto del archivo base) para no perder la imagen original.

2. **Abre Delta Patcher en modo "Apply patch":**

   * Asegúrate de que el botón principal diga **Apply patch**.

   * Si dice *Create patch*, haz clic en el botón azul con las dos flechas horizontales en la esquina inferior derecha para cambiar al modo de aplicar parche.

3. **Selecciona los archivos:**

   * **Original file:** Selecciona el archivo `.bin` de *Singletrac V3.6* que vas a parchar. *(Ten en cuenta que el parche se aplica directamente sobre el archivo seleccionado).*

   * **XDelta patch:** Selecciona el archivo `.xdelta` del mod.

4. **Aplica el parche:**
   Haz clic en **Apply patch** y espera a que aparezca el aviso de confirmación.

5. **Verifica el archivo `.cue`:**
   Asegúrate de que el archivo `.cue` siga apuntando exactamente al nombre de tu archivo `.bin` parcheado. Si renombraste el `.bin`, abre el `.cue` con el Bloc de notas y actualiza el nombre del archivo en la línea `FILE`.

*(Opcional)* Si prefieres jugar con un solo archivo `.chd`, puedes convertir tu `.bin` + `.cue` parcheados desde DuckStation en **Herramientas -> Convertir imagen de disco**.

## 3. Configuración Recomendada en DuckStation

* **Habilitar 8 MB de RAM (Obligatorio):**
  Ve a **Configuración -> Consola** (o **Avanzado** según tu versión) y activa **Habilitar 8 MB de RAM** (*Enable 8MB RAM*). Sin esto, el código extendido en memoria no cargará correctamente y el juego puede colgarse.

* **Modo de CPU:**
  Puedes usar **Recompiler** sin inconvenientes.

* **Control analógico (DualShock):**
  Asegúrate de tener configurado el mando como **Analog Controller (DualShock)** en **Configuración -> Controles** y tener asignado **L3** para alternar entre `L3: CONE 1 by rek` y `L3: CONE 2 by rek`.

* **Evita Save States antiguos:**
  Inicia una partida nueva o carga desde **Memory Card**. Cargar *Save States* previos puede sobrescribir la memoria RAM con código anterior al parche.