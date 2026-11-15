#!/usr/bin/env bash
# Captura una escena con el render real (Forward+), sin pantalla.
# Usa un servidor X virtual (xvfb) y Vulkan por software si no hay GPU.
#
# Uso: tools/capture.sh res://escena.tscn salida.png [ancho] [alto] [fotogramas]
set -eu
GODOT="${GODOT:-godot}"
SCENE="$1"
OUT="$(realpath -m "$2")"
WIDTH="${3:-1600}"
HEIGHT="${4:-900}"
FRAMES="${5:-30}"
cd "$(dirname "$0")/.."
mkdir -p "$(dirname "$OUT")"
xvfb-run -a -s "-screen 0 ${WIDTH}x${HEIGHT}x24" \
    "$GODOT" --path . --rendering-driver vulkan --audio-driver Dummy \
    --resolution "${WIDTH}x${HEIGHT}" \
    -s tools/capture/capture.gd -- --scene="$SCENE" --out="$OUT" --frames="$FRAMES" ${CAPTURE_ARGS:-} 2>&1 \
    | grep -E "^Captura|ERROR|SCRIPT ERROR|No se pudo" || true
test -f "$OUT" || ls "$(dirname "$OUT")" | grep -q "$(basename "${OUT%.png}")"
