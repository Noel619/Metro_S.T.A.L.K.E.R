# Desarrollo

Cómo poner en marcha el proyecto, generar los assets y comprobar que todo funciona.

## Abrir el juego en tu PC (Windows)

1. Descarga **Godot 4.7.2** (versión estándar, no la de .NET) desde [godotengine.org](https://godotengine.org/download/windows/). Tiene que ser esa versión exacta.
2. Descarga o clona este repositorio.
3. Abre Godot, pulsa **Importar** y elige el archivo `project.godot`.
4. Pulsa **F5**. Se abre **el depósito jugable** (Fase 2):

| Control | Qué hace |
|---|---|
| W A S D · ratón | Andar y mirar |
| F | Coger lo que tienes delante (el punto de lápiz se convierte en una mano) y soltarlo |
| Botón derecho, mantenido | Acerca el objeto a los ojos; el ratón lo gira |
| Esc | Suelta o recupera el ratón |
| F9 | Abre la partida a otro jugador (puerto 24680) |
| F10 | Te une a una partida abierta en la misma máquina |
| F1 | Oculta la ayuda |

Argumentos, después de `--`: `--chica` (juegas con la chica), `--host` (abres la partida) y `--join=DIRECCION` (te unes a otra). Por ejemplo, para probar el cooperativo en un solo PC: `godot --path . -- --host` en una ventana y `godot --path . -- --join=127.0.0.1 --chica` en otra.

El **visor del estilo** de la Fase 1 sigue en `scenes/style/visor_estilo.tscn` (ábrela y pulsa F6):

| Tecla | Qué hace |
|---|---|
| ← → | Cambia de diorama (depósito, patio de día, al anochecer y de noche, y las hojas de los personajes) |
| C | Cambia de cámara |
| ↑ ↓ | Sube o baja el miedo: el trazo tiembla más y el tramado invade la imagen |
| R | Activa o quita la radiación (más grano) |
| L | Enciende o apaga la linterna (imprescindible de noche) |

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

## Órdenes

`make` sin argumentos muestra la lista. Las principales:

| Orden | Qué hace |
|---|---|
| `make assets` | Regenera texturas, ilustraciones y modelos |
| `make models` | Solo los modelos (`tools/blender/recipes/`) |
| `make import` | Importa los recursos en Godot |
| `make test` | Tests unitarios, sin pantalla |
| `make test-net` | Pruebas de red: un anfitrión y un invitado en la misma máquina (la caja de la Fase 0 y el depósito) |
| `make lint` | Revisa el estilo del código GDScript |
| `make capture` | Capturas de las escenas de revisión en `docs/capturas/` |
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

### Personajes

- `tools/blender/personaje_bpy.py`: piezas blandas con color y pesos de hueso (`Sculpt`), volúmenes sobre los que colocar correas y bolsillos (`Profile`), el esqueleto y las poses con cinemática inversa.
- `tools/blender/personaje_anim.py`: las animaciones, como funciones del tiempo. Un nombre que acaba en `-loop` se importa en bucle.
- `tools/blender/recipes/personajes.py`: `jugador_chico`, `jugador_chica` y las manos de primera persona (`manos_*`).
- En Godot, `PlayerAvatar` (`scripts/actors/player_avatar.gd`) carga el modelo y lo anima: `speed`, `carrying`, `look_pitch`, `expression`, y la mochila, el zurrón y la mascarilla, que se pueden ocultar.
- Para revisarlos: `tools/capture.sh res://scenes/style/personajes_superficie.tscn salida.png`.

Si cambias un material de `assets/materials/` después de importar un modelo, borra su copia de `.godot/imported/` para que Godot lo importe otra vez.

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

Las escenas de revisión del estilo están en `scenes/style/` y se describen en [ESTILO.md](ESTILO.md).

## Cooperativo

El juego arranca siempre como anfitrión sin invitados (`NetSession`). `make test-net` lanza dos pruebas con un anfitrión y un invitado en la misma máquina:

- **caja**: el invitado ve moverse la caja de "Hola, Tumansk".
- **deposito**: el invitado entra en el depósito, recibe su jugador y los 22 objetos, anda, coge una lata, se la lleva y la suelta; el anfitrión comprueba que lo ve andar y llevarla.

Quién manda sobre qué está en [D-003](DECISIONES.md) y [D-024](DECISIONES.md).
