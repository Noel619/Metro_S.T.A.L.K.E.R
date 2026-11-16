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

Tumansk entera, levantada desde el plano en volúmenes sencillos para probar recorridos, vistas, sectores de carga y rendimiento. Para abrirla: en Godot, abre `scenes/debug/maqueta_ciudad.tscn` y pulsa **F6** (ejecutar la escena actual). Tarda un par de segundos en levantar la ciudad. Empiezas a pie en la salida del metro, a mediodía.

| Tecla | Qué hace |
|---|---|
| Clic / Esc | Captura el ratón para mirar / lo suelta |
| W A S D | Moverse. Andando: Mayús corre, C se agacha, Espacio salta. Volando: Mayús acelera, Espacio sube, C baja y la rueda cambia la velocidad |
| Tab | Andar (con colisión, a 1,4 m/s) o volar (sin colisión) |
| 1-9 y 0 | Las vistas fijas: la salida, la avenida, Los Bloques, el río, el puente, la Escalinata, la zona industrial, la Zona Cero, la ciudad desde el aire y las rutas desde el aire |
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

## El kit de arquitectura (F3-16)

Los edificios de la superficie se montan con piezas: cada familia es una biblioteca (un `.glb` con una malla por pieza) que genera su receta, y Godot coloca las piezas de cada casa según su ficha del plano. Cada pieza se repite con una `MultiMesh`: una llamada de dibujo por pieza y edificio ([D-029](DECISIONES.md)).

| Biblioteca | Receta | Tipos del plano |
|---|---|---|
| `kit_paneles` | `tools/blender/recipes/kit_paneles.py` | Jrushchovka, bloque de 9 plantas y torre de 16 (estos dos, con plaqueta) |
| `kit_estalinka` | `tools/blender/recipes/kit_estalinka.py` | Estalinista y casa obrera |
| `kit_ladrillo` | `tools/blender/recipes/kit_ladrillo.py` | Casa anterior a la revolución (usa las carpinterías, interiores y cubierta de la estalinista) |
| `kit_madera` | `tools/blender/recipes/kit_madera.py` | Isba y barracón: casas enteras, una por estado ([D-032](DECISIONES.md)) |

**Para verlos**, en Godot, con **F6**:

- `scenes/style/diorama_edificios.tscn`: una calle de Los Bloques hecha a mano, con cada tipo y cada daño, las isbas y los barracones. Sus cámaras: jrushchovka, portal, balcones, bloque y torre, daños, cascarón, muñones, la casa obrera y la de ladrillo, las isbas, el piñón de una isba y el barracón (también a ras de su fachada).
- `scenes/style/diorama_plaza.tscn` y `diorama_mercaderes.tscn`: las casas del plano que el kit sabe montar alrededor de la plaza del Trabajo y en el barrio de los mercaderes, tal como son (con su daño real: los mercaderes están cerca de la bomba).
- Los tres tienen `mood` (día, anochecer, noche), `hour`, `weather` y `flashlight` en el inspector. Para las capturas: `set_hour`, `set_flashlight` y `capture_only` (por ejemplo, `--call=DioramaEdificios:capture_only:portal,pinon`).

**El código:**

| Archivo | Qué hace |
|---|---|
| `scripts/surface/building_kit.gd` | `BuildingKit`: carga las bibliotecas, viste las piezas con las pieles de cada tipo y monta un edificio desde su ficha |
| `scripts/surface/kit_assembly.gd` | `KitAssembly`: junta las piezas de un edificio y crea una `MultiMesh` por pieza |
| `scripts/surface/kit_rules.gd` | Lo común a las familias: la ficha, el azar con semilla (la misma casa sale siempre igual), el marco de cada pieza, los estados de las ventanas y el hollín |
| `scripts/surface/kit_panel_block.gd` | Los bloques de paneles: portales, escaleras, balcones y logias, paneles caídos, muñones, el peto y los cortes |
| `scripts/surface/kit_masonry.gd` | Las casas de muros de carga, sobre cualquier huella (rectas, curvas, en L): bajos, plantas, pilastras, esquinas, cornisa, cubierta, patios y arcos |
| `scripts/surface/kit_whole.gd` | Las casas de madera: escoge la de su estado y la encaja en la huella |
| `tools/blender/kit_bpy.py` | Las utilidades de las recetas: la biblioteca y la pintura con contexto, las carpinterías, los interiores falsos, los daños y las molduras a prueba de tinta |
| `assets/shaders/tinta_muro.gdshader` | Los muros: suciedad, chorretones, hollín, revoque caído y plaqueta ([ESTILO.md](ESTILO.md#9-los-edificios-del-kit-f3-16)) |
| `scripts/debug/buildings_diorama.gd` | Los dioramas |
| `tests/unit/test_building_kit.gd` | Que estén todas las piezas que piden las reglas, que la misma ficha dé siempre el mismo edificio, los daños y que se monten todas las viviendas del plano |

**La ficha de un edificio** (`BuildingKit.build(spec)`) es un diccionario: `tipo`, `huella` (la planta en metros, x al este e y al norte), `origen`, `pisos`, `dano` (1 a 4), `incendio` (`no`, `parcial`, `total`), `clave` (la semilla: la misma ficha da siempre la misma casa) y `bomba` (dónde cayó). Cada familia admite algo más: los bloques, `entrada` (el lado de los portales) y `portales`; las casas de muros de carga, `patios`, `comercios` y `arco`. El detalle está al principio de `building_kit.gd`.

**Las piezas** siguen las convenciones de `kit_bpy.py`: el origen es el arranque de un vano en la cara exterior del muro, x corre a lo largo de la fachada, z hacia arriba y el muro va de y = 0 hacia +y (lo que sobresale queda en y < 0). Al montarlas, cada instancia lleva en el color su tono y en los datos de instancia el desgaste y el hollín del incendio, que lee el shader.

**Para añadir una pieza:**

1. Constrúyela en su receta y guárdala con `lib.add(pieza, contexto, alpha=..., seed=...)`. El contexto son las piezas que tendrá alrededor al montarla (los muros vecinos, el forjado, las carpinterías): se usa para pintar la oclusión y no se exporta. `alpha` es la máscara que leen los shaders de muro (dónde va la plaqueta o dónde se cae antes el revoque).
2. Sigue las reglas de modelado para la tinta ([ESTILO.md](ESTILO.md#9-los-edificios-del-kit-f3-16)): para las molduras, `kit.moulding` (con `mitre` si acaba en el aire), `kit.moulding_run`, `kit.corner`, `kit.outline`, `kit.block` y `kit.ring`.
3. Regenera la biblioteca (`python3 tools/blender/build_assets.py kit_estalinka`) y comprueba que las demás no cambian (`git status`).
4. Úsala en las reglas de su familia con `assembly.put("nombre", transformación, tono, datos)`. Si pides una pieza que no existe, el edificio la apunta en sus metadatos (`kit_faltan`) y el test lo detecta.
5. Mírala en los dioramas, de cerca, de lejos y a ras, de día y de noche. Para cazar caras de menos de un píxel, `CAPTURE_ARGS="--post=debug_view=2"` (las normales) enseña los píxeles sueltos.

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
- Las utilidades comunes están en `tools/blender/tumansk_bpy.py`: cajas con bisel, piezas de torno (`lathe`), placas con contorno (`prism`), tubos y cintas que siguen una curva (`tube`, `ribbon`, `smooth_path`), imperfección controlada (`wobble`, `dent`, `apply_bulge`), pintura por vértice (color base, oclusión y cavidades) y exportación. Las del kit de arquitectura, en `tools/blender/kit_bpy.py`.
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
| `plano.py` | Valida, calcula daños, escombros, relieve y cotas, y exporta el plano (`plano.json`), el relieve (`relieve.png`) y el suelo de la maqueta (`suelo.png`) |
| `dibujo.py` | Dibuja las cuatro hojas de desarrollo |

Para dibujar una sola hoja: `python3 tools/ciudad/plano.py --plano=general` (también `subsuelo`, `peligros` o `rutas`).

## Capturas

`tools/capture.sh res://escena.tscn salida.png [ancho] [alto] [fotogramas]` renderiza con el render real (Forward+) sin pantalla: usa un servidor X virtual y, si no hay GPU, Vulkan por software. Las cámaras del grupo `capture_camera` generan una imagen cada una. En la maqueta, las cámaras de las capturas son sus vistas fijas: `tools/capturas_docs.sh maqueta` rehace las suyas (con `--call=MaquetaCiudad:capture_only:avenida` se captura una sola).

Opciones extra con la variable `CAPTURE_ARGS`:

- `--hide=InkPost`: captura sin el post-proceso del estilo.
- `--post=debug_view=N`: muestra una capa del post-proceso (ver `docs/ESTILO.md`).

Las escenas de revisión del estilo están en `scenes/style/` y se describen en [ESTILO.md](ESTILO.md). `tools/capturas_docs.sh [filtro]` rehace las capturas de `docs/capturas/` (o solo las de un grupo: `deposito`, `equipo`, `patio`, `interfaz`, `maqueta`, `kit`); dice qué cámara de cada escena va a la documentación y con qué nombre. Las de interfaz (`scenes/ui/prueba_interfaz.tscn` y `prueba_tipografia.tscn`) son 2D: se capturan igual, sin cámara.

Con `CAPTURE_ARGS="--call=Nodo:metodo[:valor]"` se llama a un método antes de capturar; por ejemplo, el panel de depuración abierto a las 18:45:

```bash
CAPTURE_ARGS="--call=VisorEstilo:_load:3 --call=DioramaPatio:set_hour:18.75 --call=PanelDepuracion:toggle" tools/capture.sh res://scenes/style/visor_estilo.tscn panel.png
```

## Vídeo

`tools/video.sh salida.mp4 [ancho] [alto] [fps]` graba `scenes/debug/video_dioramas.tscn` con el modo película de Godot y lo convierte a MP4 con ffmpeg. El director (`scripts/debug/video_director.gd`) encadena los planos: cada uno carga un diorama, mueve su cámara entre dos puntos y anima la hora, el miedo o la linterna.

## Cooperativo

El juego arranca siempre como anfitrión sin invitados (`NetSession`). Para probar dos jugadores en la misma máquina, `make test-net` lanza un anfitrión y un invitado y comprueba que el invitado ve moverse la caja de "Hola, Tumansk".
