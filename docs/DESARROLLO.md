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
| ← → | Cambia de diorama (depósito limpio, depósito abandonado y patio de día, al anochecer, de noche y con ventisca, y las hojas de los personajes) |
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
| Mayús+1-0 | Las vistas de la red de tránsito: la Escalinata desde abajo, un cruce del Barrio Obrero, el vano hundido del puente, las escaleras de la loma, los andenes de la estación, la playa de vías, un paso a nivel, un desvío del escape de la playa, un tope y el tranvía por la mediana de la Avenida |
| Ctrl+1-8 | Las vistas del deterioro (el socavón de la avenida, la galería de la calefacción hundida frente a la fábrica y una tubería del agua reventada en la calle de la Juventud), dos de los edificios singulares (el vestíbulo del metro desde la plaza y la Casa de los Sóviets al final de la avenida), la calle de la Planta con el firme levantado en placas, el atasco de la avenida Soviética y los barcos atrapados en el hielo frente a la Estación Fluvial |
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
| `scripts/surface/city_kit.gd` | `CityKit`: los edificios del kit en la maqueta: su ficha, el zócalo en ladera, el foso del vestíbulo en el terreno y qué piezas no proyectan sombra ([D-052](DECISIONES.md)) |
| `scripts/surface/city_terrain.gd` | El relieve por sectores (cada 2 m y cada 8 m) y su colisión |
| `scripts/surface/city_buildings.gd` | Cada edificio a su altura, con su cubierta y lo que queda en pie según su daño |
| `scripts/surface/city_props.gd` | Vehículos (cada uno, su modelo a la medida del plano: `tools/blender/recipes/vehiculos.py`), árboles, puentes, tuberías, vallas, la línea eléctrica y los muros del borde |
| `scripts/surface/city_geometry.gd`, `mesh_buffer.gd` | Cuentas con polígonos y construcción de mallas |
| `scripts/debug/city_mockup.gd` | La escena: vistas, recorridos, panel, capas, pruebas |
| `scripts/debug/mockup_walker.gd`, `city_overlays.gd` | El visitante (andar y volar) y las capas de ayuda |

## El kit de arquitectura (F3-16)

Los edificios de la superficie se montan con piezas: cada familia es una biblioteca (un `.glb` con una malla por pieza) que genera su receta, y Godot coloca las piezas de cada casa según su ficha del plano. Cada pieza se repite con una `MultiMesh`: una llamada de dibujo por pieza y edificio ([D-034](DECISIONES.md)).

| Biblioteca | Receta | Tipos del plano |
|---|---|---|
| `kit_paneles` | `tools/blender/recipes/kit_paneles.py` | Jrushchovka, bloque de 9 plantas y torre de 16 (estos dos, con plaqueta) |
| `kit_estalinka` | `tools/blender/recipes/kit_estalinka.py` | Estalinista y casa obrera |
| `kit_ladrillo` | `tools/blender/recipes/kit_ladrillo.py` | Casa anterior a la revolución (usa las carpinterías, interiores y cubierta de la estalinista) |
| `kit_madera` | `tools/blender/recipes/kit_madera.py` | Isba y barracón: casas enteras, una por estado ([D-037](DECISIONES.md)) |

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
| `scripts/surface/kit_singular.gd` | Los edificios singulares: pone su modelo entero, su colisión y su hueco en el terreno |
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

### Los edificios singulares

Los hitos y los sitios clave no se montan con piezas: cada uno es un modelo entero con su receta, que `KitSingular` pone por su id del plano ([D-038](DECISIONES.md)).

| Biblioteca | Receta | Del plano | Qué tiene |
|---|---|---|---|
| `singular_vestibulo` | `tools/blender/recipes/singular_vestibulo.py` | PLZ-06 | La rotonda por fuera y por dentro, la esclusa con las escaleras y el túnel, la compuerta (aparte, para poder moverla) y el control del ejército |
| `singular_partido` | `tools/blender/recipes/singular_partido.py` | ZC-01 | La estructura rota, las fachadas, los tabiques y la escalera hasta la azotea; los muebles; el montón de escombros |
| `singular_soviets` | `tools/blender/recipes/singular_soviets.py` | CEN-SOV y CEN-SOVT | El bloque quemado con su boquete (su escombro sale a la calle: por él se sube al boquete y se baja al cuarto quemado de detrás, con los archivadores, la caja fuerte y las mesas) y la torre con la aguja doblada y el puesto del vigía (dos modelos: `soviets` y `torre_soviets`) |

- **El marco:** cada modelo se hace en las coordenadas del plano (x al este, y al norte, z arriba) alrededor del «centro» de su ficha, a su cota, y se pone tal cual, sin girarlo ni estirarlo. Dentro de la receta conviene un marco propio (el eje de la rotonda, el eje largo del edificio) y llevarlo al plano al final.
- **Sus piezas** son las mallas que se llaman como el modelo o empiezan por su nombre y un guion bajo. Dos no se dibujan: `<modelo>_colision`, la colisión hecha a mano (suelos, muros, columnas; los escalones y las escaleras son rampas, porque el jugador no sube escalones de 16 cm), y `<modelo>_hueco`, dónde no va el terreno cuando el edificio baja bajo la calle (el foso de las escaleras del metro). Los triángulos del hueco quedan en los metadatos del edificio (`kit_huecos`, en coordenadas de plano): los dioramas recortan su suelo con ellos y la maqueta, su relieve (`CityKit`).
- **La nieve de dentro:** el material `nevado_parcial` pone la nieve que dice el alfa del color de vértice ([D-039](DECISIONES.md)): en el Partido nieva junto al borde roto y las ventanas reventadas, no en el fondo de los pasillos.
- **Para verlos**, con **F6**: `scenes/style/diorama_vestibulo.tscn` (la avenida, el control, la entrada, el peristilo, la sala, la cúpula, la compuerta, las escaleras y desde el aire), `diorama_partido.tscn` (desde el cráter, la casa de muñecas de cerca, la esquina, el testero, la entrada, un pasillo, la escalera, el borde, la azotea y desde el aire) y `diorama_soviets.tscn` (la avenida, la plaza, el pórtico, el escudo, el boquete, su escombro desde la calle, el cuarto quemado de detrás, la esquina, la torre, el vigía y desde el aire). Las cámaras de dentro se ven mejor con `set_flashlight`.

**Para añadir uno:** escribe `tools/blender/recipes/singular_<nombre>.py` con su `models()`, añade su biblioteca a `BuildingKit.LIBRARIES` y su id a `KitSingular.MODELS`, y genera el modelo. El test (`test_singular_buildings_are_whole`) comprueba que no falte ninguna pieza, que tenga colisión, que las piezas ocultas no se dibujen y que quepa en su parcela. Las reglas de modelado son las del kit ([ESTILO.md](ESTILO.md#reglas-de-modelado-para-la-tinta)).

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
| `make test-net` | Pruebas de red: un anfitrión y un invitado en la misma máquina (la caja de la Fase 0 y el depósito) |
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

### Personajes

- `tools/blender/personaje_bpy.py`: piezas blandas con color y pesos de hueso (`Sculpt`), volúmenes sobre los que colocar correas y bolsillos (`Profile`), el esqueleto y las poses con cinemática inversa.
- `tools/blender/personaje_anim.py`: las animaciones, como funciones del tiempo. Un nombre que acaba en `-loop` se importa en bucle.
- `tools/blender/recipes/personajes.py`: `jugador_chico`, `jugador_chica` y las manos de primera persona (`manos_*`).
- En Godot, `PlayerAvatar` (`scripts/actors/player_avatar.gd`) carga el modelo y lo anima: `speed`, `carrying`, `look_pitch`, `expression`, y la mochila, el zurrón y la mascarilla, que se pueden ocultar.
- Para revisarlos: `tools/capture.sh res://scenes/style/personajes_superficie.tscn salida.png`.
- Las manos de primera persona las maneja `FirstPersonArms`; `GripModifier` las pone sobre lo que se sujeta, en puntos de su malla ([D-050](DECISIONES.md)). Dónde se lleva cada cosa lo decide `Player` ([D-049](DECISIONES.md)). Para verlo con distintos objetos: `scenes/style/primera_persona_*.tscn` (con `tools/capture.sh` y 150 fotogramas de espera).

Si cambias un material de `assets/materials/` después de importar un modelo, borra su copia de `.godot/imported/` para que Godot lo importe otra vez.

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
| `vias.py` | El trazado de la red de vías: los desvíos y sus curvas de enlace, los topes, los vagones de la playa y, con las rasantes, cada desvío en 3D para la maqueta |
| `ferrocarril.py` | Las rasantes de las vías del tren, los andenes, los pasos a nivel (la calle y el terreno suben al carril), los tramos de vía que se exportan y las vías del tranvía con sus curvas |
| `rejilla.py` | Lo que el tránsito tapa de cada triángulo de la rejilla del relieve, el relleno exacto y el rebaje de la colisión |
| `deterioro.py` | El deterioro de la superficie: los socavones (contorno, cubeta, malla y lo que cae dentro), las grietas, los baches, las tapas abiertas o robadas, los bordillos que faltan o se han movido y los matojos |
| `firmes.py` | El firme roto: las zonas de calle levantada en placas, con su base y sus placas |
| `restos.py` | Lo tirado por la calle (cascotes, montones de escombros, basura, contenedores) y las farolas, en pie o rotas |
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

El juego arranca siempre como anfitrión sin invitados (`NetSession`). `make test-net` lanza dos pruebas con un anfitrión y un invitado en la misma máquina:

- **caja**: el invitado ve moverse la caja de "Hola, Tumansk".
- **deposito**: el invitado entra en el depósito, recibe su jugador y los 22 objetos, anda, coge una lata, se la lleva y la suelta; el anfitrión comprueba que lo ve andar y llevarla.

Quién manda sobre qué está en [D-003](DECISIONES.md) y [D-046](DECISIONES.md).
