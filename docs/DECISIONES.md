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
