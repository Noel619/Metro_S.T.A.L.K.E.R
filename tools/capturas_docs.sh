#!/usr/bin/env bash
# Rehace las capturas de la documentación (docs/capturas/*.jpg) a 1600×900.
# Cada escena se captura con todas sus cámaras; aquí se eligen las que pasan a
# la documentación y con qué nombre. Necesita Pillow (para el JPG).
#
# Uso: tools/capturas_docs.sh [filtro]
#   filtro: solo los grupos cuyo nombre lo contenga (deposito, equipo, patio, interfaz,
#   maqueta).
set -eu
cd "$(dirname "$0")/.."
FILTER="${1:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

want() { [ -z "$FILTER" ] || [[ "$1" == *"$FILTER"* ]]; }

# capture escena nombre [CAPTURE_ARGS] [fotogramas]
capture() {
    CAPTURE_ARGS="${3:-}" tools/capture.sh "res://scenes/$1.tscn" "$TMP/$2.png" 1600 900 "${4:-30}" \
        | grep -v "^Captura" || true
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
if want maqueta; then
    # La maqueta no tiene partículas ni nada que asentar: con 10 fotogramas basta.
    capture debug/maqueta_ciudad maqueta "" 10
    keep maqueta_vista_aerea fase3_maqueta_aerea
    keep maqueta_vista_rutas fase3_maqueta_rutas
    keep maqueta_vista_salida fase3_maqueta_salida
    keep maqueta_vista_avenida fase3_maqueta_avenida
    keep maqueta_vista_bloques fase3_maqueta_bloques
    keep maqueta_vista_rio fase3_maqueta_rio
    keep maqueta_vista_puente fase3_maqueta_puente
    keep maqueta_vista_centro fase3_maqueta_centro
    keep maqueta_vista_industria fase3_maqueta_industria
    keep maqueta_vista_zona_cero fase3_maqueta_zona_cero
    keep maqueta_vista_escalinata fase3_transito_escalinata
    keep maqueta_vista_esquina fase3_transito_esquina
    keep maqueta_vista_vano fase3_transito_vano
    keep maqueta_vista_loma fase3_transito_loma
    keep maqueta_vista_estacion fase3_transito_estacion
    keep maqueta_vista_playa fase3_transito_playa
    keep maqueta_vista_paso_nivel fase3_transito_paso_nivel
    keep maqueta_vista_tranvia fase3_transito_tranvia
    capture debug/maqueta_ciudad ciegos \
        "--call=MaquetaCiudad:survey_landmarks --call=MaquetaCiudad:capture_only:aerea" 10
    keep ciegos fase3_maqueta_hitos
    capture debug/maqueta_ciudad anochecer \
        "--call=MaquetaCiudad:set_hour:18.6 --call=MaquetaCiudad:capture_only:avenida" 10
    keep anochecer fase3_maqueta_avenida_anochecer
    capture debug/maqueta_ciudad noche \
        "--call=MaquetaCiudad:set_hour:23 --call=MaquetaCiudad:set_flashlight:1 --call=MaquetaCiudad:capture_only:salida" 10
    keep noche fase3_maqueta_salida_noche
    capture debug/maqueta_ciudad panel \
        "--call=MaquetaCiudad:go_to_view:1 --call=MaquetaCiudad:show_layers:hitos --call=MaquetaCiudad:capture_walker" 20
    keep panel fase3_maqueta_panel
fi
