# Convenciones

## Idioma

| Qué | Idioma |
|---|---|
| Identificadores de código (clases, funciones, variables, señales, acciones de control) | Inglés, como la API de Godot |
| Comentarios, documentación y mensajes de commit | Español |
| Textos del juego | Español (solo español) |
| Nombres de contenido (modelos, texturas, datos, nodos de escena) | Español, `snake_case` sin tildes |

## GDScript

- **Tipado estático en todo**: variables, parámetros, retornos y bucles (`for item: Item in items`).
- `gdformat` da el formato y `gdlint` revisa nombres y orden (`make lint`). La configuración está en `gdlintrc`.
- Orden dentro de un script: `@tool`, `class_name`, `extends`, comentario `##`, señales, enums, constantes, variables exportadas, públicas, privadas (`_`), `@onready` y, después, las funciones.
- `class_name` solo para clases que se reutilizan. Los tests extienden por ruta (`extends "res://tests/test_case.gd"`).
- Comentarios de documentación con `##`: explican el porqué, no repiten el código.
- Archivos en `snake_case`. Una escena y su script se llaman igual.

## Red

- El anfitrión manda sobre el mundo. Antes de cambiar el mundo: `if not NetSession.is_authority(): return`.
- Todo lo que se mueve y deben ver todos lleva un `TransformSync` (o un `MultiplayerSynchronizer` propio).
- Cada sistema nuevo se prueba también con dos instancias (`make test-net` o una prueba propia).

## Assets

- Lo de `assets/models/`, `assets/textures/` y `assets/ui/` se genera: se editan las recetas y los generadores, nunca los archivos resultantes.
- Sufijos de las recetas: `-fisico`, `-estatico`, `-colcaja`, `-colconvexa` (ver `docs/DESARROLLO.md`).
- Todo generador es determinista: semillas fijas.

## Commits y ramas

- Mensajes en español y en imperativo: "Añade…", "Corrige…", "Ajusta…".
- Si el cambio corresponde a tareas de la Hoja de Desarrollo, se citan sus IDs (por ejemplo, `F1-02`).
- Cada pull request sigue la plantilla y lleva capturas si cambia algo visual.
