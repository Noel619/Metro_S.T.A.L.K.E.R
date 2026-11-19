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

## D-029 · La red de tránsito: el plano decide, la maqueta construye

Las calles, aceras, plazas, sendas y escaleras se trazan en Python (`tools/ciudad/transito.py`) con las mismas figuras que valida el plano, y se exportan a `data/ciudad/transito.json` como grupos de superficie triangulados en planta, cada uno con su regla de altura (la rasante más el nivel de su clase, un plano o la rampa del puente), y aristas ya clasificadas (bordillo, borde, contrahuella, muro, pretil…). La rasante (`rasante.png`) es el terreno nivelado sin escombros, con los muelles rellenos. Godot (`CityTransit`) solo construye: corta las superficies por la rejilla del relieve donde la rasante no es plana y extruye el perfil de cada arista. Lo caro de decidir y lo que hay que validar se queda en Python; lo que pesa (los triángulos) no va en el repositorio.

## D-030 · El terreno se recorta bajo el tránsito

El tránsito no se pone encima del terreno: la acera va 3 cm por encima de la rasante y la calzada 12 cm por debajo (con bordillo de 15 cm), como en una calle de verdad. Para que el terreno no asome ni deje zanjas, `tools/ciudad/rejilla.py` decide qué hace la maqueta con cada triángulo de la rejilla de 2 m: los que tapa el tránsito no se dibujan; donde una acera llega a la tierra se dibuja el terreno debajo; donde lo que se pisa va por debajo del terreno se dibuja aparte, exacto, lo que queda de tierra (`rejilla.png` y el relleno de `transito.json`). La colisión del relieve se rebaja bajo el tránsito (`rebaje.png`). Los montones de escombros que caen a la calle se dibujan rebajados igual y asoman sobre el asfalto. Las calles de la falda de la loma se nivelan de lado a lado en el propio relieve, con un talud de 8 m.

## D-031 · La Escalinata, horizontal de lado a lado

La ladera cae de través bajo la Escalinata (un 14 % en 40 m de ancho). Los peldaños van horizontales y la escalera queda excavada a un lado (muro de contención) y en alto al otro (muro con pretil), con siete tramos y descansillos colocados donde la ladera se allana. Para que el primer peldaño sea horizontal, la parte de la plaza del Puente Norte que queda al pie pasa a ser el rellano de abajo, a la cota del muelle, y lo que la plaza tenía ladera arriba, al otro lado de la Bajada, queda en tierra. La cabeza se allana de lado a lado (solo en la rasante: lo que asoma del terreno lo cierra un borde). El Bulevar del Río pierde el trozo que caía sobre los tramos y llega a la Escalinata por la plaza de la cabeza.

## D-032 · Las vías del tren llevan su propia rasante

Cada vía del tren tiene su rasante (`tools/ciudad/ferrocarril.py`), que no es la del terreno: lo sigue sin pasar de la pendiente de su clase (1,2 % la principal y la playa, 2,5 % los apartaderos), no baja de la corona de su terraplén, va recta de estribo a estribo por el puente y queda atada a la vía de la que sale. El relieve se nivela después a lo largo de cada vía (caja y talud), salvo bajo el puente. Así una vía nunca sube ni baja más de lo que puede un tren, y la estación, la playa y los andenes quedan en llano. Los andenes son los altos soviéticos (1,10 m sobre el carril) y los vehículos de la vía se apoyan en el carril. En la maqueta, el balasto y los carriles son perfiles extruidos y las traviesas instancias; cada sector levanta solo los tramos que le tocan.

## D-033 · Pasos a nivel y tranvía, siempre a ras

Donde el tren cruza una calle, la calle sube hasta el carril (no al revés: la vía no puede quebrar su rasante), con una losa de hormigón de lado a lado de la calle y el terreno subiendo con ella como un terraplén; así ningún carril hace escalón con un bordillo y no hacen falta pretiles junto a la vía. El tranvía va siempre a ras de la calzada: donde su vía pisa algo peatonal o la tierra, una cama de losas a la altura de la calzada le abre paso. Sus curvas se redondean a 20 m de radio, porque el trazado del plano giraba en seco.

## D-034 · Los edificios se montan con piezas, una MultiMesh por pieza

Los edificios de la superficie (F3-16) no se modelan enteros: cada familia (paneles, mampostería, madera) es una biblioteca de piezas, un `.glb` con una malla por pieza que genera su receta, y `BuildingKit` coloca las de cada casa según su ficha del plano. Las piezas miden un vano de ancho y una planta de alto, con el origen en el arranque del vano, en la cara del muro; las reglas de cada familia las estiran lo justo para que los vanos llenen la huella y las plantas tengan su altura. Cada pieza se repite con una `MultiMesh` (una llamada de dibujo por pieza y edificio): el tono de cada casa y de cada panel va en el color de la instancia, y el desgaste y el hollín, en sus datos. El daño sigue las reglas y las semillas de la maqueta (`CityPlan.chance`), así que una casa se hunde por el mismo extremo en los dos.

## D-035 · Los muros se ensucian en el shader, en el espacio del mundo

La suciedad, los chorretones, el aparejo del ladrillo, la plaqueta y el revoque caído los calcula `tinta_muro.gdshader` con la posición en el mundo: siguen de una pieza a la siguiente sin costuras ni repeticiones y no cuestan vértices. Lo que depende de la pieza va en el color de vértice (el alfa marca dónde va la plaqueta o dónde se cae antes el revoque: junto a los huecos y abajo) y lo que depende de la casa llega por instancia (el desgaste, el hollín y de dónde sale). La oclusión, las cavidades y los chorretones de óxido se pintan al generar cada pieza, con lo que tendrá alrededor al montarla.

## D-036 · Nada plano y estrecho: molduras con perfil y juntas enrasadas

El contorno de tinta dibuja a puntos las caras que ocupan menos de un píxel: las de abajo de las molduras vistas desde la calle, las de arriba de los zócalos y los cantos a escuadra de lo que sobresale poco, sobre todo de lejos, a ras y en sombra. Hacer las molduras más gruesas no basta (a ras siguen siendo finas) y tocar el post-proceso cambiaría todo el estilo, así que se modela a prueba de tinta, como la arquitectura clásica: molduras con perfil (vierteaguas y caras de abajo en derrame), cantos inclinados, esquinas a inglete, juntas de color enrasadas y piezas que no se descolocan al montarlas. Las reglas están en [ESTILO.md](ESTILO.md#9-los-edificios-del-kit-f3-16). Los travesaños de las carpinterías se quedan como están: enrasar el cristal quitaría sus puntos, pero también las líneas de los paños de cerca.

## D-037 · Las casas de madera, enteras y por estado

La isba (9 × 8 m) y el barracón (30 × 11 m) tienen las medidas fijas en el plano y casi todos ardieron, así que no se montan por vanos: el kit guarda cada casa entera en cada estado (abandonada, chamuscada, cascarón y quemada) y `KitWhole` escoge la suya por el daño y el incendio de la ficha y la encaja en la huella, por su lado largo y estirada lo poco que haga falta. Una casa entera es una sola llamada de dibujo.

## D-038 · Los hitos y los sitios clave, modelos enteros

Los edificios que no siguen ninguna serie (el vestíbulo del metro, el Edificio Partido, la Casa de los Sóviets…) no se montan con piezas: cada uno es un modelo entero con su receta, hecho en las coordenadas del plano alrededor del «centro» de su ficha, y `KitSingular` lo pone tal cual por su id. Están en el estado que fija el plano, así que no tienen variantes, y llevan dos piezas que no se dibujan: su colisión, hecha a mano y más sencilla que lo que se ve (los escalones y las escaleras, rampas: el jugador no sube escalones), y, si el edificio baja bajo la calle, el hueco del terreno, que el edificio deja en sus metadatos para que quien pone el suelo lo recorte.

## D-039 · Nieve dentro de los edificios abiertos, solo donde entra

Los suelos de un edificio reventado no pueden coger nieve en todas sus caras de arriba, como `nevado`: quedarían blancos hasta el fondo de los pasillos. El material `nevado_parcial` usa la variante del sombreado de los pavimentos (`tinta_transito.gdshader`), que pone la nieve a parches según el alfa del color de vértice: la receta pinta mucha junto al borde roto y las ventanas reventadas y nada al fondo. En las caras de fuera de los antepechos el mismo alfa marca la plaqueta del material `azulejo`.

## D-040 · Desvíos de verdad: la playa de vías se rehace

Las vías que salen de otra lo hacen con un desvío (agujas, corazón, contracarriles y traviesas de madera) de marca 1/9 en la línea y 1/6 en la playa y los apartaderos, y con una curva de enlace hasta su cuerpo; las agujas van en tramos rectos y dos desvíos no se pisan (`tools/ciudad/vias.py` lo comprueba). La playa de vías del plano no se podía construir así: sus diez vías salían de un mismo punto en abanico. Se rehace con un escape en diagonal del que salen las vías una tras otra, como en una playa de verdad; en el mismo sitio y con la misma separación, pero con forma de trapecio y casi todas las vías acabadas en tope. Los apartaderos de la fábrica, el puerto y el carbón cambian de empalme por lo mismo, y las vías de los andenes ahora se unen a la principal por los dos lados. El plano sigue siendo el de la ciudad; lo que cambia es la geometría que no se podía construir.

## D-041 · Nada está intacto: el deterioro, con datos y reglas

Tumansk es una ciudad posapocalíptica: la bomba cayó a unos kilómetros y lleva dos inviernos abandonada. Lo de fuera no puede parecer cuidado (README, «La ambientación de la superficie»). El deterioro no se pinta a mano: lo genera `tools/ciudad/deterioro.py` con datos (los socavones, sobre lo que reventó debajo) y reglas (grietas, baches, tapas, bordillos y matojos, con densidades por clase de superficie y el azar fijo de cada clave), y lo comprueba (los socavones, dentro del pavimento y lejos de edificios, vías, árboles y tuberías). Los socavones son huecos de verdad: el tránsito se corta y una malla propia con la altura de cada vértice baja al fondo, porque la rejilla del relieve (2 m, promediada en sus vértices) no puede tallar un hoyo de 5 m; la colisión del relieve se rebaja bajo ella y el relieve natural ya no lleva el socavón de la avenida (tallado ahí, hacía bajar la calle con él). Los baches y los pozos abiertos van encima de la calle (son poco hondos o pequeños, y cortar la calle por cada uno costaría mucho). Las grietas son tiras a ras de lo que se pisa con la nieve de su clase, para que la nieve las tape donde tapa el pavimento.

## D-042 · Personajes por receta, con el esqueleto humanoide de Godot

Las personas se generan igual que el resto de los modelos (`tools/blender/personaje_bpy.py`): piezas blandas hechas de anillos, con su color y sus pesos de hueso, suavizadas con una subdivisión. Los huesos llevan los nombres del perfil humanoide de Godot (`Hips`, `Spine`, `LeftUpperArm`…): así las animaciones se podrán compartir entre los protagonistas, los clientes y los saqueadores. Es la excepción a la regla de nombrar el contenido en español; los huesos propios de un personaje (`Bufanda1`, `Trenza2`) sí van en español.

## D-043 · Animaciones como funciones, a saltos al reproducirlas

Cada animación es una función del tiempo que devuelve una pose (`tools/blender/personaje_anim.py`). Las piernas se resuelven con cinemática inversa, así que los pies no patinan: basta con reproducir el ciclo a la velocidad a la que anda el personaje. Se guardan suaves; el aspecto de dibujo animado lo pone el juego, que solo avanza la animación 12 veces por segundo (`PlayerAvatar.animation_fps`). La mirada, la bufanda y la trenza van por encima, con suavidad.

## D-044 · Caras dibujadas sobre una cabeza con relieve

El rostro es una lámina 2D de 8 expresiones pegada sobre la cabeza (README 9.3), pero la cabeza no es una bola: tiene cejas, cuencas, pómulos y nariz. Con la luz de arriba, los ojos quedan en sombra y la tinta hace el resto.

## D-045 · El tono de los personajes: nada de juguetes

Revisión de la primera pasada de los protagonistas: eran cabezones, con colorete y ropa limpia, y el mundo no puede ser tan amable. Regla para todas las personas del juego: proporciones reales (unas siete cabezas), caras cansadas y sucias, ropa heredada, remendada y manchada, y equipo que cuente el oficio (mascarilla, gafas, cuerda, palanca). Los personajes se revisan siempre dentro de los dioramas, con la luz de la superficie y la del depósito, nunca sobre un fondo neutro.

## D-046 · Coger cosas: lo pide el jugador, lo mueve el anfitrión

Cada jugador manda sobre su movimiento y su mirada; el anfitrión, sobre la física de los objetos. Quien quiere coger algo se lo pide al anfitrión, que lleva el objeto hacia sus manos con velocidades (no lo teletransporta): así choca con lo que hay por medio y el peso se nota. En los invitados los objetos están congelados y solo siguen la posición replicada.

## D-047 · Los guiones que se lanzan con `-s` no nombran clases del juego

Un guion lanzado con `godot -s` se compila antes de que existan las autocargas. Si nombra una clase que las usa (`Player` usa `Settings`), falla al compilar y, como no llega a llamar a `quit()`, el proceso se queda colgado. Por eso las pruebas de red (`tests/net/`) acceden a los nodos sin tipos; los tests unitarios sí pueden, porque el ejecutor los carga más tarde.

## D-048 · Las manos se colocan con las medidas del objeto

En primera persona, la animación de sujetar deja las manos a una distancia fija, y eso solo vale para un tamaño. `GripModifier` las corrige cada fotograma con la caja que envuelve al objeto y con su posición real: van a sus costados, a algo menos de media altura, y lo que es estrecho y ligero (hasta 14 cm y 1,5 kg: una lata, una botella) se lleva solo con la derecha. La distancia a la que se lleva algo también depende de su tamaño: a partir de 15 cm de medio ancho se aleja, y a partir de 12 cm de medio alto baja, para que una caja grande o el bidón no tapen toda la vista. No hacen falta datos por objeto: sale todo de su malla.

## D-049 · Lo que se lleva va delante del pecho, nunca dentro del cuerpo

Lo que se llevaba iba en un punto fijo respecto a los ojos y colocado por su base: al mirar abajo se metía en el cuerpo (con el bidón, ya a -15°), al girarlo para inspeccionarlo llegaba a la cámara y, como el cuerpo no chocaba con ello, al andar contra una pared el jugador lo atravesaba y la cámara acababa dentro. Reglas:

- Se coloca por su centro, en la vista y por debajo de la mirada, y siempre al menos a 20 cm del eje de los ojos más lo que abulte hacia ellos (el pecho y un hueco). Al inspeccionarlo, lo bastante lejos para que, lo gire como lo gire, no llegue a la cara.
- Cuanto más abajo se mira, más lejos tendría que ir para no tocar el pecho, y las manos (antebrazos que salen de abajo de la vista) no lo pueden seguir más allá de un punto. Por eso, con algo en las manos la mirada no baja más de lo que las manos lo alcanzan: unos 42° con el bidón o la caja grande, 56° con una caja pequeña y 68° con una lata o una botella (sin nada, 82°). Si se coge algo mirando más abajo, la mirada sube sola.
- Al mirar arriba, lo ligero sube con la mirada; lo pesado no pasa de la altura del pecho y sale de la vista por abajo.
- Si hay una pared delante, se acerca al pecho en vez de meterse en ella; cuando ya no cabe, no se puede seguir andando hacia la pared (sí a lo largo). Lo mismo con otro jugador. Las comprobaciones son de solape: un barrido de forma no ve lo que ya toca al empezar.
- Lo que el jugador anda o gira se sigue sin retraso: si no, al andar se quedaba atrás y acababa dentro del cuerpo. El peso se nota al acomodarlo, en lo que frena y en lo bajo que cuelga, y se cae solo si se queda atascado a más de 50 cm de las manos.
- Quien lo lleva lo ve dibujado justo en sus manos: las mallas cuelgan de un nodo `Visual` que se pone en el sitio de las manos mientras el cuerpo físico (que va a 60 pasos por segundo y, en los invitados, llega con el retraso de la red) coincida con alguno de los sitios donde han estado las manos en el último medio segundo. Si no coincide, algo lo para de verdad y se dibuja donde está. La física sigue siendo del anfitrión (D-046).

## D-050 · Las manos agarran puntos de la malla, en los ejes del objeto

Sustituye a D-048 en cómo se ponen las manos; lo de no necesitar datos por objeto se mantiene. Las manos se movían cada fotograma a los lados de la caja que envuelve al objeto vista desde la cámara, con límites de alcance: al mirar casi en vertical, al girar deprisa o con lo que no es una caja (la escoba), quedaban lejos y el objeto flotaba. Ahora, cuando el objeto llega a las manos, `GripModifier` busca con rayos sobre su malla dónde apoyar cada palma y guarda esos puntos en los ejes del objeto, así que las manos van pegadas a él aunque se mueva, gire o se mire desde otro ángulo:

- Con dos manos, en la esquina de delante de cada costado, con los dedos rodeándola: más atrás, la cara de delante las taparía. En lo redondo (el bidón, el cubo) esa esquina ya es la cara de delante, así que el agarre se retrasa hacia el costado.
- Lo que cabe en una mano (hasta 14 cm y 1,5 kg), por el medio, con la derecha y los dedos cerrados alrededor; va un poco a la derecha y se coloca por el agarre, de modo que una escoba sobresale por arriba.
- Lo que se lleva va derecho en el mundo, así que al mirar abajo gira respecto a la cámara y su parte de abajo se esconde. Al cogerlo se buscan varias alturas en cada costado y se usa la más baja que se vea; si las manos quedan en el borde de la vista, agarran más arriba. Si gira tanto que los costados ya no quedan a los lados (al inspeccionarlo), se vuelven a buscar.
- Cada antebrazo se orienta para que la palma mire al objeto, sin doblar la muñeca de más y con el final de la manga fuera de la vista: el modelo solo tiene antebrazos.

## D-051 · Los edificios con modelo propio mandan sobre el plano a su alrededor

El plano les apilaba montones de escombro sobre la huella, por su daño, y los dejaba en la ladera del relieve. Los montones tapaban plantas bajas, entradas y el pórtico; y bajo la Casa de los Sóviets el terreno variaba ±0,9 m, así que asomaba dentro de sus patios y en la planta baja abierta del Edificio Partido. Ahora, los edificios con modelo propio (`MODELO_PROPIO` en `tools/ciudad/datos.py`: los de `KitSingular`) no reciben montones del plano, porque su receta trae su escombro, y se asientan en una explanada a su cota (`EXPLANADAS`): llano bajo la huella entera (con lo que haya en sus patios cerrados) y unos metros alrededor (lo que el modelo sale de ella: el basamento del vestíbulo, el escombro del Partido, el pórtico de los Sóviets), y una transición suave hasta el terreno. El tránsito sale del terreno, así que sigue la explanada. Los demás edificios del kit, cerrados, se quedan en su ladera con un zócalo de piedra hasta el punto más bajo de su huella.

## D-052 · El kit en la maqueta: tres escalones de detalle por edificio

Un bloque del kit son unas sesenta mallas (una MultiMesh por pieza), y cada una se dibuja en la pasada de color y en cada cascada de sombras. Con el relevo solo por sectores (a 450 m), a pie de calle se llegaba a 3.600 llamadas de dibujo, seis veces más que con volúmenes. Ahora cada edificio del kit tiene tres escalones dentro de la versión detallada de su sector:

- A más de 200 m (`kit_distance`), su volumen.
- De 200 a 60 m, su modelo sin sombras. La sombra la proyecta su volumen, metido 40 cm hacia dentro para no quitarle la luz a su propia fachada.
- A menos de 60 m (`kit_shadow_distance`), el modelo entero, con sus sombras.

Las tres versiones miden la distancia desde el mismo punto (el centro del volumen), para que cambien a la vez. Además, lo que va en los huecos de las fachadas (ventanas, puertas, escaparates y los cuartos de detrás) no proyecta sombra nunca: la sombra de un hueco la hace su muro, y en una calle es la mitad de las mallas. Con eso, las calles con edificios del kit se quedan entre 900 y 1.250 llamadas (con volúmenes, entre 400 y 670). Los singulares, de pocas mallas, se dibujan enteros a menos de 200 m.

## D-053 · La calle no es un plano

Con texturas rotas, grietas pintadas y baches encima, la calle seguía viéndose plana y en buen estado: una superficie lisa que sigue la rasante. El deterioro tiene que estar en la geometría. Zonas de firme roto (`tools/ciudad/firmes.py`) cortan la calle y la sustituyen por su base de grava (una malla propia, como los socavones) y placas sueltas que la maqueta levanta como prismas con colisión: se levantan, se hunden, se inclinan y se montan en lomos de presión, más cerca de la Zona Cero. Los bordillos van pieza a pieza (faltan o se han movido). Lo tirado por la calle y las farolas (`tools/ciudad/restos.py`) son instancias de modelos de Blender, las pequeñas solo de cerca. La rasante de toda la calle no se ondula: obligaría a cortar por la rejilla todos los triángulos que hoy se dibujan enteros y doblaría el tránsito para un efecto que apenas se ve; el relieve se concentra donde la calle está rota. El precio, medido: el doble de triángulos en el tránsito (1,3 millones) y el doble de tiempo al levantarlo (unos 9 s).

## D-054 · Lo que se trabaja avanza con el ratón, y el anfitrión lo aplica

Barrer, fregar, atornillar, hacer palanca o coser avanza con el movimiento del ratón mientras se mantiene el botón izquierdo, no con el tiempo: cada herramienta tiene su gesto (pasadas largas, frotar corto, círculos con sentido, tirar hacia abajo, mantener). Lo mide cada jugador en su equipo y lo manda al anfitrión a ratos (cada décima de segundo), que comprueba que es él, que lleva esa herramienta y que alcanza, y lo aplica (`Workable`). Así un invitado trabaja igual que el anfitrión, sin que su ratón tenga que viajar por la red fotograma a fotograma.

## D-055 · El estado de las cosas fijas, en un solo diccionario replicado

Cada cosa fija del local que cambia (cada mancha, telaraña, la persiana, la bombilla, la estufa, el cubo, los papeles…) es un `Fixture` con un identificador, y su estado vive en `DepotWorld`: un diccionario por identificador que cambia el anfitrión, se manda a todos (también a quien llega tarde) y se guarda con la partida. Lo que no se ha tocado no está en el diccionario: cada cosa sabe cómo es el primer día. Los objetos sueltos llevan su estado en `ItemState.extra`, también replicado y guardado.

## D-056 · Los papeles del mundo y de cerca son el mismo papel

Las notas, las fichas de encargo, los recibos, las etiquetas y las páginas del libro de cuentas se describen con un diccionario: el SVG del papel y los rótulos en píxeles del SVG, con su tipografía. `PaperCard` lo pone en el mundo (un rectángulo con el dibujo y el texto encima) y `CloseUp` lo dibuja grande al acercarlo. No hay cajas de texto: todo lo que hay que saber está escrito en algún papel.

## D-057 · Sin sonido en la Fase 2

Por decisión del equipo, el depósito no suena todavía: la respuesta táctil (F2-13) es visual (polvo, papeles que caen y se asientan, agujas con inercia, tapas que se levantan, la lámpara que se balancea, las caras de los clientes). Cuando haya sonido, se colgará de los mismos sitios.

## D-058 · La gente de la estación, con la misma receta que los protagonistas

El relojero, la vendedora, la vecina y el chatarrero salen de la receta de los protagonistas (`tools/blender/recipes/personajes.py`), con el mismo esqueleto y las mismas animaciones, así que `PlayerAvatar` los anima igual: solo cambia la clave del modelo. Lo que los distingue es la ropa (abrigo largo o chaqueta acolchada, gorra de paño, pañuelo atado a la nuca, delantal, falda, botas de fieltro) y la cara: sus láminas (`cara_<nombre>.svg`) tienen más años, con arrugas, patas de gallo, bigote, barba de días o gafas redondas dibujadas. No llevan mochila ni máscara: viven abajo. La bufanda la tiñe el juego, como la de los jugadores.

## D-059 · Cada vehículo es su modelo, a la medida que le da su caja de colisión

Los vehículos que no eran coches eran cajas del color de su tipo. Ahora cada tipo tiene su modelo (`tools/blender/recipes/vehiculos.py`) y, si en el plano hay quemados de ese tipo, otro quemado: la pintura no se puede quemar con un tinte (se pierden los cristales, la goma y la altura sobre las llantas). La maqueta escala cada modelo a lo que mide en el plano dividiendo por el largo de su caja de colisión, no por el de su malla: las pértigas del trolebús, la devanadera del camión de bomberos o el casco bajo el hielo de un barco alargarían la malla y encogerían el vehículo. Lo volcado se tumba en la maqueta (el coche y la barca, boca abajo; lo demás, de costado, con la huella en su sitio) y los barcos llevan el origen en la línea del hielo, con el casco debajo, para escorarse sin despegarse de él. Si falta un modelo, el vehículo vuelve a ser una caja de su medida.

## D-060 · El botín lleva en su ficha lo raro que es y dónde se encuentra

Lo que se puede juntar arriba lleva en su ficha (`ItemData`) lo que cuesta encontrarlo (`rarity`: común, poco común, raro o muy raro) y dónde aparece (`found_in`): los usos de los edificios del plano agrupados en 21 lugares (`ItemData.PLACES`: piso, trastero, garaje, coche, quiosco, tienda, farmacia, hospital, taller, refugio de la defensa civil, puesto militar, laboratorio, iglesia, museo…). Todavía no hay nada que reparta el botín por la ciudad (llegará con las zonas, F3-14 y F6-08); cuando llegue, solo tendrá que leer las fichas. La rareza dice cuántos ejemplares hay y lo lejos de la estación que suelen estar, no lo que valen: eso sigue en `base_value` (un tarro de pepinillos es común y vale poco; las pastillas antirradiación son raras y pesan 30 gramos). Lo que ya había y también se encuentra arriba (las latas, el botiquín, las radios, el dosímetro…) lleva igualmente su rareza y sus lugares; lo que solo se compra o se hace en la estación, no. Lo personal y lo de valor (la foto enmarcada, la medalla, el icono, el samovar, el paquete de correos) no cabía en ninguna categoría: tiene la suya, `OBJETOS`, al final de la lista para no mover las demás, y su cartel en una balda del depósito (la tercera de la última estantería, que repetía Electrónica).

## D-061 · Sin sonido en la Fase 3: el ruido existe para la IA y se ve en ondas de tinta

La superficie tampoco suena todavía (decisión del equipo), pero el sigilo depende del ruido: cada paso, cada puerta y cada cosa que cae tiene un alcance en metros (`NoiseRules`), que la IA oye con lo que tapan el viento y los muros. Para que el jugador sepa cuánto ruido hace sin oírlo, lo que suena se dibuja: unos aros de tinta entrecortados se abren desde donde sonó hasta lo lejos que se oye (`InkRipples`), como las líneas de un ruido en un dibujo animado. Los de los pasos los dibuja cada equipo con lo que ya se replica; los demás los manda el anfitrión. Cuando haya sonido se quedarán como ayuda de accesibilidad (`Settings.sound_ripples`).

## D-062 · El ruido y la visibilidad de un jugador los calcula el anfitrión con lo que ya se replica

Cada jugador manda sobre su movimiento, pero no sobre lo que se oye de él: el anfitrión cuenta las zancadas de cada uno con la posición, la velocidad y la postura replicadas, mira qué pisa (`Ground`: la chapa, los cascotes y los cristales lo dicen en sus metadatos; lo demás es nieve al aire libre y suelo de dentro bajo techo) y le añade el peso de lo que lleva (`Footsteps`, `NoiseRules`). La visibilidad sale de la luz de la hora, la sombra del sol, el techo, la silueta contra el cielo, la postura, el movimiento, el clima y la parte del cuerpo que se ve (`Visibility`). Así un invitado no puede hacerse más silencioso que el anfitrión y la IA solo decide con lo que percibe.

## D-063 · Al cambiar de escena, lo que se deja queda aparcado y los invitados avisan de que han cargado

Subir a la superficie y volver cambia de escena, y la partida tiene un solo guardado. El estado de la escena que se deja (el depósito mientras se está arriba; la superficie mientras se está abajo) queda aparcado en `SaveSystem` (`park_all`), se escribe igual en el archivo y la escena lo recupera al volver (`restore_parked`); lo que se lleva en las manos cambia de escena con su dueño (`Sortie`). Como cada equipo tarda lo suyo en cargar (la ciudad son unos segundos), el anfitrión no hace aparecer jugadores ni objetos hasta que todos los invitados avisan de que tienen la escena (`LevelSync`).

## D-064 · Los perros se mueven por una rejilla sacada del plano, no por la física

Para ir de un sitio a otro, la Jauría usa una rejilla de 1 m sobre el plano de la ciudad (`CityNav`, con el A* de Godot): los edificios, el tambor del vestíbulo, los vehículos, las vallas, los escombros altos y los terraplenes del ferrocarril son obstáculo. Se levanta en unas decenas de milisegundos desde los mismos datos que la maqueta, sin depender de la física ni de hornear una malla de navegación de cientos de miles de triángulos; lo pequeño (troncos, farolas, placas sueltas) lo esquiva el propio cuerpo del perro al moverse. Que un sitio no esté en la rejilla tiene sentido de juego: encima de un coche, dentro de un edificio o en la esclusa, los perros no llegan, y la manada acaba por irse. Cuando haya interiores que se recorran, cada uno será otra capa unida a la calle por sus puertas y sus escaleras.

## D-065 · La manada decide junta y con lo que percibe cada perro

Cada perro tiene sus sentidos y su memoria (`Perception`, `Knowledge`), pero lo que hacen lo decide la manada (`Pack`): la Vieja delante, los demás según el modo (ronda, investigar, rastreo, tanteo, rodeo, persecución, ataque, comer, retirada). Lo que percibe un perro lo sabe la manada; si es una presa que no esperaban, ladra, y los que lo oyen se lo apuntan como un aviso que cita la percepción del que ladró. Así la prueba de justicia vale para la manada entera: cada decisión con sitio sale de algo que percibió alguno de ellos. Las animaciones de los perros, como las de los protagonistas, son ciclos generados por código en Blender (`perro_anim.py`) que Godot reproduce "a saltos"; la cabeza que sigue lo que oye y el hocico al suelo los pone Godot encima (`DogLook`).

## D-066 · La mochila de cada jugador vive en el estado de la partida

La mochila y el cinturón de cada jugador (`Backpack`) se guardan dentro de `GameState`, por el puesto del jugador. Así se guardan con la partida, pasan de una escena a otra sin hacer nada y llegan a todos los equipos con lo demás del estado. Lo que hay dentro son estados de objeto (como los que se guardan del depósito), no objetos del mundo: al guardar algo, el objeto sale del mundo; al sacarlo, vuelve a las manos con su estado. Lo cambia siempre el anfitrión, cuando el dueño lo pide (`PlayerPack`).

## D-067 · En la Fase 3 los objetivos de La Plaza son los edificios menores, que se recorren enteros

Los interiores de las casas grandes (Correos, el Gastronom, el Banco) y el paso subterráneo piden una construcción que no cabe en esta fase: las casas del kit se montan por fachadas, sin plantas por dentro, y el paso subterráneo hay que excavarlo en el relieve y en la red de tránsito de la ciudad. Así que los sitios que se saquean ahora son los menores, que sí se hacen enteros y por dentro: los quioscos de prensa, las tiendas de la evacuación, los trasteros de los patios, el palomar y el centro de transformación (`kit_menores`, `KitMinor`). Cada uno lleva su colisión hecha a mano y deja en sus metadatos dónde van sus puertas, sus escaleras y su botín; la superficie pone las cosas fijas (`SurfaceSites`). El mirador es la azotea del peristilo del vestíbulo, por una escalera de servicio y un ventanal roto, y el refugio, el transformador (puerta de chapa, sin ventanas). Lo demás queda para cuando se puedan recorrer las casas.

## D-068 · Las ganzúas se juegan en el equipo de quien abre; el anfitrión solo comprueba el resultado

Abrir una cerradura es un gesto fino (subir cada pin despacio hasta su punto, con el temblor del miedo), y con el retraso de la red no se podría sentir si cada movimiento del ratón fuera al anfitrión. Así que la vista de la cerradura (`LockpickView`) vive en el equipo de quien abre, con los pines que salen del nombre de la puerta (siempre los mismos), y al acabar le dice al anfitrión si se ha abierto o se ha partido una ganzúa. El anfitrión comprueba que lleva las ganzúas en la mano y que esa puerta se abre con ellas, y es quien cambia el mundo (y gasta las ganzúas). La palanca y la cizalla, que son tirones, sí van como cualquier otro trabajo (`Workable`).

## D-069 · Las cintas del botín, del derecho

`MeshBuilder.ribbon` deja las cintas del revés: la cara de fuera mira hacia dentro, así que lo que se ve es la de dentro, a unos milímetros por debajo, y con sombras la de fuera la deja a oscuras (la faja de papel de las velas salía negra). Las recetas del botín usan `botin_bpy.strap`, que es la misma cinta con las caras vueltas. `ribbon` se queda como está porque cambiarla cambiaría modelos ya revisados (las correas de la máscara, la brújula y los prismáticos, las cintas del cuaderno), donde apenas se nota porque son oscuras; si algún día se arregla, hay que regenerar esos modelos y repasar sus capturas.
