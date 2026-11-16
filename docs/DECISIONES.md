# Registro de decisiones

Decisiones técnicas que conviene recordar, con su motivo. Las nuevas se añaden al final.

## D-001 · Godot 4.7.2

Versión estable más reciente al empezar el proyecto. Queda fijada: no se cambia sin motivo y, si se cambia, se cambia a la vez en el proyecto, en la CI (`GODOT_VERSION`) y en `docs/DESARROLLO.md`.

## D-002 · Ejecutor de tests propio

`tests/run_tests.gd` es un ejecutor mínimo (unas 60 líneas) en lugar de GUT o gdUnit4. No añade dependencias, funciona sin acceso a red y cubre lo que hace falta: tests de lógica sin pantalla, con el árbol de escena y las autocargas disponibles.

## D-003 · Red: siempre hay un anfitrión

En solitario se usa `OfflineMultiplayerPeer`: el jugador es el anfitrión (peer 1) y no tiene invitados. En cooperativo, ENet. El código es el mismo en los dos casos, así que el cooperativo no hay que añadirlo después. El anfitrión tiene la autoridad sobre el mundo; la replicación usa `MultiplayerSynchronizer`.

## D-004 · Modelos en glTF con post-importación propia

Las recetas de Blender exportan `.glb`. `tools/godot/post_import.gd` se aplica a todos los modelos (`importer_defaults` en `project.godot`) y convierte los sufijos de nombre en cuerpos físicos y colisiones, y asigna los materiales.

## D-005 · Pintura por vértice

El color base, la oclusión ambiental y las cavidades se calculan en Blender y se guardan en los colores por vértice. Da el aspecto de objeto pintado a mano sin necesitar una textura para cada objeto, y es barato para la gráfica integrada.

## D-006 · Controles

La fuente de verdad es `tools/godot/setup_project.gd`. Se usan teclas físicas (funcionan igual con cualquier distribución de teclado). Como en otros juegos tácticos: F para interactuar y Q/E para asomarse.

## D-007 · Ilustraciones 2D con rough.js, sin texto dentro

Las ilustraciones se dibujan por código con aspecto de trazo a mano. El texto nunca va dentro del SVG: se pone en Godot con las tipografías del juego, para poder cambiarlo y traducirlo sin regenerar nada.

## D-008 · Post-proceso en un rectángulo a pantalla completa

El estilo se aplica con un `MeshInstance3D` que cubre la pantalla y lee la imagen, la profundidad y las normales (`scenes/style/ink_post.tscn`), en lugar de con un `CompositorEffect`. Es más sencillo de mantener y de depurar, y funciona igual en la gráfica integrada. Si el rendimiento lo pide, se puede pasar a `CompositorEffect` sin tocar el aspecto. El README mencionaba `CompositorEffect`; esta decisión lo sustituye.

## D-009 · Bandas por ángulo, caída suave

El sombreado por bandas depende solo del ángulo con la luz. La caída con la distancia y las sombras proyectadas se aplican después, sin bandas. Con bandas en la caída aparecían círculos de luz muy marcados en las paredes, y quedaba peor.

## D-010 · Parámetros globales de shader y StyleDirector

Todo lo dinámico del estilo (zona, miedo, radiación) viaja en parámetros globales `tinta_*` (declarados en `tools/godot/setup_project.gd`). Los colores globales llegan en sRGB y el shader los convierte a lineal: sin esa conversión, la tinta salía gris lavanda.

## D-011 · Gradación por parámetros, no por LUT

La gradación de color de cada zona (saturación, contraste, tinte) se hace con parámetros en lugar de con una tabla LUT. Así se puede interpolar de forma continua al cambiar de zona y con el miedo. Si más adelante hace falta un control más fino, se añadirá una LUT por encima.

## D-012 · Capturas con Vulkan por software

Las capturas usan el render real (Forward+) con Vulkan por software (lavapipe) y un servidor X virtual. Es lento, unos 10 segundos por imagen, pero el resultado es el mismo que en una GPU.

## D-013 · Cielo pintado y nunca negro

El cielo es un shader propio (`assets/shaders/cielo.gdshader`): degradado, resplandor del sol o de la luna y nubes en dos tonos, con contorno de tinta y algo de tramado. Cada momento del día (día, anochecer, noche) es un conjunto de valores en `scripts/surface/atmosphere.gd`, que también fija la luz ambiente, la niebla, el sol y el estilo. Regla de la revisión 1: el cielo se ve siempre, también de noche.

## D-014 · Siluetas lejanas sin luz ni niebla

Las ruinas del horizonte y la Zona Cero usan `tinta_lejano.gdshader`: color plano, derivado del color del horizonte (parámetro global `tinta_horizonte`) y más oscuro cuanto más cerca está la capa. Así se leen como decorados de papel recortado a cualquier distancia, sin depender de la niebla del motor, que a esas distancias lo borraría todo.

## D-015 · La superficie nunca es blanca

Revisión 1: el exterior no puede verse limpio ni pálido. La nieve es vieja (ceniza, hollín, barro; el shader nunca la deja blanca), los bloques llevan chorretones, hollín de incendio y daños, y la gradación de la superficie es más oscura y con más tramado.

## D-016 · La noche se ve con linterna

Revisión 2: de noche, sin linterna prácticamente no se ve nada. El relleno de tinta se oscurece hasta casi negro (`tinta_negro`) y los contornos solo se dibujan donde llega algo de luz: en la oscuridad total no hay información gratis. El cielo sigue distinguiéndose apenas, para leer las siluetas de los edificios. La linterna es un foco cálido que sale de la mano del jugador.

## D-017 · El mundo vivo tiene fase propia

Como en *Rain World*, el mundo funciona sin el jugador: rutinas de día y de noche, caza, peleas y rastros que quedan. Se construye en la Fase 4, antes del vertical slice, porque todas las amenazas se apoyan en ese sistema (`WorldSim`: simulación completa cerca de los jugadores y abstracta en el resto). Las fases siguientes se renumeran (vertical slice = Fase 5).

## D-018 · La ciudad es un plano de datos

Antes de construir nada se fija el plano entero ([docs/CIUDAD.md](CIUDAD.md)). La fuente de verdad es `tools/ciudad/datos.py`: cada calle, manzana, edificio, guarida, ruta y peligro tiene su posición y su descripción. `plano.py` lo valida, lo exporta a `data/ciudad/plano.json` (con el relieve en `relieve.png`) y dibuja las hojas de desarrollo. La validación comprueba que nada se solape, que nada pise la calle ni el río y que cada edificio esté en su zona, y la CI la ejecuta en cada cambio. El trazado se decide a mano y con lógica de ciudad real. Los edificios se levantarán con el kit modular a partir de esos datos (primero en una maqueta automática, Fase 3) y los sitios clave se terminan a mano.

## D-019 · Los daños se calculan, no se reparten al azar

El nivel de daño de cada edificio sale de su distancia a la Zona Cero (cuatro anillos), con una variación fija por edificio y excepciones a mano. Los escombros caen del lado contrario a la bomba y los árboles tumbados apuntan lejos de ella, así que la destrucción tiene dirección y sirve para orientarse. La lluvia radiactiva cae en una franja hacia el sureste.

## D-020 · Contorno de casco construido en el juego

El casco invertido de los objetos clave no se exporta desde Blender: `InkHull` lo construye al cargar el objeto, a partir de su propia malla, con las normales suavizadas por posición y en caché. Así cualquier modelo, actual o futuro, puede llevarlo sin tocar su receta. El grosor se mide en píxeles (en el shader), no en metros, para que el trazo sea igual de cerca que de lejos, como el del post-proceso.

## D-021 · Tipografías

Caveat (manuscrita), PT Mono (a máquina), Oswald (rótulos) y PT Sans (texto). Las cuatro tienen licencia OFL, español completo y cirílico. Las de ParaType (PT) nacieron para el ruso y encajan con el diseño soviético. Se guardan en `assets/fonts/` con su licencia; vienen de los paquetes de npm `@expo-google-fonts`, que traen los TTF originales de Google Fonts.

## D-022 · Vídeo con el modo película de Godot

El vídeo de revisión se graba con `--write-movie`, a fotogramas fijos (12 por segundo, que casa con el trazo vivo a saltos), y luego se convierte con ffmpeg. Sin GPU es lento (unos dos minutos para 33 segundos a 720p), pero sale exactamente lo que se ve en el juego.

## D-023 · Un solo kit de modelos, con el generador reproducible

Los modelos se hicieron en dos ramas a la vez. Al juntarlas, de los objetos que estaban en las dos (la báscula, el dosímetro, la linterna, la máscara y el quiosco) se quedan los de la rama de modelos, más trabajados, y los otros se borran con sus recetas: no hay dos versiones del mismo objeto. El generador es el reproducible de esa rama (sin conjuntos en el orden de las aristas, vértices soldados y geometría ordenada), así que la misma receta da siempre el mismo archivo, byte a byte: un `.glb` solo cambia cuando cambia su receta. Los muebles y el equipo que esa rama adelantó para las Fases 2 y 3 ya se usan en el depósito y en la mesa del equipo.

## D-024 · La maqueta se levanta al abrirla, desde los datos del plano

La maqueta automática de la ciudad (F3-15, `scenes/debug/maqueta_ciudad.tscn`) no se guarda como escena: `City` la construye al abrirla a partir de `data/ciudad/` (plano, relieve y suelo), en un segundo y medio. Así nunca se queda desfasada respecto al plano: se cambia `tools/ciudad/datos.py`, se ejecuta `make ciudad` y la próxima vez que se abre ya es la ciudad nueva. Godot no importa `data/ciudad/` (`.gdignore`): los archivos se leen tal cual, y el relieve de 16 bits se descomprime en GDScript (`CityPlan.decode_gray16`), porque el cargador de PNG de Godot lo reduce a 8 bits y se perderían los centímetros. Por eso la maqueta funciona ejecutando desde el proyecto (el editor), no en una build exportada. Cuando la ciudad pase al juego, el plano se convertirá en recursos de Godot.

## D-025 · Del plano al mundo: el norte es -Z

El plano mide en metros con x hacia el este e y hacia el norte. En el mundo de Godot, el punto (x, y) a la altura h es `Vector3(x, h, -y)`: el este es +X y el norte es -Z, como la aguja de la brújula. El origen es la esquina suroeste del mapa. La conversión está en un solo sitio (`CityPlan.to_world` y `CityPlan.to_plan`).

## D-026 · Sectores con dos niveles de detalle; lo lejano, del color de la niebla

Cada sector de 200 × 200 m tiene una versión lejana (el relieve cada 8 m y los edificios en un solo bloque) y una detallada (el relieve cada 2 m, cada edificio con sus ventanas, los vehículos, los árboles y las estructuras). La detallada se dibuja cuando la cámara está a menos de 450 m del centro del sector; si no, la lejana (HLOD con `visibility_parent`, sin huecos ni solapes). La versión lejana se pinta del color de la niebla, sin luz (`tinta_silueta.gdshader`): con la niebla del juego, a esa distancia lo detallado ya se ve exactamente así, de modo que el cambio no se nota y cuesta muy poco. Lo que destaca contra el cielo es el perfil de la ciudad. El color de la niebla llega a los shaders por dos parámetros globales nuevos, `tinta_niebla` y `tinta_niebla_densidad`, que fija `Atmosphere`. Los edificios grandes y el relieve son oclusores.

## D-027 · Los hitos atraviesan la niebla

Sin mapas, el jugador se orienta con lo que ve de lejos (docs/CIUDAD.md, sección 8), pero la niebla de día del estilo (densidad 0,011) lo borra todo a partir de unos 300 m. Los hitos se dibujan con `tinta_hito.gdshader`, que les pone su propia niebla con un tope: como mucho los tapa un 78 %. Se ven siempre, como siluetas apagadas, igual que las ruinas del horizonte del patio (D-014). Es una propuesta pendiente de tu revisión: el tope se ajusta en el material (`hito_niebla_max`). La maqueta cuenta los hitos que se ven desde cada punto y comprueba la regla del plano en toda la ciudad.

## D-028 · El suelo de la ciudad lo pinta el plano

`tools/ciudad/plano.py` exporta, además del plano y el relieve, `data/ciudad/suelo.png` (1 m por píxel): el color del suelo bajo la nieve (calzadas, aceras, plazas, hielo, vías, patios, escombros) y, en el canal alfa, cuánta nieve lo cubre. Se pinta con las mismas figuras de shapely que valida el plano, así que el suelo de la maqueta coincide con las hojas. También exporta la cota de cada edificio (el terreno sin escombros bajo su huella: los muñones quedan medio enterrados en su propio escombro), los árboles (que antes solo existían en el dibujo; las hojas no cambian) y las medidas de los vehículos. Al exportar, las huellas que el redondeo a 0,1 m dejaba con astillas cruzadas se limpian. El daño de cada edificio se expresa en la maqueta con reglas fijas (el extremo que mira a la bomba se hunde, cascarones, muñones) y las mismas semillas que usa `plano.py` (`CityPlan.chance` da los mismos números que `azar`).

## D-034 · Los edificios se montan con piezas, una MultiMesh por pieza

Los edificios de la superficie (F3-16) no se modelan enteros: cada familia (paneles, mampostería, madera) es una biblioteca de piezas, un `.glb` con una malla por pieza que genera su receta, y `BuildingKit` coloca las de cada casa según su ficha del plano. Las piezas miden un vano de ancho y una planta de alto, con el origen en el arranque del vano, en la cara del muro; las reglas de cada familia las estiran lo justo para que los vanos llenen la huella y las plantas tengan su altura. Cada pieza se repite con una `MultiMesh` (una llamada de dibujo por pieza y edificio): el tono de cada casa y de cada panel va en el color de la instancia, y el desgaste y el hollín, en sus datos. El daño sigue las reglas y las semillas de la maqueta (`CityPlan.chance`), así que una casa se hunde por el mismo extremo en los dos.

## D-035 · Los muros se ensucian en el shader, en el espacio del mundo

La suciedad, los chorretones, el aparejo del ladrillo, la plaqueta y el revoque caído los calcula `tinta_muro.gdshader` con la posición en el mundo: siguen de una pieza a la siguiente sin costuras ni repeticiones y no cuestan vértices. Lo que depende de la pieza va en el color de vértice (el alfa marca dónde va la plaqueta o dónde se cae antes el revoque: junto a los huecos y abajo) y lo que depende de la casa llega por instancia (el desgaste, el hollín y de dónde sale). La oclusión, las cavidades y los chorretones de óxido se pintan al generar cada pieza, con lo que tendrá alrededor al montarla.

## D-036 · Nada plano y estrecho: molduras con perfil y juntas enrasadas

El contorno de tinta dibuja a puntos las caras que ocupan menos de un píxel: las de abajo de las molduras vistas desde la calle, las de arriba de los zócalos y los cantos a escuadra de lo que sobresale poco, sobre todo de lejos, a ras y en sombra. Hacer las molduras más gruesas no basta (a ras siguen siendo finas) y tocar el post-proceso cambiaría todo el estilo, así que se modela a prueba de tinta, como la arquitectura clásica: molduras con perfil (vierteaguas y caras de abajo en derrame), cantos inclinados, esquinas a inglete, juntas de color enrasadas y piezas que no se descolocan al montarlas. Las reglas están en [ESTILO.md](ESTILO.md#9-los-edificios-del-kit-f3-16). Los travesaños de las carpinterías se quedan como están: enrasar el cristal quitaría sus puntos, pero también las líneas de los paños de cerca.

## D-037 · Las casas de madera, enteras y por estado

La isba (9 × 8 m) y el barracón (30 × 11 m) tienen las medidas fijas en el plano y casi todos ardieron, así que no se montan por vanos: el kit guarda cada casa entera en cada estado (abandonada, chamuscada, cascarón y quemada) y `KitWhole` escoge la suya por el daño y el incendio de la ficha y la encaja en la huella, por su lado largo y estirada lo poco que haga falta. Una casa entera es una sola llamada de dibujo.
