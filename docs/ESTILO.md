# Guía de estilo: ilustración entintada

Estado: **segunda pasada de la Fase 1**, pendiente de tu aprobación. Los valores de esta guía son los que usan ahora mismo los shaders, `StyleDirector` y `Atmosphere`.

**Revisión 1** (tu respuesta): contorno y tramado, bien; el depósito cálido, muy bien; el exterior estaba demasiado blanco y pálido, sin ambiente posapocalíptico, y el cielo no podía ser negro. La segunda pasada cambia el exterior (secciones 2, 3, 5 y 6).

**Revisión 2**: el exterior transmite la sensación; hay que mantener ese nivel en toda la ciudad. La noche, mucho más oscura (sin linterna casi no se ve). El anochecer, bien, con un ligero retoque: ahora es algo más marrón y menos saturado.

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

| Parámetro (`tinta_*`) | Depósito | Superficie | Superficie de noche | Qué controla |
|---|---|---|---|---|
| `trazo_fps` | 4 | 8 | 8 | Cuántas veces por segundo se "redibuja" el contorno |
| `trazo_amplitud` | 0,6 px | 1,0 px | 1,0 px | Cuánto tiembla el contorno |
| `grosor` | 1,6 px | 2,2 px | 2,2 px | Grosor del contorno a 1080p |
| `tramado` | 0,5 | 0,85 | 0,75 | Fuerza de las rayas de lápiz |
| `tramado_umbral` | 0,07 | 0,30 | 0,10 | Luminancia por debajo de la cual empieza el tramado |
| `relleno` | 0,003 | 0,018 | 0,002 | Luminancia por debajo de la cual todo es tinta |
| `saturacion` | 1,0 | 0,62 | 0,7 | Saturación del color |
| `contraste` | 1,05 | 1,18 | 1,1 | Contraste alrededor del gris medio |
| `papel` | 0,3 | 0,4 | 0,35 | Cuánto se nota el grano del papel |
| `grano` | 0,025 | 0,06 | 0,07 | Grano de película |
| `vineta` | 0,3 | 0,5 | 0,45 | Oscurecimiento de los bordes |
| `rampa` | 1 | 2 | 2 | Fila de `rampas.png` |
| `tinte` | `#FFF7EB` | `#F7F2E6` | `#E6F2FF` | Tinte de la imagen |
| `negro` | 0 | 0 | 1 | Cuánto se oscurece el relleno de tinta; con 1 casi negro, y los contornos desaparecen donde no llega la luz |

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

**Superficie: "Ceniza y óxido"** (más sucia y oscura desde la revisión 1)

| Uso | Hex |
|---|---|
| Nieve vieja | `#B3AEA2`, con barro `#7A7266` y hollín `#1E1B19` |
| Paneles de hormigón | `#7E7A72`, oscuros `#625E58` |
| Cristal | `#1F2228`; quemado `#0D0C0E` |
| Balcones (pintados por los vecinos, ya desvaídos) | `#6A7F8B`, `#7D8C78`, `#9A8F78`, `#86706B` |
| Óxido | `#7E4128` |
| Corteza | `#34302C` |

**Cielo** (`scripts/surface/atmosphere.gd`). Nunca es negro del todo, pero la noche es muy oscura: sin linterna solo se distinguen el cielo y las siluetas (revisión 2).

| Momento | Cénit | Horizonte | Nubes (claro / oscuro) | Luz |
|---|---|---|---|---|
| Día | `#6E7273` | `#9A968C` | `#AEABA2` / `#6A6967` | Sol velado `#F2E6CC` |
| Anochecer | `#2E3040` | `#B47A55` | `#C58560` / `#3E3541` | Sol bajo `#FFA06A` |
| Noche | `#0A0D14` | `#161B25` | `#2A3142` / `#0E1118` | Luna muy débil `#7D8DB5` |

Regla: el rojo (`#C8323C`) se reserva para lo importante.

### La noche y la linterna

De noche la luz ambiente y la de la luna son casi nulas (`tinta_negro` = 1): el relleno de tinta es casi negro y los contornos solo se dibujan donde llega algo de luz. La linterna (`scripts/surface/flashlight.gd`) es un foco de luz cálida que sale de la mano: dentro de su cono vuelven el color, el tramado y la tinta. Los copos de nieve reciben la luz de la escena, así que de noche solo se ven dentro del cono.

## 4. Reglas de modelado (recetas)

- **Biseles** de 3 a 20 mm según el tamaño. Las piezas sin bisel se sombrean planas.
- **Imperfección** siempre con semilla: `wobble` (ondulación de 2 a 6 mm en objetos, hasta 22 cm en montones de nieve), `dent` (abolladuras), `apply_bulge` (cartón hinchado), giros de 0,5 a 2° en baldosas y tablones.
- **Variación de color** por pieza de un 4 a un 10 % (`jitter`), más manchas (`stain`). Con `stretch_z` < 1 las manchas se alargan en vertical, como chorretones bajo los balcones.
- **Pintura** (`paint`): oclusión de 8 a 32 muestras según el tamaño, cavidades oscuras y aristas algo más claras.
- **Destrucción** (superficie): hollín de incendio sobre las ventanas quemadas (`scorch`), paneles caídos con el hueco oscuro y varillas, balcones desplomados que cuelgan de la bisagra, cornisas rotas, escombros al pie de la fachada y puertas tapiadas con tablones.
- **Nombres de material**: `metal` (rampa de metal), `vidrio`, `bombilla` (emite luz), `nevado` (nieve vieja) y `lejano_*` (siluetas del horizonte). El resto usa el material base.

## 4b. Personas

![Los protagonistas en el patio](capturas/fase2_personajes_superficie.jpg)

- **Tono** ([D-023](DECISIONES.md)): nada de juguetes. Unas siete cabezas de alto, flacos, cargados de hombros; caras cansadas y sucias; ropa heredada, remendada, manchada de grasa y con barro de rodillas abajo.
- **Cara**: lámina 2D de 8 expresiones (`assets/ui/cara_*.svg`) sobre una cabeza con relieve. Ojos pequeños con el párpado pesado, ojeras, rayas de lápiz bajo el pómulo, la boca apretada. Sin colorete ni brillos.
- **Contorno**: además del contorno del post-proceso, las personas llevan un casco invertido (`assets/shaders/casco.gdshader`, segunda pasada de los materiales `ropa`, `piel` y `prenda_jugador`). Su grosor sigue al de la zona y al miedo, y varía a saltos.
- **Movimiento a saltos**: 12 fotogramas por segundo.
- **Color del jugador**: la bufanda (y el trapo de la trenza) se tiñen con el color de cada jugador, siempre apagado: ocre `#9A7A2E`, petróleo `#2C6468`, óxido `#7A4A30` y azul pizarra `#42558A`. No hay jugador rojo.

| Uso | Hex |
|---|---|
| Piel | `#C9A58B`, enrojecida por el frío `#B5766A`, sucia `#7C6455` |
| Chaqueta acolchada del chico | `#676650`, oscura `#525240` |
| Capote de la chica | `#5B5A54`, oscuro `#494842` |
| Lona | `#6B634C`, `#555D47` (zurrón) |
| Cuero | `#3E2C21`, gastado `#5F4532` |
| Goma, cinta aislante | `#222224`, `#1F2733` |
| Cuerda | `#85765A` |
| Mugre, polvo, barro | `#26221E`, `#8B8576`, `#4E4233` |

## 5. Herramientas de revisión

- `tools/capture.sh escena salida.png [ancho] [alto] [fotogramas]` hace una captura por cada cámara del grupo `capture_camera`.
- `CAPTURE_ARGS="--hide=InkPost"` captura sin post-proceso.
- `CAPTURE_ARGS="--post=debug_view=N"` muestra una capa del post-proceso: 1 profundidad, 2 normales, 3 contorno, 4 tramado, 5 color de entrada, 6 relleno.
- Escenas de revisión en `scenes/style/`: `diorama_deposito_limpio`, `diorama_deposito_abandonado`, `diorama_patio_dia`, `diorama_patio_anochecer`, `diorama_patio_noche`, `prueba_estilo`, `personajes_superficie`, `personajes_deposito` y las de primera persona (`primera_persona_caja`, `_caja_grande`, `_lata`, `_bidon` e `_inspeccion`). El visor (`visor_estilo`, la escena principal) las recorre todas.

## 6. Pendiente en la Fase 1

- Huellas en la nieve y ventisca (F1-07).
- Más detalle en las ruinas del horizonte y en la silueta de la Zona Cero.
- Panel de depuración dentro del juego para mover miedo, hora y zona (F1-11).
- Piezas de interfaz en el estilo final y tipografías (F1-12, F1-13).
- Vídeo corto de los dioramas (F1-14).
- Ajustes que salgan de tu revisión de las capturas.
