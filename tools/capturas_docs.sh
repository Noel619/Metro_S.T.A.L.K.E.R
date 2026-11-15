#!/usr/bin/env bash
# Rehace las capturas de la documentación (docs/capturas/fase1_*.jpg) a 1600×900.
# Cada escena se captura con todas sus cámaras; aquí se eligen las que pasan a
# la documentación y con qué nombre. Necesita Pillow (para el JPG).
#
# Uso: tools/capturas_docs.sh [filtro]
#   filtro: solo los grupos cuyo nombre lo contenga (deposito, equipo, patio, interfaz).
set -eu
cd "$(dirname "$0")/.."
FILTER="${1:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

want() { [ -z "$FILTER" ] || [[ "$1" == *"$FILTER"* ]]; }

# capture escena nombre [CAPTURE_ARGS]
capture() {
    CAPTURE_ARGS="${3:-}" tools/capture.sh "res://scenes/$1.tscn" "$TMP/$2.png" 1600 900 | grep -v "^Captura" || true
}

# keep captura nombre_en_docs
keep() {
    python3 - "$TMP/$1.png" "docs/capturas/$2.jpg" <<'EOF'
import sys
from PIL import Image
Image.open(sys.argv[1]).convert("RGB").save(sys.argv[2], quality=90, optimize=True)
print(f"  {sys.argv[2]}")
EOF
}

if want deposito; then
    capture style/diorama_deposito_limpio limpio
    keep limpio_camara_fondo fase1_deposito_limpio
    keep limpio_camara_persiana fase1_deposito_limpio_persiana
    keep limpio_camara_banco fase1_deposito_limpio_banco
    keep limpio_camara_rincon fase1_deposito_limpio_rincon
    keep limpio_camara_pasillo fase1_deposito_limpio_pasillo
    capture style/diorama_deposito_abandonado abandonado
    keep abandonado_camara_fondo fase1_deposito_abandonado
    keep abandonado_camara_persiana fase1_deposito_abandonado_persiana
fi
if want equipo; then
    capture style/diorama_equipo equipo
    keep equipo_camara_mesa fase1_equipo
    keep equipo_camara_detalle fase1_equipo_detalle
fi
if want patio; then
    capture style/diorama_patio_dia dia
    keep dia_camara_patio fase1_patio_dia
    keep dia_camara_banco fase1_patio_dia_banco
    keep dia_camara_horizonte fase1_patio_dia_horizonte
    keep dia_camara_huellas fase1_patio_dia_huellas
    keep dia_camara_quiosco fase1_patio_dia_quiosco
    capture style/diorama_patio_anochecer anochecer
    keep anochecer_camara_patio fase1_patio_anochecer
    keep anochecer_camara_banco fase1_patio_anochecer_banco
    capture style/diorama_patio_noche noche
    keep noche_camara_patio fase1_patio_noche
    capture style/diorama_patio_noche_linterna linterna
    keep linterna_camara_banco fase1_patio_noche_linterna
    keep linterna_camara_patio fase1_patio_noche_linterna_patio
    capture style/diorama_patio_ventisca ventisca
    keep ventisca_camara_patio fase1_patio_ventisca
    keep ventisca_camara_banco fase1_patio_ventisca_banco
    capture style/visor_estilo panel \
        "--call=VisorEstilo:_load:3 --call=DioramaPatio:set_hour:18.75 --call=PanelDepuracion:toggle"
    keep panel_camara_patio fase1_panel_depuracion
fi
if want interfaz; then
    capture ui/prueba_interfaz interfaz
    keep interfaz fase1_interfaz
    capture ui/prueba_tipografia tipografias
    keep tipografias fase1_tipografias
fi
