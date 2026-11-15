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
