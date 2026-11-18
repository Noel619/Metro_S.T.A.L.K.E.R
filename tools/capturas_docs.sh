#!/usr/bin/env bash
# Rehace las capturas de la documentación (docs/capturas/*.jpg) a 1600×900.
# Cada escena se captura con todas sus cámaras; aquí se eligen las que pasan a
# la documentación y con qué nombre. Necesita Pillow (para el JPG).
#
# Uso: tools/capturas_docs.sh [filtro]
#   filtro: solo los grupos cuyo nombre lo contenga (deposito, consigna, equipo, patio,
#   interfaz, maqueta, kit, singulares).
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
if want consigna; then
    # El depósito jugable (Fase 2): el primer día y el local abierto, con el relojero.
    capture debug/revision_deposito primer "--sin-ayuda" 40
    keep primer_camara_sala fase2_consigna_primer_dia
    keep primer_camara_mostrador fase2_consigna_persiana_atascada
    keep primer_camara_telarana fase2_consigna_telarana
    keep primer_camara_dormir fase2_consigna_dormir
    capture debug/revision_deposito abierto "--sin-ayuda --abierto" 50
    keep abierto_camara_mostrador fase2_consigna_mostrador
    keep abierto_camara_cliente fase2_consigna_cliente
    keep abierto_camara_banco fase2_consigna_banco
    keep abierto_camara_encargos fase2_consigna_encargos
    keep abierto_camara_ventanilla fase2_estacion_ventanilla
    keep abierto_camara_puesto fase2_estacion_puesto
    keep abierto_camara_pasillo fase2_estacion_pasillo
    keep abierto_camara_arcos fase2_estacion_arcos
    keep abierto_camara_escaleras fase2_estacion_escaleras
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
    keep maqueta_vista_desvio fase3_transito_desvio
    keep maqueta_vista_topes fase3_transito_topes
    keep maqueta_vista_socavon fase3_deterioro_socavon
    keep maqueta_vista_socavon_galeria fase3_deterioro_galeria
    keep maqueta_vista_socavon_agua fase3_deterioro_agua
    keep maqueta_vista_vestibulo fase3_maqueta_vestibulo
    keep maqueta_vista_soviets fase3_maqueta_soviets
    keep maqueta_vista_calle_rota fase3_deterioro_calle_rota
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
if want kit; then
    # El kit de arquitectura (F3-16): los edificios no tienen nada que asentar.
    capture style/diorama_edificios edificios "" 10
    keep edificios_camara_jrushchovka fase3_kit_jrushchovka
    keep edificios_camara_portal fase3_kit_portal
    keep edificios_camara_bloque fase3_kit_bloque
    keep edificios_camara_danos fase3_kit_danos
    keep edificios_camara_munones fase3_kit_munones
    keep edificios_camara_mercader fase3_kit_mercader
    keep edificios_camara_pinon fase3_kit_isba
    keep edificios_camara_isbas fase3_kit_isbas
    keep edificios_camara_barracon fase3_kit_barracon
    capture style/diorama_plaza plaza "--call=DioramaPlaza:capture_only:banco,fachada" 10
    keep plaza_camara_banco fase3_kit_estalinka
    keep plaza_camara_fachada fase3_kit_estalinka_fachada
    capture style/diorama_mercaderes mercaderes "--call=DioramaMercaderes:capture_only:calle" 10
    keep mercaderes fase3_kit_mercaderes
    capture style/diorama_edificios anochecer \
        "--call=DioramaEdificios:set_hour:18.6 --call=DioramaEdificios:capture_only:mercader" 10
    keep anochecer fase3_kit_anochecer
    capture style/diorama_edificios noche \
        "--call=DioramaEdificios:set_hour:23 --call=DioramaEdificios:capture_only:portal,pinon --call=DioramaEdificios:set_flashlight:1" 10
    keep noche_camara_portal fase3_kit_noche
    keep noche_camara_pinon fase3_kit_noche_isba
fi
if want singulares; then
    # Los edificios singulares (F3-16): el vestíbulo del metro, el Edificio Partido y la
    # Casa de los Sóviets.
    capture style/diorama_vestibulo vestibulo "--call=DioramaVestibulo:capture_only:avenida,cupula" 10
    keep vestibulo_camara_avenida fase3_singular_vestibulo
    keep vestibulo_camara_cupula fase3_singular_vestibulo_cupula
    capture style/diorama_vestibulo esclusa \
        "--call=DioramaVestibulo:capture_only:compuerta --call=DioramaVestibulo:set_flashlight:1" 10
    keep esclusa fase3_singular_vestibulo_compuerta
    capture style/diorama_partido partido "--call=DioramaPartido:capture_only:crater,casa" 10
    keep partido_camara_crater fase3_singular_partido
    keep partido_camara_casa fase3_singular_partido_casa
    capture style/diorama_soviets soviets "--call=DioramaSoviets:capture_only:avenida,escombro,cuarto" 10
    keep soviets_camara_avenida fase3_singular_soviets
    keep soviets_camara_escombro fase3_singular_soviets_escombro
    keep soviets_camara_cuarto fase3_singular_soviets_cuarto
fi
