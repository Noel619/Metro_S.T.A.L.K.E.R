# Desarrollo

Cómo poner en marcha el proyecto, generar los assets y comprobar que todo funciona.

## Abrir el juego en tu PC (Windows)

1. Descarga **Godot 4.7.2** (versión estándar, no la de .NET) desde [godotengine.org](https://godotengine.org/download/windows/). Tiene que ser esa versión exacta.
2. Descarga o clona este repositorio.
3. Abre Godot, pulsa **Importar** y elige el archivo `project.godot`.
4. Pulsa **F5**. Se abre el **visor del estilo**, con los dioramas de la Fase 1 en movimiento:

| Tecla | Qué hace |
|---|---|
| ← → | Cambia de diorama (depósito limpio, depósito abandonado y patio de día, al anochecer, de noche y con ventisca) |
| C | Cambia de cámara |
| ↑ ↓ | Sube o baja el miedo: el trazo tiembla más y el tramado invade la imagen |
| R | Activa o quita la radiación (más grano) |
| L | Enciende o apaga la linterna (imprescindible de noche) |
| F1 | Panel de depuración: miedo, radiación, hora del día, clima, linterna, trazo reducido y estilo |

Los modelos, las texturas y las ilustraciones ya vienen generados en el repositorio: no hace falta instalar nada más para jugar o abrir las escenas.

## Herramientas para generar los assets

Solo hacen falta para cambiar recetas o generadores.

| Herramienta | Versión | Para qué |
|---|---|---|
| Godot | 4.7.2 | Motor |
| Python | 3.13 (la exige `bpy` 5.3) | Modelos y texturas |
| `bpy` | 5.3.0 (`pip install bpy==5.3.0`) | Blender como módulo de Python |
| `numpy`, `pillow` | Recientes | Texturas y plano de la ciudad |
| `shapely` | 2.2 | Plano de la ciudad (geometría) |
| `gdtoolkit` | 4.5.0 | Revisar y formatear GDScript |
| Node.js | 20 o superior | Ilustraciones 2D (rough.js) |
| ffmpeg | Cualquiera reciente | Vídeo de revisión |

## Órdenes

`make` sin argumentos muestra la lista. Las principales:

| Orden | Qué hace |
|---|---|
| `make assets` | Regenera texturas, ilustraciones y modelos |
| `make models` | Solo los modelos (`tools/blender/recipes/`) |
| `make import` | Importa los recursos en Godot |
| `make test` | Tests unitarios, sin pantalla |
| `make test-net` | Prueba de red: un anfitrión y un invitado en la misma máquina |
| `make lint` | Revisa el estilo del código GDScript |
| `make capture` | Capturas de las escenas de revisión en `capturas/` |
| `make video` | Vídeo de los dioramas en `capturas/dioramas.mp4` |
| `make setup` | Reescribe controles, capas y buses de audio en `project.godot` |
| `make ciudad` | Valida el plano de la ciudad, exporta `data/ciudad/` y dibuja las hojas de `docs/ciudad/` |
| `make ciudad-comprobar` | Solo valida y exporta el plano (lo que hace la CI) |

## Los pipelines de arte

Todo se genera por código. **Nunca se editan a mano** los archivos de `assets/models/`, `assets/textures/` ni `assets/ui/`: se edita la receta o el generador y se vuelve a generar.

### Modelos 3D

- Cada archivo de `tools/blender/recipes/` es una receta. Define `models()`, que devuelve un diccionario `nombre → función que construye el modelo`.
- Las utilidades comunes están en `tools/blender/tumansk_bpy.py`: cajas con bisel, imperfección controlada (`wobble`, `dent`, `apply_bulge`), pintura por vértice (color base, oclusión y cavidades) y exportación.
- `make models` (o `python3 tools/blender/build_assets.py nombre`) genera `assets/models/<nombre>.glb`.
- Godot lo importa solo y `tools/godot/post_import.gd` aplica las convenciones de nombre:

| Sufijo | Resultado en Godot |
|---|---|
| `-fisico` | La pieza pasa a ser un `RigidBody3D` |
| `-estatico` | La pieza pasa a ser un `StaticBody3D` |
| `-colcaja` | La malla se sustituye por una colisión de caja |
| `-colconvexa` | La malla se sustituye por una colisión convexa |

El nombre del material elige el material de Godot si existe `assets/materials/<nombre>.tres`; si no, se usa `base_vertex.tres`, que pinta con los colores por vértice.

### Ilustraciones 2D

`tools/svg/generate.mjs` dibuja con rough.js (aspecto a mano) y guarda SVG en `assets/ui/`. El texto no va dentro de los SVG: se pone en Godot con las tipografías del juego.

### Texturas

`tools/textures/generate_textures.py` genera el papel, los cuatro tonos de tramado, las rampas del sombreado por bandas y los ruidos. Todas se pueden repetir sin costuras.

### El plano de la ciudad

`tools/ciudad/` contiene el plano de Tumansk ([CIUDAD.md](CIUDAD.md)):

| Archivo | Qué hace |
|---|---|
| `datos.py` | Los datos: zonas, calles, edificios, patios, vehículos, hitos, subsuelo, amenazas, peligros y rutas |
| `geo.py` | Marcos de referencia (el eje monumental) y figuras |
| `relieve.py` | El terreno: río, loma, barranco, colina y cráter |
| `plano.py` | Valida, calcula daños, escombros y relieve, y exporta |
| `dibujo.py` | Dibuja las cuatro hojas de desarrollo |

Para dibujar una sola hoja: `python3 tools/ciudad/plano.py --plano=general` (también `subsuelo`, `peligros` o `rutas`).

## Capturas

`tools/capture.sh res://escena.tscn salida.png [ancho] [alto] [fotogramas]` renderiza con el render real (Forward+) sin pantalla: usa un servidor X virtual y, si no hay GPU, Vulkan por software. Las cámaras del grupo `capture_camera` generan una imagen cada una.

Opciones extra con la variable `CAPTURE_ARGS`:

- `--hide=InkPost`: captura sin el post-proceso del estilo.
- `--post=debug_view=N`: muestra una capa del post-proceso (ver `docs/ESTILO.md`).

Las escenas de revisión del estilo están en `scenes/style/` y se describen en [ESTILO.md](ESTILO.md). Las de interfaz (`scenes/ui/prueba_interfaz.tscn` y `prueba_tipografia.tscn`) son 2D: se capturan igual, sin cámara.

Con `CAPTURE_ARGS="--call=Nodo:metodo[:valor]"` se llama a un método antes de capturar; por ejemplo, el panel de depuración abierto a las 18:45:

```bash
CAPTURE_ARGS="--call=VisorEstilo:_load:3 --call=DioramaPatio:set_hour:18.75 --call=PanelDepuracion:toggle" tools/capture.sh res://scenes/style/visor_estilo.tscn panel.png
```

## Vídeo

`tools/video.sh salida.mp4 [ancho] [alto] [fps]` graba `scenes/debug/video_dioramas.tscn` con el modo película de Godot y lo convierte a MP4 con ffmpeg. El director (`scripts/debug/video_director.gd`) encadena los planos: cada uno carga un diorama, mueve su cámara entre dos puntos y anima la hora, el miedo o la linterna.

## Cooperativo

El juego arranca siempre como anfitrión sin invitados (`NetSession`). Para probar dos jugadores en la misma máquina, `make test-net` lanza un anfitrión y un invitado y comprueba que el invitado ve moverse la caja de "Hola, Tumansk".
