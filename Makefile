# Órdenes de desarrollo de Tumansk. `make` sin argumentos muestra la ayuda.
GODOT ?= godot
PYTHON ?= python3
GD_DIRS := scripts tests tools/godot tools/capture

.PHONY: help setup assets textures svg models import test test-net lint format capture video ciudad ciudad-comprobar

help: ## muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## escribe en project.godot los controles, las capas y los buses de audio
	$(GODOT) --headless --path . -s tools/godot/setup_project.gd

assets: textures svg models ## genera todas las texturas, ilustraciones y modelos

textures: ## texturas del estilo (papel, tramado, rampas, ruido)
	$(PYTHON) tools/textures/generate_textures.py

svg: ## ilustraciones 2D con aspecto dibujado (rough.js)
	cd tools/svg && npm ci --silent && node generate.mjs

models: ## modelos 3D a partir de las recetas (Blender como módulo de Python)
	$(PYTHON) tools/blender/build_assets.py

ciudad: ## plano de la ciudad: datos (data/ciudad) y planos de desarrollo (docs/ciudad)
	$(PYTHON) tools/ciudad/plano.py

ciudad-comprobar: ## valida el plano de la ciudad (sin dibujar)
	$(PYTHON) tools/ciudad/plano.py --comprobar

import: ## importa los recursos en Godot
	$(GODOT) --headless --path . --import

test: import ## tests unitarios
	$(GODOT) --headless --path . -s tests/run_tests.gd

test-net: import ## prueba de red con dos instancias (anfitrión e invitado)
	GODOT=$(GODOT) tools/test_net.sh

lint: ## revisa el estilo del código GDScript
	gdlint $(GD_DIRS)
	gdformat --check $(GD_DIRS)

format: ## formatea el código GDScript
	gdformat $(GD_DIRS)

capture: import ## capturas de las escenas de revisión (en capturas/, sin versionar)
	tools/capture.sh res://scenes/debug/hola_tumansk.tscn capturas/hola_tumansk.png
	tools/capture.sh res://scenes/style/diorama_deposito_limpio.tscn capturas/deposito_limpio.png
	tools/capture.sh res://scenes/style/diorama_deposito_abandonado.tscn capturas/deposito_abandonado.png
	tools/capture.sh res://scenes/style/diorama_patio_dia.tscn capturas/patio_dia.png
	tools/capture.sh res://scenes/style/diorama_patio_anochecer.tscn capturas/patio_anochecer.png
	tools/capture.sh res://scenes/style/diorama_patio_noche.tscn capturas/patio_noche.png
	tools/capture.sh res://scenes/style/diorama_patio_ventisca.tscn capturas/patio_ventisca.png
	tools/capture.sh res://scenes/ui/prueba_interfaz.tscn capturas/interfaz.png
	tools/capture.sh res://scenes/ui/prueba_tipografia.tscn capturas/tipografias.png

video: import ## vídeo de los dioramas (capturas/dioramas.mp4)
	tools/video.sh capturas/dioramas.mp4
