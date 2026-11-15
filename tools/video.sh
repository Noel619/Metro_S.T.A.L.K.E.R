#!/usr/bin/env bash
# Graba el vídeo de los dioramas (F1-14) con el modo película de Godot y lo
# convierte a MP4 con ffmpeg. Igual que las capturas: servidor X virtual y, si
# no hay GPU, Vulkan por software (lento, pero el resultado es el real).
#
# Uso: tools/video.sh salida.mp4 [ancho] [alto] [fotogramas_por_segundo]
set -eu
GODOT="${GODOT:-godot}"
OUT="$(realpath -m "$1")"
WIDTH="${2:-1280}"
HEIGHT="${3:-720}"
FPS="${4:-12}"
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
xvfb-run -a -s "-screen 0 ${WIDTH}x${HEIGHT}x24" \
    "$GODOT" --path . --rendering-driver vulkan --audio-driver Dummy \
    --resolution "${WIDTH}x${HEIGHT}" --fixed-fps "$FPS" \
    --write-movie "$TMP/video.avi" res://scenes/debug/video_dioramas.tscn 2>&1 \
    | grep -E "ERROR|SCRIPT ERROR" || true
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -loglevel error -i "$TMP/video.avi" -c:v libx264 -preset veryslow -crf 30 \
    -pix_fmt yuv420p -movflags +faststart "$OUT"
echo "Vídeo: $OUT ($(du -h "$OUT" | cut -f1))"
