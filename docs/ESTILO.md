# Guía de estilo: ilustración entintada

Estado: **primera pasada de la Fase 1**, pendiente de tu aprobación. Los valores de esta guía son los que usan ahora mismo los shaders y `StyleDirector`.

![Depósito limpio](capturas/fase1_deposito_limpio.jpg)

## 1. Cómo se construye la imagen

| Capa | Dónde está | Qué hace |
|---|---|---|
| Color base | Recetas de Blender (`tools/blender/`) | Cada pieza lleva su color pintado en los vértices, con oclusión, cavidades y manchas (óxido, humedad, suciedad) |
| Sombreado por bandas | `assets/shaders/tinta.gdshaderinc` | Tres bandas (sombra, medio tono, luz) según el ángulo con la luz. La banda de sombra vale 0: ahí solo llega la luz ambiente, así que las sombras propias y las proyectadas tienen el mismo color |
| Caída de la luz | Mismo shader | La distancia y las sombras proyectadas se aplican suaves, encima de las bandas |
| Nieve | Mismo shader (`snow_amount`) | Blanquea lo que mira hacia arriba, con ruido para que no sea uniforme |
| Post-proceso | `assets/shaders/post_tinta.gdshader` | Gradación, tramado, relleno de tinta, contorno, trazo vivo, papel, grano y viñeta |
| Estado del dibujo | `scripts/core/style_director.gd` | Mezcla el preajuste de la zona con el miedo y la radiación y lo publica en los parámetros globales `tinta_*` |

El post-proceso es un rectángulo que cubre la pantalla (`scenes/style/ink_post.tscn`). Se dibuja antes que los objetos transparentes, así que las partículas (nieve, polvo) y las telarañas quedan limpias encima del dibujo.

## 2. Preajustes por zona

| Parámetro (`tinta_*`) | Depósito | Superficie | Qué controla |
|---|---|---|---|
| `trazo_fps` | 4 | 8 | Cuántas veces por segundo se "redibuja" el contorno |
| `trazo_amplitud` | 0,6 px | 1,0 px | Cuánto tiembla el contorno |
| `grosor` | 1,6 px | 2,2 px | Grosor del contorno a 1080p |
| `tramado` | 0,5 | 0,8 | Fuerza de las rayas de lápiz |
| `tramado_umbral` | 0,07 | 0,20 | Luminancia por debajo de la cual empieza el tramado |
| `relleno` | 0,003 | 0,02 | Luminancia por debajo de la cual todo es tinta |
| `saturacion` | 1,0 | 0,55 | Saturación del color |
| `contraste` | 1,05 | 1,12 | Contraste alrededor del gris medio |
| `papel` | 0,3 | 0,4 | Cuánto se nota el grano del papel |
| `grano` | 0,025 | 0,05 | Grano de película |
| `vineta` | 0,3 | 0,45 | Oscurecimiento de los bordes |
| `rampa` | 1 | 2 | Fila de `rampas.png` |
| `tinte` | `#FFF7EB` | `#EDF7FF` | Tinte de la imagen (cálido o frío) |

**Miedo** (`StyleDirector.fear`, de 0 a 1): el trazo tiembla hasta 3,5 veces más y más deprisa, el contorno engorda hasta 1,5 px, el color pierde saturación y el tramado invade la imagen desde los bordes. **Radiación** (`StyleDirector.radiation`): el grano crece. Con la opción de accesibilidad "trazo vivo reducido", el temblor baja al 30 % y no pasa de 4 fps.

## 3. Paletas

**Depósito: "Ámbar y madera"**

| Uso | Hex |
|---|---|
| Tinta | `#1B1A22` |
| Azulejo de metro | `#2F6F73` (franja crema `#D3C8AC`) |
| Yeso | `#CDBF9F`, manchas `#9C8F72` |
| Suelo | `#8E857A` y `#7C746A`, mortero `#3B3631` |
| Madera | `#8A5A3B`, oscura `#6E4A32` |
| Cartón | `#A8794E`, cinta `#D8B26A` |
| Metal de estanterías | `#55615A`, óxido `#8E4A2F` |
| Luz de la bombilla | `#FFCC8F` |

**Superficie: "Ceniza y óxido"**

| Uso | Hex |
|---|---|
| Nieve | `#D4D1C9`, pisada `#9C9890` |
| Paneles de hormigón | `#8E8B83`, oscuros `#716E67` |
| Cristal | `#262A30` |
| Balcones (pintados por los vecinos) | `#7C93A0`, `#8FA08A`, `#B3A58A`, `#9A7F7A` |
| Corteza | `#3B3430` |
| Cielo nublado | `#A3ADB3`; al anochecer `#42474F` |

Regla: el rojo (`#C8323C`) se reserva para lo importante.

## 4. Reglas de modelado (recetas)

- **Biseles** de 3 a 20 mm según el tamaño. Las piezas sin bisel se sombrean planas.
- **Imperfección** siempre con semilla: `wobble` (ondulación de 2 a 6 mm en objetos, hasta 22 cm en montones de nieve), `dent` (abolladuras), `apply_bulge` (cartón hinchado), giros de 0,5 a 2° en baldosas y tablones.
- **Variación de color** por pieza de un 4 a un 10 % (`jitter`), más manchas (`stain`). Con `stretch_z` < 1 las manchas se alargan en vertical, como chorretones bajo los balcones.
- **Pintura** (`paint`): oclusión de 8 a 32 muestras según el tamaño, cavidades oscuras y aristas algo más claras.
- **Nombres de material**: `metal` (rampa de metal), `vidrio`, `bombilla` (emite luz) y `nevado` (nieve). El resto usa el material base.

## 5. Herramientas de revisión

- `tools/capture.sh escena salida.png [ancho] [alto] [fotogramas]` hace una captura por cada cámara del grupo `capture_camera`.
- `CAPTURE_ARGS="--hide=InkPost"` captura sin post-proceso.
- `CAPTURE_ARGS="--post=debug_view=N"` muestra una capa del post-proceso: 1 profundidad, 2 normales, 3 contorno, 4 tramado, 5 color de entrada, 6 relleno.
- Escenas de revisión en `scenes/style/`: `diorama_deposito_limpio`, `diorama_deposito_abandonado`, `diorama_patio_dia`, `diorama_patio_anochecer` y `prueba_estilo`.

## 6. Pendiente en la Fase 1

- Contorno por casco invertido para personajes y criaturas (F1-03).
- Huellas en la nieve y ventisca (F1-07).
- Panel de depuración dentro del juego para mover miedo, hora y zona (F1-11).
- Piezas de interfaz en el estilo final y tipografías (F1-12, F1-13).
- Vídeo corto de los dioramas (F1-14).
- Ajustes que salgan de tu revisión de las capturas.
