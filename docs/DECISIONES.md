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

## D-020 · Personajes por receta, con el esqueleto humanoide de Godot

Las personas se generan igual que el resto de los modelos (`tools/blender/personaje_bpy.py`): piezas blandas hechas de anillos, con su color y sus pesos de hueso, suavizadas con una subdivisión. Los huesos llevan los nombres del perfil humanoide de Godot (`Hips`, `Spine`, `LeftUpperArm`…): así las animaciones se podrán compartir entre los protagonistas, los clientes y los saqueadores. Es la excepción a la regla de nombrar el contenido en español; los huesos propios de un personaje (`Bufanda1`, `Trenza2`) sí van en español.

## D-021 · Animaciones como funciones, a saltos al reproducirlas

Cada animación es una función del tiempo que devuelve una pose (`tools/blender/personaje_anim.py`). Las piernas se resuelven con cinemática inversa, así que los pies no patinan: basta con reproducir el ciclo a la velocidad a la que anda el personaje. Se guardan suaves; el aspecto de dibujo animado lo pone el juego, que solo avanza la animación 12 veces por segundo (`PlayerAvatar.animation_fps`). La mirada, la bufanda y la trenza van por encima, con suavidad.

## D-022 · Caras dibujadas sobre una cabeza con relieve

El rostro es una lámina 2D de 8 expresiones pegada sobre la cabeza (README 9.3), pero la cabeza no es una bola: tiene cejas, cuencas, pómulos y nariz. Con la luz de arriba, los ojos quedan en sombra y la tinta hace el resto.

## D-023 · El tono de los personajes: nada de juguetes

Revisión de la primera pasada de los protagonistas: eran cabezones, con colorete y ropa limpia, y el mundo no puede ser tan amable. Regla para todas las personas del juego: proporciones reales (unas siete cabezas), caras cansadas y sucias, ropa heredada, remendada y manchada, y equipo que cuente el oficio (mascarilla, gafas, cuerda, palanca). Los personajes se revisan siempre dentro de los dioramas, con la luz de la superficie y la del depósito, nunca sobre un fondo neutro.

## D-024 · Coger cosas: lo pide el jugador, lo mueve el anfitrión

Cada jugador manda sobre su movimiento y su mirada; el anfitrión, sobre la física de los objetos. Quien quiere coger algo se lo pide al anfitrión, que lleva el objeto hacia sus manos con velocidades (no lo teletransporta): así choca con lo que hay por medio y el peso se nota. En los invitados los objetos están congelados y solo siguen la posición replicada.

## D-025 · Los guiones que se lanzan con `-s` no nombran clases del juego

Un guion lanzado con `godot -s` se compila antes de que existan las autocargas. Si nombra una clase que las usa (`Player` usa `Settings`), falla al compilar y, como no llega a llamar a `quit()`, el proceso se queda colgado. Por eso las pruebas de red (`tests/net/`) acceden a los nodos sin tipos; los tests unitarios sí pueden, porque el ejecutor los carga más tarde.
