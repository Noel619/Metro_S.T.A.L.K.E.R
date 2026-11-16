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

## La maqueta de la ciudad (F3-15)

Tumansk entera, levantada desde el plano en volúmenes sencillos para probar recorridos, vistas, sectores de carga y rendimiento. Para abrirla: en Godot, abre `scenes/debug/maqueta_ciudad.tscn` y pulsa **F6** (ejecutar la escena actual). Tarda unos segundos en levantar la ciudad (la red de tránsito se levanta sector a sector en varios hilos). Empiezas a pie en la salida del metro, a mediodía.

| Tecla | Qué hace |
|---|---|
| Clic / Esc | Captura el ratón para mirar / lo suelta |
| W A S D | Moverse. Andando: Mayús corre, C se agacha, Espacio salta. Volando: Mayús acelera, Espacio sube, C baja y la rueda cambia la velocidad |
| Tab | Andar (con colisión, a 1,4 m/s) o volar (sin colisión) |
| 1-9 y 0 | Las vistas fijas: la salida, la avenida, Los Bloques, el río, el puente, la Escalinata, la zona industrial, la Zona Cero, la ciudad desde el aire y las rutas desde el aire |
| Mayús+1-8 | Las vistas de la red de tránsito: la Escalinata desde abajo, un cruce del Barrio Obrero, el vano hundido del puente, las escaleras de la loma, los andenes de la estación, la playa de vías, un paso a nivel y el tranvía por la mediana de la Avenida |
| R / Mayús+R | Recorre la ruta siguiente / anterior del plano a paso de persona, con cronómetro. **+** y **-** la aceleran (×4, ×16); Retroceso la para |
| F2 / F3 / F4 | Capas: las rutas; la rejilla de sectores y las zonas; los hitos que se ven desde donde estás |
| V | Comprueba en toda la ciudad la regla «desde cualquier punto se ven al menos dos hitos» y marca los puntos ciegos (rosa: ninguno; amarillo: uno) |
| N | Niebla: la del juego, una ligera o ninguna (sin niebla, todos los sectores detallados) |
| O / P / L | Oclusión sí o no / post-proceso de tinta sí o no / linterna |
| B | Prueba de rendimiento: recorre las vistas a pie de calle y da los fps (media y peor momento), las llamadas de dibujo y los triángulos |
| F1 | El panel de depuración: hora del día, clima, miedo, radiación y estilo |
| F9 | Oculta el texto |

El panel de arriba dice dónde estás (sector, zona, coordenadas del plano, rumbo), qué edificio tienes delante (su id del plano, plantas, altura y lo que queda en pie, daño e incendio), qué hitos se ven desde ahí y cuánto cuesta la imagen (fps, llamadas de dibujo, triángulos, sectores detallados).

Es una herramienta de desarrollo: lee `data/ciudad/` directamente (ver [D-024](DECISIONES.md)), así que funciona desde el editor, no en una build exportada. El código:

| Archivo | Qué hace |
|---|---|
| `scripts/surface/city_plan.gd` | `CityPlan`: lee el plano, el relieve (16 bits) y el suelo; alturas, sectores, zonas y conversión de coordenadas |
| `scripts/surface/city.gd` | `City`: levanta los 48 sectores, cada uno con su versión lejana y la detallada, colisión y oclusores |
| `scripts/surface/city_terrain.gd` | El relieve por sectores (cada 2 m y cada 8 m) y su colisión |
| `scripts/surface/city_buildings.gd` | Cada edificio a su altura, con su cubierta y lo que queda en pie según su daño |
| `scripts/surface/city_props.gd` | Vehículos, árboles, puentes, tuberías, vallas, la línea eléctrica y los muros del borde |
| `scripts/surface/city_geometry.gd`, `mesh_buffer.gd` | Cuentas con polígonos y construcción de mallas |
| `scripts/debug/city_mockup.gd` | La escena: vistas, recorridos, panel, capas, pruebas |
| `scripts/debug/mockup_walker.gd`, `city_overlays.gd` | El visitante (andar y volar) y las capas de ayuda |

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
| `make capturas-docs` | Rehace las capturas de la documentación (`docs/capturas/`) |
| `make video` | Vídeo de los dioramas en `capturas/dioramas.mp4` |
| `make setup` | Reescribe controles, capas y buses de audio en `project.godot` |
| `make ciudad` | Valida el plano de la ciudad, exporta `data/ciudad/` y dibuja las hojas de `docs/ciudad/` |
| `make ciudad-comprobar` | Solo valida y exporta el plano (lo que hace la CI) |

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

### El plano de la ciudad

`tools/ciudad/` contiene el plano de Tumansk ([CIUDAD.md](CIUDAD.md)):

| Archivo | Qué hace |
|---|---|
| `datos.py` | Los datos: zonas, calles, edificios, patios, vehículos, hitos, subsuelo, amenazas, peligros y rutas |
| `geo.py` | Marcos de referencia (el eje monumental) y figuras |
| `relieve.py` | El terreno: río, loma, barranco, colina y cráter |
| `plano.py` | Valida, calcula daños, escombros, relieve y cotas, y exporta el plano (`plano.json`), el relieve (`relieve.png`), el suelo de la maqueta (`suelo.png`) y la red de tránsito (`transito.json`, `rasante.png`, `rejilla.png` y `rebaje.png`) |
| `transito.py` | Traza la red de tránsito (calles, aceras, plazas, sendas, escaleras, el puente, los andenes, los pasos a nivel y la cama del tranvía) con sus alturas, aristas, marcas y detalles |
| `ferrocarril.py` | Las rasantes de las vías del tren, los andenes, los pasos a nivel (la calle y el terreno suben al carril), los tramos de vía que se exportan y las vías del tranvía con sus curvas |
| `rejilla.py` | Lo que el tránsito tapa de cada triángulo de la rejilla del relieve, el relleno exacto y el rebaje de la colisión |
| `dibujo.py` | Dibuja las cuatro hojas de desarrollo |

Para dibujar una sola hoja: `python3 tools/ciudad/plano.py --plano=general` (también `subsuelo`, `peligros` o `rutas`).

## Capturas

`tools/capture.sh res://escena.tscn salida.png [ancho] [alto] [fotogramas]` renderiza con el render real (Forward+) sin pantalla: usa un servidor X virtual y, si no hay GPU, Vulkan por software. Las cámaras del grupo `capture_camera` generan una imagen cada una. En la maqueta, las cámaras de las capturas son sus vistas fijas: `tools/capturas_docs.sh maqueta` rehace las suyas (con `--call=MaquetaCiudad:capture_only:avenida` se captura una sola).

Opciones extra con la variable `CAPTURE_ARGS`:

- `--hide=InkPost`: captura sin el post-proceso del estilo.
- `--post=debug_view=N`: muestra una capa del post-proceso (ver `docs/ESTILO.md`).

Las escenas de revisión del estilo están en `scenes/style/` y se describen en [ESTILO.md](ESTILO.md). `tools/capturas_docs.sh [filtro]` rehace las capturas de `docs/capturas/` (o solo las de un grupo: `deposito`, `equipo`, `patio`, `interfaz`, `maqueta`); dice qué cámara de cada escena va a la documentación y con qué nombre. Las de interfaz (`scenes/ui/prueba_interfaz.tscn` y `prueba_tipografia.tscn`) son 2D: se capturan igual, sin cámara.

Con `CAPTURE_ARGS="--call=Nodo:metodo[:valor]"` se llama a un método antes de capturar; por ejemplo, el panel de depuración abierto a las 18:45:

```bash
CAPTURE_ARGS="--call=VisorEstilo:_load:3 --call=DioramaPatio:set_hour:18.75 --call=PanelDepuracion:toggle" tools/capture.sh res://scenes/style/visor_estilo.tscn panel.png
```

## Vídeo

`tools/video.sh salida.mp4 [ancho] [alto] [fps]` graba `scenes/debug/video_dioramas.tscn` con el modo película de Godot y lo convierte a MP4 con ffmpeg. El director (`scripts/debug/video_director.gd`) encadena los planos: cada uno carga un diorama, mueve su cámara entre dos puntos y anima la hora, el miedo o la linterna.

## Cooperativo

El juego arranca siempre como anfitrión sin invitados (`NetSession`). Para probar dos jugadores en la misma máquina, `make test-net` lanza un anfitrión y un invitado y comprueba que el invitado ve moverse la caja de "Hola, Tumansk".
