# Desarrollo

Cómo poner en marcha el proyecto, generar los assets y comprobar que todo funciona.

## Abrir el juego en tu PC (Windows)

1. Descarga **Godot 4.7.2** (versión estándar, no la de .NET) desde [godotengine.org](https://godotengine.org/download/windows/). Tiene que ser esa versión exacta.
2. Descarga o clona este repositorio.
3. Abre Godot, pulsa **Importar** y elige el archivo `project.godot`.
4. Pulsa **F5**. Se abre el **visor del estilo**, con los dioramas de la Fase 1 en movimiento:

| Tecla | Qué hace |
|---|---|
| ← → | Cambia de diorama (depósito limpio, depósito abandonado, patio de día, patio al anochecer) |
| C | Cambia de cámara |
| ↑ ↓ | Sube o baja el miedo: el trazo tiembla más y el tramado invade la imagen |
| R | Activa o quita la radiación (más grano) |

Los modelos, las texturas y las ilustraciones ya vienen generados en el repositorio: no hace falta instalar nada más para jugar o abrir las escenas.

## Herramientas para generar los assets

Solo hacen falta para cambiar recetas o generadores.

| Herramienta | Versión | Para qué |
|---|---|---|
| Godot | 4.7.2 | Motor |
| Python | 3.13 (la exige `bpy` 5.3) | Modelos y texturas |
| `bpy` | 5.3.0 (`pip install bpy==5.3.0`) | Blender como módulo de Python |
| `numpy`, `pillow` | Recientes | Texturas |
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
| `make test-net` | Prueba de red: un anfitrión y un invitado en la misma máquina |
| `make lint` | Revisa el estilo del código GDScript |
| `make capture` | Capturas de las escenas de revisión en `docs/capturas/` |
| `make setup` | Reescribe controles, capas y buses de audio en `project.godot` |

## Los pipelines de arte

Todo se genera por código. **Nunca se editan a mano** los archivos de `assets/models/`, `assets/textures/` ni `assets/ui/`: se edita la receta o el generador y se vuelve a generar.

### Modelos 3D

- Cada archivo de `tools/blender/recipes/` es una receta. Define `models()`, que devuelve un diccionario `nombre → función que construye el modelo`.
- Las utilidades comunes están en `tools/blender/tumansk_bpy.py`: cajas con bisel, piezas de torno (`lathe`), placas con contorno (`prism`), tubos y cintas que siguen una curva (`tube`, `ribbon`, `smooth_path`), imperfección controlada (`wobble`, `dent`, `apply_bulge`), pintura por vértice (color base, oclusión y cavidades) y exportación.
- `make models` (o `python3 tools/blender/build_assets.py nombre`) genera `assets/models/<nombre>.glb`.
- Godot lo importa solo y `tools/godot/post_import.gd` aplica las convenciones de nombre:

| Sufijo | Resultado en Godot |
|---|---|
| `-fisico` | La pieza pasa a ser un `RigidBody3D` |
| `-estatico` | La pieza pasa a ser un `StaticBody3D` |
| `-colcaja` | La malla se sustituye por una colisión de caja |
| `-colconvexa` | La malla se sustituye por una colisión convexa |

El nombre del material elige el material de Godot si existe `assets/materials/<nombre>.tres`; si no, se usa `base_vertex.tres`, que pinta con los colores por vértice.

El generador es reproducible: la misma receta da siempre el mismo archivo, byte a byte. Si un modelo cambia al regenerarlo sin haber tocado su receta, es un fallo.

#### Piezas móviles

Lo que se mueve o se enciende en el juego es un nodo propio dentro del modelo, con el origen en su eje (`tb.set_origin`). En reposo marca el cero o está apagado.

| Modelo | Nodo | Cómo se mueve (en Godot) |
|---|---|---|
| `bascula` | `aguja` | `rotation.z` de 0 a -64° (fondo de escala) |
| `dosimetro` | `aguja` | `rotation.y` de 0 a -90° |
| `dosimetro` | `piloto` | Lámpara: cambiarle el material para encenderla |
| `linterna` | `bombilla`, `foco` | Bombilla apagada (ponerle `bombilla.tres`) y punto donde colgar la luz |
| `mascara` | `cristales` | Material propio, para empañarlos y agrietarlos |
| `estufa` | `brasas` | Rendijas de la puerta: ponerles un material que emita luz |
| `radio` | `mando_volumen`, `mando_brillo`, `mando_sensibilidad` | `rotation.z` |
| `radio` | `aguja`, `piloto` | La aguja se desliza en X ±0,066 m; el piloto se enciende |
| `mostrador` | `cajon` | Se abre deslizándolo 0,3 m hacia -Z |
| `pila_descontaminacion` | `llave`, `agua` | La llave gira en `rotation.y`; el agua se tiñe, sube o se oculta |
| `cuaderno` | `tapa`, `goma`, `lapiz` | La tapa se abre con `rotation.z` de 0 a 180°; la goma se oculta y el lápiz se saca |
| `cuaderno_abierto` | `pagina_izquierda`, `pagina_derecha` | Caras donde se dibuja: UV de 0 a 1 (origen arriba a la izquierda de cada página) y material `papel.tres` |
| `cuaderno_abierto` | `lapiz`, `cinta` | Se ocultan o se mueven |
| `brujula` | `aguja`, `bisel` | `rotation.y`; la aguja en reposo marca el norte (-Z) |
| `linterna_dinamo` | `manivela` | `rotation.x`; lleva también `bombilla` y `foco`, como la linterna de pilas |
| `navaja` | `hoja` | Se pliega dentro del mango con `rotation.y` de 0 a -180° |
| `prismaticos` | `lentes`, `rueda_enfoque` | Los cristales llevan `vidrio.tres` (para el reflejo); la rueda gira en `rotation.z` |
| `despertador` | `aguja_horas`, `aguja_minutos`, `aguja_alarma` | `rotation.z` negativo va en el sentido del reloj; a 0° marcan las doce |
| `despertador` | `martillo`, `llave_cuerda` | El badajo oscila entre las campanas y la llave gira, los dos en `rotation.z` |

Las herramientas que se empuñan (`martillo`, `palanca`, `navaja`) llevan un nodo vacío `agarre` en el punto por donde las coge la mano. La `cizalla`, que es de dos manos, lleva `agarre` y `agarre_2`.

### Ilustraciones 2D

`tools/svg/generate.mjs` dibuja con rough.js (aspecto a mano) y guarda SVG en `assets/ui/`. El texto no va dentro de los SVG: se pone en Godot con las tipografías del juego.

### Texturas

`tools/textures/generate_textures.py` genera el papel, los cuatro tonos de tramado, las rampas del sombreado por bandas y los ruidos. Todas se pueden repetir sin costuras, salvo `pagina_cuadriculada.png`, que es una página entera del cuaderno (la usa `assets/materials/papel.tres`).

## Capturas

`tools/capture.sh res://escena.tscn salida.png [ancho] [alto] [fotogramas]` renderiza con el render real (Forward+) sin pantalla: usa un servidor X virtual y, si no hay GPU, Vulkan por software. Las cámaras del grupo `capture_camera` generan una imagen cada una.

Opciones extra con la variable `CAPTURE_ARGS`:

- `--hide=InkPost`: captura sin el post-proceso del estilo.
- `--post=debug_view=N`: muestra una capa del post-proceso (ver `docs/ESTILO.md`).

Las escenas de revisión del estilo están en `scenes/style/` y se describen en [ESTILO.md](ESTILO.md).

## Cooperativo

El juego arranca siempre como anfitrión sin invitados (`NetSession`). Para probar dos jugadores en la misma máquina, `make test-net` lanza un anfitrión y un invitado y comprueba que el invitado ve moverse la caja de "Hola, Tumansk".
