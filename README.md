<div align="center">

# TUMANSK

*Título de trabajo · repositorio `Metro_S.T.A.L.K.E.R`*

**Supervivencia táctica en primera persona: sube a la superficie de una ciudad soviética arrasada, saquea lo que puedas y vuelve vivo a tu depósito.**

Gestión acogedora bajo tierra · Exploración de terror en la superficie · 3D con estilo de ilustración entintada

</div>

> Tu padre subió una última vez y no volvió.
> Lo único que heredaste es un depósito sucio en una estación de metro.
> Arriba está todo lo que necesitas para sobrevivir. Y todo lo que puede matarte.

---

## Índice

0. [Estado del proyecto](#0-estado-del-proyecto)
1. [El concepto](#1-el-concepto)
2. [Pilares de diseño](#2-pilares-de-diseño)
3. [Dos mitades claramente divididas](#3-dos-mitades-claramente-divididas)
4. [El bucle de juego: un día](#4-el-bucle-de-juego-un-día)
5. [El Depósito: gestión](#5-el-depósito-gestión)
6. [La Superficie: táctica y terror](#6-la-superficie-táctica-y-terror)
7. [Las amenazas](#7-las-amenazas)
8. [Mundo y narrativa](#8-mundo-y-narrativa)
9. [Dirección de arte: ilustración entintada](#9-dirección-de-arte-ilustración-entintada)
10. [Interfaz: sin cajas de texto](#10-interfaz-sin-cajas-de-texto)
11. [Audio](#11-audio)
12. [Cooperativo](#12-cooperativo)
13. [Arquitectura técnica (Godot 4)](#13-arquitectura-técnica-godot-4)
14. [Plan por fases](#14-plan-por-fases)
15. [Hoja de Desarrollo](#15-hoja-de-desarrollo)
16. [Riesgos y mitigaciones](#16-riesgos-y-mitigaciones)
17. [Preguntas abiertas](#17-preguntas-abiertas)
18. [Propiedad intelectual](#18-propiedad-intelectual)
19. [Glosario](#19-glosario)

---

## 0. Estado del proyecto

| | |
|---|---|
| **Fase actual** | Fase 0 terminada · Fase 1 (*Prueba de Tinta*) completa, a falta de tu aprobación · Fase 2 (*El Depósito jugable*) en curso · Fase 3 empezada: la maqueta de la ciudad (F3-15), su red de tránsito (F3-17) y los edificios de la superficie (F3-16) |
| **Motor** | Godot 4.7.2 |
| **Plataforma** | PC (Windows; la build de Linux sale casi gratis) |
| **Idioma** | Solo español |
| **Calidad objetivo** | Lista para publicarse, aunque por ahora no se publique |
| **Equipo de referencia** | Ryzen 7 8700G con su gráfica integrada (Radeon 780M) |
| **Siguiente hito** | H1 · *Prueba de Tinta* (Fase 1) y H2 · *El depósito abre* (Fase 2) |
| **La ciudad** | Plano completo fijado: [docs/CIUDAD.md](docs/CIUDAD.md) · Maqueta en 3D: `scenes/debug/maqueta_ciudad.tscn` (F6 en el editor) |

**Para abrirlo**: instala Godot 4.7.2, importa `project.godot` y pulsa F5. Se abre **el depósito jugable**: WASD para andar, el ratón para mirar, F para coger y soltar, y el botón derecho para acercar un objeto y girarlo. Con F9 abres la partida a otro jugador y con F10 te unes a una. El visor del estilo de la Fase 1 sigue en `scenes/style/visor_estilo.tscn` (F6 en el editor): ← → cambian de diorama, C de cámara, ↑ ↓ suben o bajan el miedo, L enciende la linterna y F1 abre el panel de depuración (hora, clima, miedo, radiación y estilo). Todo lo demás (herramientas, órdenes, pipelines) está en [docs/DESARROLLO.md](docs/DESARROLLO.md).

### Así se ve ahora (Prueba de Tinta, completa)

| | |
|---|---|
| ![El depósito, desde el pasillo de la estación: el mostrador con la báscula](docs/capturas/fase1_deposito_limpio_pasillo.jpg) | ![El depósito, el primer día](docs/capturas/fase1_deposito_abandonado_persiana.jpg) |
| ![El equipo del stalker, cada pieza con su etiqueta](docs/capturas/fase1_equipo.jpg) | ![El depósito por dentro: almacén, banco, estufa, catre y pila](docs/capturas/fase1_deposito_limpio.jpg) |
| ![El rincón para dormir: la estufa y el catre](docs/capturas/fase1_deposito_limpio_rincon.jpg) | ![El banco: el cuaderno y las herramientas del oficio, con contorno de casco](docs/capturas/fase1_deposito_limpio_banco.jpg) |
| ![Patio de Los Bloques, de día](docs/capturas/fase1_patio_dia.jpg) | ![Patio de Los Bloques, al anochecer](docs/capturas/fase1_patio_anochecer.jpg) |
| ![De noche, sin linterna](docs/capturas/fase1_patio_noche.jpg) | ![De noche, con linterna](docs/capturas/fase1_patio_noche_linterna.jpg) |
| ![Hacia la Zona Cero, entre los bloques](docs/capturas/fase1_patio_dia_horizonte.jpg) | ![El quiosco de prensa](docs/capturas/fase1_patio_dia_quiosco.jpg) |
| ![Ventisca](docs/capturas/fase1_patio_ventisca.jpg) | ![Huellas de bota y de perro en la nieve](docs/capturas/fase1_patio_dia_huellas.jpg) |
| ![El dosímetro, la máscara y la brújula, de cerca](docs/capturas/fase1_equipo_detalle.jpg) | ![Las primeras piezas de interfaz](docs/capturas/fase1_interfaz.jpg) |

Vídeo de 33 segundos con todos los dioramas: [docs/capturas/fase1_dioramas.mp4](docs/capturas/fase1_dioramas.mp4).

Todo lo que se ve (los muebles y el equipo, estanterías, cajas, persiana, bloques dañados, escombros, coches, ruinas del horizonte) está generado por código: 57 modelos, cada uno a partir de su receta. La guía de estilo con los valores actuales está en [docs/ESTILO.md](docs/ESTILO.md).

### Los protagonistas (Fase 2, segunda pasada)

| | |
|---|---|
| ![Los dos protagonistas en el patio de Los Bloques](docs/capturas/fase2_personajes_superficie.jpg) | ![Primer plano](docs/capturas/fase2_personajes_caras.jpg) |
| ![En el depósito](docs/capturas/fase2_personajes_deposito.jpg) | ![De frente, de perfil y de espaldas](docs/capturas/fase2_personajes_fila.jpg) |
| ![En marcha: caminar y cargar](docs/capturas/fase2_personajes_marcha.jpg) | ![Primera persona: las manos agarran lo que llevas (caja pequeña, caja grande, lata y bidón)](docs/capturas/fase2_primera_persona.jpg) |

El chico y la chica, también generados por código: modelo, esqueleto, animaciones y las manos que se ven en primera persona. Tras tu primera revisión ("no puede ser un mundo tan *friendly*") son adolescentes flacos y ojerosos, con ropa heredada y remendada y equipo de stalker. Están **pendientes de tu visto bueno**.

### El plano de la ciudad

![Plano general de Tumansk](docs/ciudad/plano_tumansk.jpg)

Tumansk ya tiene plano: **dónde está cada calle, cada manzana y cada edificio**, el relieve, el metro, las amenazas, los peligros y varias rutas a cada objetivo. Es solo para desarrollo (en el juego no hay mapas).

- 1,6 × 1,2 km, con 8 zonas, el río y los túneles.
- 357 edificios, 314 de ellos con interior.
- 16 km de calles y 818 vehículos del atasco de la evacuación.

Todo está explicado en [docs/CIUDAD.md](docs/CIUDAD.md), con cuatro hojas: [general](docs/ciudad/plano_tumansk.jpg), [subsuelo](docs/ciudad/plano_tumansk_subsuelo.jpg), [amenazas y peligros](docs/ciudad/plano_tumansk_peligros.jpg) y [rutas](docs/ciudad/plano_tumansk_rutas.jpg).

### La maqueta de la ciudad (F3-15)

| | |
|---|---|
| ![Tumansk desde el aire, sin niebla](docs/capturas/fase3_maqueta_aerea.jpg) | ![La avenida, hacia el puente y la Casa de los Sóviets](docs/capturas/fase3_maqueta_avenida.jpg) |
| ![Las rutas y los sectores](docs/capturas/fase3_maqueta_rutas.jpg) | ![El panel: dónde estás, qué tienes delante y qué hitos se ven](docs/capturas/fase3_maqueta_panel.jpg) |

La ciudad entera en 3D, levantada desde el plano: el relieve, las calles, los 357 edificios a su altura y con lo que queda en pie según su daño, los vehículos, los árboles y los puentes. Los 142 edificios que ya tienen modelo (las viviendas del kit y los singulares) se ven con él de cerca; los demás, y todos de lejos, en volúmenes sencillos. Sirve para probar recorridos, vistas, sectores de carga y rendimiento.

| | |
|---|---|
| ![El vestíbulo del metro en su plaza](docs/capturas/fase3_maqueta_vestibulo.jpg) | ![La Casa de los Sóviets cierra la avenida](docs/capturas/fase3_maqueta_soviets.jpg) |

- **Para abrirla:** en Godot, `scenes/debug/maqueta_ciudad.tscn` y **F6**. Se recorre a pie (Tab para volar), con vistas fijas (1-9 y 0) y recorridos automáticos de las rutas del plano con cronómetro (R).
- **Herramientas:** cuenta los hitos que se ven desde donde estás (y comprueba la regla en toda la ciudad con V) y mide el rendimiento en tu PC (B). Todas las teclas, en [DESARROLLO.md](docs/DESARROLLO.md#la-maqueta-de-la-ciudad-f3-15).
- **Lo que ha enseñado**, en [CIUDAD.md](docs/CIUDAD.md#15-la-maqueta): desde el 92 % de la calle se ven al menos dos hitos, pero no desde los patios cerrados; y la niebla de día tapa la ciudad a partir de unos 300 m, así que los hitos la atraviesan.
- **Los edificios del kit en ella** ([CIUDAD.md](docs/CIUDAD.md#los-edificios-del-kit-en-la-maqueta)): cada uno tiene tres escalones de detalle (su volumen a más de 200 m, su modelo sin sombras hasta 60 m y entero más cerca) para que el coste de dibujo no se dispare ([D-052](docs/DECISIONES.md)); los que están en ladera llevan un zócalo, y los singulares se asientan en una explanada del plano ([D-051](docs/DECISIONES.md)). Se sale del metro por el foso de las escaleras del vestíbulo, y en la Casa de los Sóviets se sube por el escombro hasta el boquete.

### Los edificios de la superficie (F3-16)

| | |
|---|---|
| ![Una jrushchovka de cinco plantas: paneles, balcones y los portales](docs/capturas/fase3_kit_jrushchovka.jpg) | ![Una estalinista de esquina en la plaza del Trabajo](docs/capturas/fase3_kit_estalinka.jpg) |
| ![El bloque de 9 plantas, de plaqueta, y la torre de 16](docs/capturas/fase3_kit_bloque.jpg) | ![La fachada de una estalinista: recercados, frontones, imposta y escaparates](docs/capturas/fase3_kit_estalinka_fachada.jpg) |
| ![La casa obrera y una casa de ladrillo de los mercaderes](docs/capturas/fase3_kit_mercader.jpg) | ![Una isba: guardapolvos tallados, contraventanas y prichelinas](docs/capturas/fase3_kit_isba.jpg) |
| ![Los daños: el extremo que mira a la bomba se hunde](docs/capturas/fase3_kit_danos.jpg) | ![El barracón obrero](docs/capturas/fase3_kit_barracon.jpg) |
| ![Al anochecer](docs/capturas/fase3_kit_anochecer.jpg) | ![De noche, con linterna, ante un portal](docs/capturas/fase3_kit_noche.jpg) |

Las 138 viviendas del plano ya tienen sus modelos 3D: se montan con un kit de piezas generadas por código, en cuatro familias, cada una a partir de su ficha del plano (huella, plantas, daño, incendio, dónde cayó la bomba).

- **Las familias:** los bloques de paneles (jrushchovka, bloque de 9 plantas y torre de 16), las casas de muros de carga (la estalinista, la casa obrera y la casa de ladrillo de antes de la revolución) y las de madera (la isba y el barracón).
- **Muros y materiales:** hormigón pintado, plaqueta, ladrillo visto y estuco que se cae alrededor de los huecos y deja ver el ladrillo; suciedad, chorretones y hollín sobre las ventanas quemadas. Cada casa tiene su tono y cada panel el suyo.
- **Daños como en la maqueta:** el extremo que mira a la bomba se hunde, cascarones, muñones con su escombro, balcones caídos, ventanas rotas, tapiadas o quemadas, y las casas de madera ardidas.
- **Hechos para la tinta:** molduras con perfil y cantos en derrame, juntas enrasadas y nada plano y estrecho, para que el contorno se dibuje limpio de cerca, de lejos y a ras ([D-036](docs/DECISIONES.md)).
- **Para verlos:** en Godot, `scenes/style/diorama_edificios.tscn` (cada tipo con cada daño), `diorama_plaza.tscn` y `diorama_mercaderes.tscn` (las casas del plano tal cual), con **F6**. Cómo funciona y cómo se añaden piezas, en [DESARROLLO.md](docs/DESARROLLO.md#el-kit-de-arquitectura-f3-16); las reglas de estilo, en [ESTILO.md](docs/ESTILO.md#9-los-edificios-del-kit-f3-16).

#### Los edificios singulares

| | |
|---|---|
| ![El vestíbulo del metro desde la avenida: la rotonda, la columnata, МЕТРО y el control del ejército](docs/capturas/fase3_singular_vestibulo.jpg) | ![La cúpula de la sala, con la lámpara y la linterna sobre el óculo](docs/capturas/fase3_singular_vestibulo_cupula.jpg) |
| ![La esclusa de la defensa civil con la compuerta abierta: por ahí sales](docs/capturas/fase3_singular_vestibulo_compuerta.jpg) | ![El Edificio Partido desde el cráter: los pisos abiertos, como una casa de muñecas](docs/capturas/fase3_singular_partido.jpg) |
| ![Las plantas del Edificio Partido al borde del vacío](docs/capturas/fase3_singular_partido_casa.jpg) | ![La Casa de los Sóviets y su torre al final de la avenida](docs/capturas/fase3_singular_soviets.jpg) |
| ![El escombro de la fachada reventada de la Casa de los Sóviets: por él se sube al boquete](docs/capturas/fase3_singular_soviets_escombro.jpg) | ![El cuarto quemado detrás del boquete, con lo que ardió de las oficinas](docs/capturas/fase3_singular_soviets_cuarto.jpg) |

Los hitos y los sitios clave no salen del kit: son modelos enteros, hechos uno a uno con el máximo cuidado, que se ponen por su id del plano. Los tres primeros:

- **El vestíbulo del metro** (PLZ-06, tu salida): una rotonda de los años cincuenta con veinte columnas, la cúpula de chapa con su linterna y la estrella, y МЕТРО sobre la entrada; delante, el control del ejército de la evacuación. Por dentro se recorre entero: la sala con su cúpula de casetones, la lámpara, los torniquetes y el equipaje abandonado, y la esclusa de hormigón con la compuerta blindada por la que sales, sobre las tres escaleras mecánicas que bajan a oscuras.
- **El Edificio Partido** (ZC-01, donde termina el juego): un instituto de catorce plantas al que la bomba arrancó la mitad que la miraba. Lo que queda tiene los pisos abiertos al cráter, con los laboratorios y los despachos al borde del vacío, forjados colgando y el montón de escombros al pie; se sube por su escalera hasta la azotea, que mira al cráter.
- **La Casa de los Sóviets y su torre** (CEN-SOV y CEN-SOVT): el bloque estalinista que cierra la avenida, con su pórtico de columnas gigantes y el escudo, quemado entero y con la fachada noreste reventada: su escombro sale hasta la calle, y por él se sube al boquete y se baja al cuarto quemado de detrás, entre archivadores, la caja fuerte y mesas carbonizadas. La torre, de 110 m, tiene la aguja doblada hacia el suroeste y el puesto del vigía en la planta 20.

Tienen su colisión hecha a mano (los escalones y las escaleras son rampas) y dicen dónde quitar el terreno cuando bajan bajo la calle. Se ven en `diorama_vestibulo.tscn`, `diorama_partido.tscn` y `diorama_soviets.tscn` ([DESARROLLO.md](docs/DESARROLLO.md#los-edificios-singulares)), y ya están en la maqueta.

### Decisiones tomadas

| Tema | Decisión |
|---|---|
| Título | **Tumansk** (título de trabajo) |
| Premisa | Subes a la superficie a **saquear**. Lo que encuentras lo limpias, lo reparas, lo guardas y lo vendes en tu **depósito**, dentro de una estación de metro |
| Objetivo final | **Llegar a la zona más lejana y saber qué le pasó a tu padre.** Es la Zona Cero, donde cayó la bomba: no se va al cráter, sino a un edificio partido por la mitad que está muy cerca. Es muy difícil: exige el mejor equipo (máscaras, muchos filtros), conocer bien los caminos y llegar al final de la partida |
| Refugios | **Los construyes tú.** Con martillo y tablas clavas, tapias puertas y ventanas y mueves cajas y muebles. Casi cualquier sitio puede convertirse en refugio, pero no todos serán seguros. El juego no hace refugios por ti |
| Clima | **Invierno largo, con nieve.** Las huellas son información: tú ves las de los demás y ellos ven las tuyas |
| Cielo y noche | El cielo nunca es negro del todo, pero **la noche es muy oscura**: sin linterna prácticamente no se ve nada |
| Mundo | Posapocalipsis tras una **guerra atómica**, en **Tumansk**, una gran ciudad soviética inspirada en Moscú. Han pasado **dos años** desde la Noche de la Caída de las Bombas (sin año en el calendario) |
| Historia | Mínima. Bajo tierra se formó un **gobierno civil** en la red de túneles, y por eso las instalaciones de dentro están en buen estado. No se nombra la estación ni hay facciones |
| Protagonista | Hijo o hija de un stalker, de los que suben a buscar lo que queda. Demasiado joven para el oficio. Se llama como tú, y eliges si es chico o chica al firmar la escritura |
| Tu padre | En la superficie hay pocos rastros suyos, y ambiguos. La respuesta está al final |
| Estación | Siempre segura. Solo se recorre un trozo pequeño: el depósito, el pasillo de delante y la salida |
| Moneda | **Rublos** |
| Supervivencia | **Impuesto diario** suave por el local y **comer** cada día. El agua la da la estación |
| Muerte | **Permanente.** Si mueres, pierdes la partida. En cooperativo, quien muere queda fuera y la partida sigue mientras quede alguien vivo |
| Mapas | **No existen.** Los dibujas tú en tu cuaderno |
| Rutas | **Siempre hay varias** para llegar a un mismo sitio |
| Defensa | **Herramientas, no armas.** No se puede matar |
| Enemigos | **Pocos y de gran calidad.** Los humanos son muy inteligentes, pero nunca saben nada que no hayan percibido. Los saqueadores matan |
| Mundo vivo | Como en *Rain World*: **el mundo funciona sin el jugador**. Saqueadores y criaturas tienen rutinas de día y de noche, se cazan y se enfrentan entre ellos. El jugador es un organismo más |
| Ciudad | Una ciudad de verdad, con lógica: los edificios se recorren por dentro y la calidad es la misma en toda la parte explorable. **El plano completo está fijado** en [docs/CIUDAD.md](docs/CIUDAD.md): 1,6 × 1,2 km a orillas del río Tumán, 8 zonas, el río y los túneles |
| Cooperativo | **Arquitectura preparada desde el primer día**, de 2 a 4 jugadores |
| Motor | **Godot 4.7.2** con GDScript tipado |
| Estilo visual | **Ilustración entintada** |
| Producción 3D | **Modelos generados por código**: Blender 5 como módulo de Python, más generación dentro del motor |

### Próximos pasos

1. **Fase 1**: revisar las capturas, el [vídeo](docs/capturas/fase1_dioramas.mp4) y las piezas de interfaz, y aprobar el estilo. Con eso empiezan de lleno las Fases 2 y 3.
2. **Tu revisión de los protagonistas** (capturas de arriba): ¿tienen ya el tono de Tumansk?
3. **Fase 2**: seguir con el depósito jugable; lo siguiente es el primer día (limpiar) y el procesado del botín.
4. **La maqueta** (F3-15): abrirla en tu PC, recorrerla y medir el rendimiento con la tecla B (aquí no hay gráfica, solo puedo contar llamadas de dibujo y triángulos). Ahora, con los edificios del kit, las calles residenciales cuestan entre 900 y 1.250 llamadas: es la medida que más interesa.
5. **Los edificios** (F3-16): revisar las capturas, recorrer con F6 los dioramas de edificios y los de los tres singulares, y verlos en la maqueta (Ctrl+4 y Ctrl+5: el vestíbulo y la Casa de los Sóviets). Lo siguiente serían los interiores de serie, el resto de los sitios clave y, si el rendimiento lo pide, juntar las piezas iguales de cada manzana.
6. Responder las [preguntas abiertas](#17-preguntas-abiertas) que quedan: dos son nuevas y salen de la maqueta.

---

## 1. El concepto

### Premisa

Hace dos años, en la Noche de la Caída de las Bombas, la gente de Tumansk se refugió en el metro. Bajo tierra se organizó un gobierno civil que mantiene las estaciones en pie: hay luz, agua y orden. Arriba quedó una ciudad de avenidas anchas, bloques de hormigón y nieve sucia, donde el aire y la radiación matan despacio y lo que vive entre las ruinas mata rápido.

Algunos suben de todos modos. En la estación los llaman **stalkers**: buscan lo que queda (medicinas, comida, herramientas, piezas) y lo venden abajo. Tu padre era uno de ellos. Cuando enfermó tuvo que dejarlo, pero un día subió una última vez y no volvió. No sabes nada de él.

Lo único que heredas es un **depósito** en la estación: un local que él compró y nunca llegó a usar. Está sucio, lleno de telarañas y de cajas desordenadas. Eres demasiado joven para el oficio. Pero el impuesto hay que pagarlo, y hay que comer.

### En una frase

*Un depósito que levantar bajo tierra y una ciudad muerta que saquear arriba: planifica cada salida, dibuja tus propios mapas y vuelve vivo.*

### La ambientación de la superficie: nada está intacto

La superficie es una ciudad soviética de provincias que ya estaba gastada antes de la guerra, que recibió una bomba atómica a pocos kilómetros (cayó en el nudo ferroviario y la Planta Nº 1, al noreste; otra, más lejos, al suroeste) y que lleva dos años abandonada a un invierno que no acaba. Todo lo que se haga para el exterior cuenta esas tres cosas a la vez:

- **El desgaste de antes de la guerra**: asfalto parcheado y agrietado, hormigón soviético de mala calidad (poroso, desconchado, con la armadura oxidada asomando), losas desniveladas, bordillos rotos, pintura vial desvaída y óxido en todo lo metálico.
- **La bomba**: cuanto más cerca de la Zona Cero, más destrozo. Hollín y quemaduras, cristales y escombros por todas partes, losas levantadas, grietas abiertas por la onda, y postes y árboles tumbados en la misma dirección.
- **Dos años de abandono en invierno**: nadie limpia ni repara. El hielo revienta las tuberías y las alcantarillas y el terreno se hunde sobre ellas: socavones en mitad de la calle, como en *Metro 2033*. Las heladas abren baches y levantan las losas, faltan tapas de registro o están movidas, la nieve y el hielo se amontonan en los rincones, asoman matojos secos en las grietas, y los vehículos y los trenes se pudren donde se pararon.

Reglas para todo lo que se haga fuera (modelos, texturas, terreno, calles):

1. **Nada nace limpio ni nuevo.** Cada superficie, modelo y textura lleva grietas, desconchones, manchas, óxido, piezas que faltan o suciedad. Una superficie impecable es un fallo, como lo sería un agujero en el suelo.
2. **El daño tiene causa y dirección.** Se reparte según la distancia a la Zona Cero, lo que hay debajo (colectores, galerías, tuberías) y lo que el tiempo hace a cada material; no a voleo.
3. **Se nota de cerca y de lejos.** De cerca, en el detalle: bordes rotos, gravilla suelta, juntas abiertas. De lejos, en la silueta: socavones, cosas caídas, huecos.
4. **Sigue siendo legible.** El jugador tiene que poder leer por dónde se pasa y qué es peligroso: un socavón, un pozo abierto, hielo fino.
5. **Es determinista.** El deterioro sale de semillas fijas, como todo el plano: dos ejecuciones dan la misma ciudad rota.

En las calles ya está hecho así (`tools/ciudad/deterioro.py`, `firmes.py` y `restos.py`; ver [CIUDAD.md, «La superficie, rota»](docs/CIUDAD.md#17-la-superficie-rota) y las decisiones D-041 y D-053). **La calle no es un plano**: el firme está levantado en placas (más cerca de la Zona Cero), los bordillos van pieza a pieza (faltan o se han movido) y hay diez socavones sobre los colectores, la galería de la calefacción, las tuberías del agua y el túnel del metro. Encima, escombros al pie de las fachadas, basura en las cunetas, contenedores volcados, farolas torcidas, caídas o arrancadas, el tendido del tranvía y del trolebús con sus postes torcidos o caídos y los hilos colgando o tirados en la calle, grietas, baches, tapas abiertas o robadas, pintura a trozos, carriles oxidados, traviesas que faltan y matojos secos. Los vehículos también: cada uno es su modelo, oxidado, con los cristales rotos y las ruedas pinchadas, y los quemados, sobre las llantas (D-054). Lo siguiente que se haga fuera (edificios, patios) sigue las mismas reglas.

### Qué hace el jugador

- **En el Depósito**: limpia y restaura el local; procesa el botín (mide la radiación, descontamina, repara, pesa, etiqueta y ordena); atiende el mostrador; acepta encargos; paga el impuesto y come.
- **En la Superficie**: observa, planifica, se mueve sin ser visto, saquea, dibuja su mapa y vuelve antes de que se acaben la luz, el aire o la suerte.

---

## 2. Pilares de diseño

1. **Dos mundos, un mismo trazo.** El depósito es el hogar: luz ámbar, líneas limpias, colores cálidos. La superficie es hostil: frío, ceniza, líneas que tiemblan.
2. **Tajante.** La muerte es definitiva. Cada salida a una zona nueva exige un plan; ir de frente se paga con la partida.
3. **Tu mapa lo dibujas tú.** No hay mapas, ni minimapa, ni marcadores. Lo que sabes de la ciudad está en tu cuaderno, dibujado por ti.
4. **Siempre hay otra ruta.** A cada objetivo se llega de varias formas: por la calle, por dentro de los edificios, por los tejados o por debajo.
5. **Eres frágil.** No hay armas y no se mata. Hay información, preparación, sigilo y huida.
6. **Enemigos justos.** Pocos, de gran calidad, y nunca hacen trampa: solo saben lo que ven, oyen o huelen.
7. **El mundo está vivo.** Como en *Rain World*, todo sigue funcionando aunque no estés: los saqueadores duermen en sus guaridas, unas criaturas salen a cazar mientras otras descansan, y se pelean entre ellas. Tú eres un organismo más.
8. **Pequeño pero impecable.** Poco espacio, muy bien hecho, y la misma calidad en toda la ciudad que se explora. Calidad antes que cantidad, en todo.
9. **Sin cajas de texto.** Toda la interfaz es un objeto del mundo.
10. **Nada está intacto.** Fuera, todo lleva el desgaste de una ciudad soviética vieja, la huella de la bomba y dos años de abandono en invierno (ver [la ambientación de la superficie](#la-ambientación-de-la-superficie-nada-está-intacto)).

---

## 3. Dos mitades claramente divididas

| | **El Depósito** (gestión) | **La Superficie** (exploración) |
|---|---|---|
| Emoción | Calma, rutina, satisfacción, hogar | Miedo, incertidumbre, vulnerabilidad |
| Ritmo | Sin prisa durante el día de trabajo | Tensión constante: la luz del día y los filtros se acaban |
| Luz | Lámparas de taller, bombillas desnudas, calor | Cielo gris, nieve, tu linterna, oscuridad |
| Trazo | Contorno firme, temblor casi imperceptible | Contorno nervioso, tramado denso |
| Color | Cálido y saturado | Frío y desaturado: ceniza, óxido, hormigón |
| Sonido | La radio, el murmullo de la estación, herramientas | Viento, nieve que cruje, el dosímetro, tu respiración dentro de la máscara |
| Interfaz | Objetos sobre la mesa: cuaderno, libro de cuentas, tablón | Casi nada: tus manos, tu reloj, tu dosímetro, tu cuaderno |
| Verbos | Limpiar, reparar, etiquetar, ordenar, vender | Observar, dibujar, escuchar, esconderse, trepar, abrir, huir |

**La frontera es física**: la **escalera mecánica parada** y la **compuerta hermética** de la estación. Mientras subes, la imagen cambia poco a poco: el color se enfría, el trazo empieza a temblar y la radio del depósito se apaga a tu espalda. Bajar de vuelta es el momento de alivio.

---

## 4. El bucle de juego: un día

```mermaid
flowchart LR
    A["Mañana<br/>clientes · encargos"] --> B["Planificar<br/>cuaderno · mochila"]
    B --> C["La subida<br/>escalera · compuerta"]
    C --> D["La superficie<br/>observar · saquear · dibujar"]
    D --> E["El regreso"]
    D -.->|mueres| X["Fin de la partida"]
    E --> F["Procesar el botín<br/>dosímetro · limpiar · reparar · etiquetar"]
    F --> G["Vender<br/>mostrador · encargos"]
    G --> H["Noche<br/>impuesto · comer · dormir"]
    H --> A
```

1. **Mañana.** Subes la persiana metálica del depósito. Los clientes compran, te venden cosas y dejan **encargos**.
2. **Planificar.** Sobre la mesa repasas tus mapas, eliges objetivo, ruta y una alternativa, y preparas la mochila. Cada hueco que ocupa una herramienta es un hueco menos para el botín.
3. **La subida.** Escalera mecánica, compuerta. El mundo cambia.
4. **La superficie.** Observas, te mueves, saqueas, dibujas lo que descubres y evitas lo que no puedes vencer. Mientras tanto, se acaban la luz del día y los filtros.
5. **El regreso.** Si vuelves.
6. **Procesar el botín.** Dosímetro, descontaminación, reparación, peso, etiqueta, estantería.
7. **Vender.** Cumples encargos, vendes y cobras.
8. **Noche.** Pagas el impuesto, comes y duermes. Al dormir se guarda la partida.

### Duración de las salidas

| Etapa | Duración típica |
|---|---|
| Primeras salidas | 10–20 minutos |
| Salidas planificadas | 30–60 minutos |
| Zonas avanzadas | Unos 60 minutos |

### Encargos y peligro

Cuanto más peligroso es un encargo, más paga y más difícil es volver. *(Valores iniciales; se equilibran en la Fase 8.)*

| Peligro | Ejemplo | Paga relativa |
|---|---|---|
| ● | Latas de conserva de los quioscos de la plaza | ×1 |
| ●● | Una radio de un piso de Los Bloques | ×2 |
| ●●● | Antibióticos de la farmacia de un bloque con Inquilino | ×3,5 |
| ●●●● | Piezas de los grandes almacenes de la avenida, territorio de saqueadores | ×6 |
| ●●●●● | Insulina del hospital | ×10 |

---

## 5. El Depósito: gestión

### 5.1 El espacio

Pequeño a propósito: pocos metros cuadrados, cuidados al milímetro.

| Rincón | Qué hay |
|---|---|
| Mostrador | La persiana metálica que se sube cada mañana, el mostrador, la vitrina, la caja de los rublos |
| Almacén | Estanterías, cajas, ganchos y redes. El espacio es limitado: ordenarlo bien es parte del juego |
| Banco de trabajo | Reparaciones, piezas, herramientas |
| Descontaminación | Pila, cepillos, bolsas, el dosímetro |
| Para dormir | Un catre, una estufa, tus cosas |
| Mesa de planificación | Tu cuaderno y el tablero de la pared, con tus páginas y el hilo de las rutas |

**La estación**, de la que solo se recorre un trozo: el pasillo frente al depósito, el puesto de comida de al lado, el tablón de avisos, la escalera mecánica y la compuerta. El resto (gente, humo, luces) se ve y se oye, pero no se recorre.

### 5.2 El primer día: limpiar

Funciona como tutorial y, como en Cat Mail Co., tiene que dar gusto:

- Quitar telarañas, barrer, fregar, sacar la basura.
- Vaciar las cajas desordenadas del antiguo dueño. Entre los trastos aparecen tus primeras herramientas y algo de mercancía.
- Cambiar una bombilla, desatascar la persiana con una palanca, encender la estufa.
- Al acabar, el depósito ha pasado del abandono a ser un negocio. Ver el antes y el después es parte de la recompensa.

### 5.3 Procesar el botín

Lo que en Cat Mail Co. es pesar, sellar y etiquetar paquetes, aquí es preparar lo que traes de arriba:

1. **Vaciar la mochila** sobre la mesa.
2. **Inspeccionar**: girar el objeto, leer sus etiquetas, ver en qué estado está.
3. **Medir la radiación** con el dosímetro. Lo contaminado se **descontamina** (lavar, cepillar, embolsar) o se aparta: vale menos y es peligroso tenerlo cerca.
4. **Reparar** en el banco, con minijuegos táctiles: atornillar, limpiar contactos, coser, cambiar piezas aprovechando las de otros objetos rotos.
5. **Pesar**: la chatarra y los metales se venden al peso.
6. **Etiquetar**: escribes el precio a mano en una etiqueta de cartón y la atas con cordel. Las cajas llevan el icono de su categoría.
7. **Ordenar** en las estanterías: medicinas, comida, herramientas, electrónica, ropa, chatarra.

### 5.4 El mostrador y los clientes

- Pocos clientes, todos de la estación, que vuelven una y otra vez: compran, te venden, regatean y dejan encargos.
- Hablan poco y con la voz amortiguada; lo que dicen aparece en notas y papelitos escritos a mano.
- Algunos ejemplos: un relojero que busca piezas, una madre que necesita antibióticos para su hijo, un anciano que te pide la foto que dejó en su antiguo piso.

### 5.5 Encargos

- Se cuelgan como fichas en un tablón de corcho: qué quieren, cuánto pagan, el plazo y **pistas, no mapas**. Por ejemplo: "Bloque 7, cuarto piso, la puerta con un gato pintado". Encontrarlo es cosa tuya.
- Cuanto más peligrosa es la zona, mejor pagan.

### 5.6 Economía

- **Rublos.**
- **Impuesto diario** al gobierno civil por el local. Es suave, pero si la deuda se acumula, la estación precinta el depósito (no puedes vender) hasta que pagues.
- **Comida**: hay que comer cada día, lo que compres en el puesto de al lado o lo que encuentres arriba. Sin comer te debilitas: menos aliento y más temblor. Varios días sin comer, y mueres.
- **Precios**: dependen del estado del objeto, de su contaminación y de la demanda. Los encargos pagan más que la venta suelta.

### 5.7 Mejoras

- Más estanterías, ganchos y redes: más capacidad en el mismo local.
- Herramientas para el banco, que permiten más reparaciones.
- Una pila de descontaminación mejor, la estufa, la radio, mejor luz, una vitrina en el mostrador.
- Equipo: una mochila más grande (se cose en el banco), ropa de abrigo, una máscara mejor.
- Personalización: carteles, una planta bajo la lámpara, objetos que traes de arriba. El depósito es tu sitio.

---

## 6. La Superficie: táctica y terror

### 6.1 Principios

- **Planificar o morir.** Antes de entrar en una zona nueva hay que observarla desde lejos y desde arriba.
- **Incertidumbre.** Sin minimapa, sin marcadores, sin barras de vida. La información llega por la vista, el oído y tu cuaderno.
- **Mostrar poco.** Las amenazas se intuyen antes de verse: huellas, ruidos, restos.
- **Tensión y alivio.** Los sitios donde respirar y dibujar no te los da el juego: los preparas tú (ver [6.12](#612-refugios-hechos-a-mano)).
- **La ciudad cambia entre salidas, porque está viva.** El mapa base es fijo, pero lo que hay en él no: clima, hora, patrullas, la jauría que se desplaza, campamentos nuevos, lo que otros se han llevado (ver [7.6](#76-el-mundo-vivo)).

### 6.2 Tu mapa lo dibujas tú

- **No hay mapas en el juego.** Ni encontrados, ni comprados, ni en pantalla.
- **El cuaderno** tiene páginas cuadriculadas. Dibujas con lápiz, goma, regla y lápices de colores, y puedes añadir pequeños símbolos (peligro, entrada, botín, radiación, refugio, "visto a las 14:20") y notas escritas.
- **Instrumentos que ayudan**: la **brújula** (para orientar el mapa), el **podómetro** (para medir distancias en pasos), el **reloj** (para anotar los horarios de las patrullas) y los **prismáticos** (para observar desde las alturas).
- **Dónde se dibuja**: en el depósito, con calma; en la superficie, solo en un sitio seguro, porque abrir el cuaderno lleva tiempo y hace falta luz. El miedo hace temblar el trazo.
- **Planificar**: en el depósito pegas páginas en el tablero de la pared y marcas las rutas con hilo. Siempre una ruta principal y otra de escape.
- **Si mueres, el cuaderno se pierde contigo.** Lo que aprendiste solo queda en tu cabeza.

### 6.3 Siempre hay otra ruta

Reglas de diseño de niveles:

- Cada objetivo tiene al menos tres accesos: por la calle, por el interior de los edificios, por los tejados o por el subsuelo.
- Cada ruta tiene su perfil: rápida y expuesta, lenta y segura, ruidosa, o que exige una herramienta (cuerda, tablón, cizalla, ganzúas).
- Hay puntos altos desde los que observar antes de entrar.
- Hay pocos pasos obligados, y son peligrosos: los saqueadores también los conocen.
- Puedes crear tus propios atajos (una cuerda que dejas colgada, un tablón entre azoteas, una puerta forzada)… y otros también pueden usarlos.
- **Una ciudad de verdad.** Todo tiene lógica urbana: calles, patios, servicios, comercios en los bajos, sótanos y tejados. Los edificios se recorren por dentro (portales, escaleras, pisos, sótanos) y la calidad es la misma en toda la parte explorable.

### 6.4 Sigilo: qué te delata

| Factor | Ejemplos |
|---|---|
| Ruido | Correr, nieve que cruje, cristales, escaleras metálicas, agua, lo que llevas suelto en la mochila |
| Luz | Tu linterna se ve desde muy lejos |
| Silueta | En un tejado, recortado contra el cielo, se te ve desde toda la avenida |
| Rastro | Huellas en la nieve, tu olor si el viento sopla hacia ellos, sangre |
| Clima | El viento y la lluvia tapan ruidos; la nieve que cae borra huellas; la ventisca esconde a todos |

### 6.5 La mochila

- Es una **cuadrícula** (6×5 al empezar, ampliable) donde encajan herramientas y botín según su forma.
- El **cinturón** tiene 3 huecos de acceso rápido. Para todo lo demás hay que arrodillarse y abrir la mochila, que es lento y te deja expuesto.
- **Peso**: cuanta más carga, más lento vas, más ruido haces y antes te quedas sin aliento. Lo frágil (cristal, electrónica) se rompe si corres o te caes.
- Lo que va mal guardado suena: latas, herramientas sueltas. Empaquetar bien también es sigilo.

### 6.6 Herramientas

No hay armas. No hay magia. Hay oficio.

| Categoría | Herramienta | Para qué sirve | Coste o riesgo |
|---|---|---|---|
| Información | **Cuaderno y lápices** | Tus mapas, tus notas, tus planes | Hacen falta luz y un sitio seguro |
| | **Brújula** | Orientar el mapa, y orientarte tú | — |
| | **Podómetro** | Contar pasos para dibujar a escala | — |
| | **Reloj de pulsera** | La hora, la luz que queda, los horarios de las patrullas | — |
| | **Prismáticos** | Observar desde lejos y desde las alturas | El reflejo del cristal puede delatarte |
| | **Estetoscopio** | Escuchar a través de paredes y puertas | Te obliga a quedarte quieto |
| | **Dosímetro** | Medir la radiación del entorno y de los objetos | Sus chasquidos se oyen |
| | **Tiza** | Marcar rutas y peligros en las paredes | Los saqueadores también ven tus marcas |
| Luz | **Linterna de pilas** | Luz silenciosa | Pilas escasas; se ve desde muy lejos |
| | **Linterna de dinamo** | Luz que nunca se agota | Darle a la manivela hace ruido |
| | **Velas y cerillas** | Luz fija para dibujar o trabajar | Se consumen y delatan |
| Acceso | **Ganzúas** | Abrir cerraduras en silencio (minijuego táctil) | Se rompen; el miedo hace temblar las manos |
| | **Palanca** | Forzar puertas y cajas. No es un arma: no se puede golpear con ella | Mucho ruido |
| | **Cizalla** | Cortar cadenas y alambradas | Pesa |
| | **Cuerda** | Bajar por huecos y fachadas, atar puertas | Se puede dejar puesta como atajo |
| | **Tablón** | Puentes entre azoteas y sobre suelos hundidos; tapiar huecos | Voluminoso |
| | **Martillo y clavos** | Tapiar puertas y ventanas, condenar trampillas, montar refugios, reparar escalones | Mucho ruido, y vibra por la estructura |
| | **Navaja** | Cortar hilos trampa, cuerdas y telas. No sirve para atacar | — |
| Sigilo | **Lanzables** (latas, botellas, piedras) | Distraer con ruido | — |
| | **Despertador de cuerda** | Lo dejas, te alejas… y suena donde tú ya no estás | Ocupa sitio |
| | **Campanillas con hilo** | Alarma: sabrás si algo pasa por tu ruta de escape | — |
| | **Espejo de bolsillo** | Mirar tras las esquinas y bajo las puertas | — |
| | **Cebo** (carne) | Distraer a la Jauría | Es tu comida |
| Supervivencia | **Máscara y filtros** | Respirar donde el aire está contaminado | Ves y oyes menos; los filtros se acaban |
| | **Vendas y botiquín** | Cortes, mordeduras, sangrado | — |
| | **Pastillas antirradiación** | Reducir la dosis acumulada | Escasas y caras |
| | **Ropa de abrigo** | Aguantar el frío | Abulta |
| Carga | **Bolsas y cajas acolchadas** | Aislar lo contaminado y proteger lo frágil | Ocupan sitio |

**Se progresa con equipo y conocimiento, no con estadísticas.** No subes de nivel: mejoras porque tienes mejores herramientas, conoces mejor la ciudad y entiendes mejor lo que vive en ella.

### 6.7 Peligros del entorno

- **Radiación**: zonas calientes y objetos contaminados. El dosímetro cruje. La dosis se acumula y trae náuseas, debilidad y, al final, la muerte. Se combate con pastillas y con tiempo.
- **Aire**: en algunas zonas hace falta la máscara. Los filtros duran poco, y con la máscara puesta ves menos, oyes menos y tu respiración se oye.
- **Frío**: un invierno largo te quita aliento y te hace temblar.
- **La noche**: muy oscura. Sin linterna prácticamente no se ve nada, y una linterna se ve desde muy lejos. Hace más frío y sale otra vida: lo que de día duerme, de noche caza. Volver de noche casi nunca es buena idea.
- **Estructuras**: suelos podridos, escaleras rotas, techos que ceden.

### 6.8 Tu cuerpo es la interfaz

- **Miedo**: no hay barra. Se nota en las manos, que tiemblan (la linterna, la ganzúa, el lápiz); en la respiración, que se oye; en el sonido, que se apaga; y en el propio dibujo, porque el trazo tiembla y el tramado invade los bordes de la imagen.
- **Heridas**: cortes, mordeduras y torceduras, que se tratan con vendas y botiquín. La sangre deja rastro.
- **Hambre**: el estómago suena y las manos tiemblan.
- **Radiación**: los chasquidos del dosímetro y, si te pasas, las náuseas.
- **Aire**: la máscara se empaña y se agrieta, y la respiración se ahoga cuando el filtro se agota.

### 6.9 La muerte

- Hay **un solo guardado**, que se hace al dormir. Si sales del juego en mitad de una salida, la partida se guarda en ese punto y no se puede volver atrás.
- **Si mueres, la partida se borra.**
- La última imagen es el depósito cerrado, con un cartel escrito a mano por alguien de la estación.

### 6.10 Las zonas de Tumansk

La ciudad es **una sola zona continua y grande**, sin pantallas de carga, dividida en barrios que se ordenan por distancia a la estación: cuanto más lejos, más peligro y más valor. **El plano está fijado** en [docs/CIUDAD.md](docs/CIUDAD.md): dónde está cada calle, cada edificio, cada guarida y cada ruta. El trazado se decide a mano; los edificios se levantan con el kit modular a partir de ese plano y los sitios clave se terminan a mano.

| # | Zona | Salida típica | Qué hay | Amenazas | Botín |
|---|---|---|---|---|---|
| 0 | **La Estación** | — | Tu depósito, el pasillo, la escalera, la compuerta. Es la última estación habitada hacia el norte y el este | Ninguna: es segura | — |
| 1 | **La Plaza** | 10–20 min | La plaza redonda del Trabajo, las torres de la avenida, el vestíbulo del metro, el paso subterráneo, el primer patio y la plaza de la Estación con el tren de la evacuación | La Jauría (a veces), radiación leve | Latas, ropa, chatarra, paquetes de correos |
| 2 | **Los Bloques** | 20–40 min | Un microdistrito de jrushchovkas y bloques de 9 plantas, la Torre de 16, la escuela, dos guarderías, la farmacia y el universam de Mineros 7, los garajes y la playa | El Inquilino, la Jauría | Medicinas básicas, conservas, herramientas, objetos personales |
| 3 | **La Avenida y el Mercado** | 30–60 min | La avenida de ocho carriles hasta el puente, el Mercado Central, los Grandes Almacenes, el cine, el depósito de trolebuses, el socavón y el paso subterráneo del Mercado | Saqueadores (vigía), el Llamador, la Jauría | Ropa, comida, electrónica, baterías |
| 4 | **El Barrio Obrero** | 30–50 min | El Palacio de la Cultura, la panificadora, los baños, los bomberos con su torre, la comisaría, barracones de madera y la iglesia vieja junto a la vía | La Jauría, rondas de saqueadores | Cuerda, ganzúas, equipos de respiración, azúcar y sal |
| 5 | **La Zona Industrial** | 45–60 min | La fábrica y su búnker, la playa de vías, el puerto con sus grúas, el elevador de grano, la central térmica y el parque de carbón que aún arde | La guarida de los saqueadores, radiación alta al este, humo | Herramientas, combustible, componentes, máscaras |
| 6 | **El Parque y el Hospital** | Unos 60 min | Al otro lado del río: el parque con su colina, la torre de paracaídas y el estadio, y el Hospital Nº 3 con la Cruz Roja | El Inquilino, la segunda jauría | Medicinas valiosas, insulina |
| 7 | **El Centro** | 60–90 min | La ciudad vieja (fortaleza, catedral, mercaderes) y el centro estalinista (Escalinata, plaza Central, Casa de los Sóviets, teatro, hotel, circo, universidad); las casas de madera del barranco | Saqueadores (segunda guarida y vigía en la torre), el Inquilino del hotel, el Llamador del barranco | Material de laboratorio, máscaras militares, telas, conservas caseras |
| 8 | **La Zona Cero** | La gran expedición: de 60 minutos a 2 o 3 horas | Donde cayó la bomba. No se va al cráter: el destino es un edificio partido por la mitad que está muy cerca. Radiación extrema y aire irrespirable. Aquí está la respuesta sobre tu padre | Todas, más el entorno | Las mejores máscaras y filtros (búnker de la Planta) y el final del juego |
| — | **El río** | — | El Tumán helado, con cinco cruces: el tubo, el puente hundido, el hielo, el puente del ferrocarril y el túnel inundado | Hielo fino, vigías | — |
| — | **Los túneles** | Variable | Dos líneas de metro con estaciones muertas, galerías y colectores: rutas alternativas para llegar a otras zonas | Oscuridad, agua, el Llamador | — |

### 6.11 La gran expedición

Llegar a la Zona Cero, al edificio partido por la mitad junto al cráter, es el objetivo del juego y tiene que costar muchísimo. No se consigue en una salida improvisada, sino al final de la partida y tras mucha preparación. Según lo bien preparado que vayas, dura **de 60 minutos a 2 o 3 horas**:

- **Equipo**: la mejor máscara, muchos filtros, ropa de abrigo, pastillas antirradiación y todo lo que hayas ido consiguiendo.
- **Conocimiento**: tus mapas, las rutas que te sabes de memoria, los horarios de las patrullas y dónde viven las amenazas.
- **Refugios y escondites**: en salidas anteriores preparas tus propios refugios a lo largo del camino (ver [6.12](#612-refugios-hechos-a-mano)) y dejas en ellos provisiones (filtros, comida, vendas) para recogerlas durante la gran expedición. Los saqueadores también pueden encontrarlos.

### 6.12 Refugios hechos a mano

El juego no hace refugios por ti. **Casi cualquier sitio puede convertirse en uno, pero no todos serán seguros.** Tú decides dónde, con qué y cuánto ruido estás dispuesto a hacer.

- **Cómo se monta**: clavas tablas en puertas y ventanas, mueves cajas y muebles para bloquear la entrada, atas una puerta con cuerda, tapas las rendijas por donde se escapa la luz y cuelgas campanillas en el pasillo para saber si algo se acerca.
- **De qué depende que sea seguro**: cuántas entradas tiene y cómo de bien las has cerrado, de qué materiales, si se ve tu luz desde fuera, si el viento lleva tu olor y si está en el territorio de algo (un bloque con Inquilino nunca es buena idea).
- **El precio**: clavar hace mucho ruido y la vibración viaja por el edificio. Montar un refugio en el sitio equivocado puede atraer justo lo que querías evitar.
- **Para qué sirve**: descansar, dibujar el mapa con calma, curarte, esperar a que pase la noche o la ventisca y guardar provisiones para la gran expedición.
- **La ciudad lo recuerda**: los refugios siguen ahí en las salidas siguientes. Los saqueadores pueden encontrarlos y saquearlos, y lo que vive en la niebla puede forzarlos.

---

## 7. Las amenazas

Son pocas y de gran calidad. Cada una se trata como un pequeño proyecto propio: biología, sentidos, comportamiento, las señales que deja para que las anotes en tu cuaderno, y su propia animación y su propio sonido.

**Reglas:**

1. Ninguna sabe dónde estás si no te ha percibido.
2. Todas dejan señales antes de dejarse ver.
3. Ninguna se puede matar; todas se pueden entender.
4. También se enfrentan entre ellas, y eso se puede aprovechar.

### 7.1 La Jauría

- **Qué es.** Perros asilvestrados que la radiación ha deformado: más grandes de lo que deberían, con calvas y bultos. Cazan en manada, guiados por una hembra.
- **Dónde.** Avenidas, parques, descampados y patios grandes. De día y al atardecer.
- **Cómo perciben.** Sobre todo por el olfato, así que el viento decide. También por la vista (detectan el movimiento) y el oído.
- **Cómo cazan.** Te tantean desde lejos, te rodean y te cortan la huida. Si corres, te persiguen. Un rastro de sangre lo siguen sin descanso.
- **Señales.** Huellas y excrementos, huesos roídos, aullidos al atardecer, cuervos sobre un cadáver.
- **Cómo sobrevivir.** Avanzar con el viento de cara, no correr nunca delante de ellos, subir a un piso alto y cerrar la puerta, cruzar agua para cortar el rastro, sacrificar comida como cebo.
- **Rutina.** Caza al amanecer y al atardecer; de noche duerme en su madriguera (garajes, sótanos) y de día recorre su territorio.
- **Por qué da miedo.** Nunca está sola. Cuando ves un perro, los demás ya te están rodeando.

### 7.2 El Inquilino

- **Qué es.** Algo alto y delgadísimo, de articulaciones largas y piel pálida, casi ciego. Ocupa un edificio entero y lo convierte en su territorio. En la estación se dice que "ese bloque tiene inquilino".
- **Dónde.** Grandes bloques de viviendas, y también otros edificios grandes, como el hospital.
- **Cómo percibe.** Por las vibraciones que viajan por la estructura (pisadas, golpes, objetos que caen) y por el oído.
- **Cómo caza.** Se mueve por las tripas del edificio: el hueco del ascensor, los bajantes de basura, los conductos y las cámaras entre muros. Sale cerca de donde te ha sentido y espera.
- **Señales.** Arañazos dentro de las paredes, trampillas del bajante arrancadas, despensas vaciadas, polvo removido en las escaleras, un silencio repentino.
- **Cómo sobrevivir.** Escuchar las paredes con el estetoscopio, pisar suave, condenar trampillas con martillo y clavos, provocar vibraciones en otra planta (dejar caer algo pesado, dejar un despertador), entrar y salir por la fachada y los balcones con una cuerda.
- **Rutina.** No sale de su edificio. De día se queda quieto en los huecos; de noche recorre las plantas. Come lo que entra: perros, ratas, personas.
- **Por qué da miedo.** No está en la habitación: está en las paredes. Y oye cada paso que das en su edificio.

### 7.3 El Llamador

- **Qué es.** Del tamaño de un hombre, se mueve a cuatro patas, tiene la piel desnuda y gris y una garganta hinchada con la que imita sonidos que ha oído: alguien que pide ayuda, un bebé que llora, una tos, una radio mal sintonizada.
- **Dónde.** Pasos subterráneos, accesos al metro, sótanos y patios con eco. Sobre todo al anochecer.
- **Cómo percibe.** Por el oído, que tiene finísimo.
- **Cómo caza.** Atrae a sus presas hacia un sitio cerrado y espera a que entren. Aprende: imita también los sonidos de sus presas, incluidos los tuyos y las voces de los saqueadores.
- **Señales.** La llamada se repite idéntica, como una grabación. No hay huellas de personas, solo las suyas. Los restos se acumulan siempre en el mismo punto.
- **Cómo sobrevivir.** Reconocer la repetición, no acudir nunca, rodear su zona y lanzar algo para que se delate al moverse.
- **Rutina.** Nocturno. De día duerme en lo más hondo (sótanos, túneles); al anochecer sale a cazar.
- **Por qué da miedo.** Lo que oyes no siempre es lo que parece. La próxima vez que alguien pida ayuda de verdad, dudarás.

### 7.4 Los Saqueadores

- **Qué son.** Personas armadas, organizadas y con tanto miedo como tú. No tienen bandera ni nombre: viven de lo que encuentran y de lo que les quitan a otros.
- **Dónde.** Rutas de paso, farmacias, almacenes y campamentos en edificios fortificados.
- **Qué saben.** Solo lo que ven, lo que oyen o lo que un compañero les dice en voz alta. Y tú también puedes oírlo.
- **Cómo actúan.**
  - Patrullan y ponen vigías con prismáticos.
  - Investigan ruidos y cosas fuera de sitio: una puerta abierta, una marca de tiza, huellas recientes.
  - Buscan en grupo y cubren las salidas.
  - Recuerdan dónde te vieron y qué ha cambiado.
  - En las fases avanzadas del desarrollo: tienden emboscadas en los pasos obligados, ponen cebos (una mochila a la vista), colocan trampas y aprenden tus rutas habituales.
- **Señales.** Latas colgadas como alarma, hilos trampa, humo de campamento, voces, colillas, huellas de botas.
- **Cómo sobrevivir.** Observar sus rutinas con los prismáticos y el reloj, escuchar lo que dicen, evitar sus trampas (la navaja corta los hilos), despistarlos con ruidos o con marcas de tiza falsas y tener siempre una vía de escape.
- **Si te pillan, te matan.** No hay rendición posible.
- **Rutina.** Salen de día a saquear, cazar y patrullar; de noche se encierran en sus guaridas, con guardias y fuego.
- **Por qué dan miedo.** Piensan como tú. Y tienen armas.

### 7.5 Cuando se cruzan

- La Jauría ataca a los saqueadores: llevarla hacia un campamento puede abrirte paso… o cerrártelo.
- El Llamador imita las voces de los saqueadores, y también los atrae a ellos.
- El Inquilino no sale de su edificio. Es una frontera que ni los saqueadores se atreven a cruzar.

| Quién | Caza a | Evita a | Se pelea con |
|---|---|---|---|
| La Jauría | Fauna menor, personas solas, carroña | El Inquilino, la luz del fuego | Los saqueadores |
| El Inquilino | Todo lo que entra en su edificio | — (nunca sale) | Lo que entre |
| El Llamador | Perros y personas, de noche | La luz fuerte, los grupos grandes | — (embosca, no pelea) |
| Los Saqueadores | Perros (para comer), otros supervivientes | Los edificios con inquilino, la noche | La Jauría |
| Tú | Nadie | Todos | Nadie: no puedes matar |

### 7.6 El mundo vivo

Como en *Rain World*, la ciudad funciona sin ti. Nada espera a que llegues.

- **Rutinas.** Cada especie tiene su horario: de noche los saqueadores duermen en sus guaridas y la Jauría en su madriguera, mientras el Llamador sale a cazar; de día, al revés.
- **Necesidades.** Todos comen, descansan y se ponen a salvo. Un perro con hambre se arriesga más; un saqueador herido vuelve a la guarida.
- **Enfrentamientos.** Se cazan y se pelean entre ellos aunque no estés. Al volver a una zona puedes encontrar los restos de algo que pasó sin ti.
- **El mundo recuerda.** Los cadáveres, los campamentos que se mueven, el botín que se llevan otros y los refugios forzados quedan en el mapa.
- **Dos niveles de simulación.** Cerca de ti, todo se simula al detalle. Lejos, el mundo sigue en una versión abstracta (las zonas como un grafo y los encuentros resueltos sin dibujarlos), y al llegar lo encuentras tal cual.
- **Tú eres un organismo más.** Cada especie te trata como trata a los demás: presa, competidor o amenaza. Aprender sus horarios y sus relaciones es tu mejor herramienta.
- **Fauna menor** *(propuesta)*: ratas y cuervos. No atacan: son comida para otros y también señales (los cuervos marcan dónde hay un cadáver).

Tiene una fase propia en el plan ([Fase 4](#fase-4-el-mundo-vivo--tamaño-l)), antes del vertical slice, porque todas las amenazas se construyen encima.

### 7.7 Cómo se construye cada amenaza

1. **Ficha de diseño**: biología, sentidos, comportamiento y señales.
2. **Animación propia**: ciclos generados por código con movimiento "a saltos", como en el dibujo animado, más ajustes procedurales (pies que se apoyan en el suelo, cabeza que sigue el sonido).
3. **Sonido propio**: cada amenaza tiene una firma sonora reconocible.
4. **Tres escenarios de prueba** para cada una.
5. **Herramienta de depuración** que muestra lo que percibe y lo que sabe en cada momento.

---

## 8. Mundo y narrativa

- **Guerra atómica**: la Noche de la Caída de las Bombas, hace dos años. Sin año en el calendario y sin explicaciones largas.
- **Gobierno civil**: bajo tierra, la ciudad formó un gobierno civil en la red de túneles. No se profundiza en él, pero explica que las estaciones estén en buen estado, que haya orden y que el depósito pague impuesto.
- **Tumansk**: una ciudad soviética ficticia inspirada en Moscú, con avenidas anchas, microdistritos de bloques de paneles y un metro monumental y frío. Todo el texto del juego está en español, carteles incluidos, pero el diseño es soviético.
- **La ciudad cuenta su historia por capas**: la fortaleza sobre el río, el barrio de los mercaderes, el ferrocarril, la fábrica y su barrio obrero, el eje estalinista y los microdistritos. La Noche dejó su propia capa: la bomba en el nudo ferroviario, otra más lejos que tiró la autovía, los incendios y la evacuación hacia el metro. Ver [docs/CIUDAD.md](docs/CIUDAD.md).
- **Sin facciones** y **sin nombre de estación**.
- **Tu padre**: era stalker, enfermó, subió una última vez y no volvió. No sabes nada de él. En la superficie hay pocos rastros suyos, y ambiguos.
- **La historia se cuenta poco, y a través del entorno**: pisos abandonados, notas, fotos, objetos personales. No hay cinemáticas.
- **El objetivo de la partida**: llegar a la zona más lejana y saber qué le pasó a tu padre (ver [6.11](#611-la-gran-expedición)).

---

## 9. Dirección de arte: ilustración entintada

### 9.1 ¿Qué estilo usa Cat Mail Co.?

Pertenece al **3D estilizado** (*stylized* en inglés), una rama del **renderizado no fotorrealista** (NPR). En sus capturas se ve lo siguiente:

- Formas **robustas y algo exageradas**: estanterías gruesas, cajas con los bordes suavizados.
- **Colores planos con degradados suaves** y texturas sencillas, casi pintadas a mano, sin contornos marcados.
- **Ilustraciones 2D sobre objetos 3D**: sellos, etiquetas, pegatinas y mapas.
- **Luz cálida** de lámparas, con resplandor y sombras suaves.

### 9.2 Nuestro estilo

Partimos de esa base (formas robustas, calidez, ilustraciones sobre objetos) y le añadimos **tinta**, con un tono más adulto.

| Capa | Qué es | Cómo se hace en Godot 4 |
|---|---|---|
| Sombreado por bandas (*cel shading*) | 2 o 3 tonos por material, con rampas de color. Luz cálida, sombra fría | Shader `spatial` propio con función `light()` y una textura de rampa |
| Contorno de tinta | Líneas en siluetas y pliegues, de grosor variable y trazo irregular | Post-proceso a partir de profundidad y normales, en un rectángulo a pantalla completa ([D-008](docs/DECISIONES.md)), más casco invertido en personajes y objetos clave |
| Tramado | Sombras hechas con rayas, como un grabado. Más densas cuanto más oscuro y cuanto más miedo | Texturas de tramado (*tonal art maps*) mezcladas según la iluminación |
| Trazo vivo (*line boil*) | El contorno tiembla como en una animación dibujada a mano | Ruido animado a 4–12 fps, a saltos y no de forma continua |
| Papel y grano | Grano de papel sutil sobre toda la imagen y viñeta en los bordes; con mucha radiación, el grano se intensifica | Post-proceso final |
| Color por zona | Paletas limitadas y gradación propia de cada zona | Saturación, contraste y tinte por zona, interpolados en las transiciones ([D-011](docs/DECISIONES.md)) |
| Nieve y huellas | La nieve se acumula en lo que mira hacia arriba; las huellas quedan marcadas y la nieve que cae las borra | Shader según la orientación de la superficie, más decals de huellas, que también son datos para la IA |
| Niebla y ventisca | Niebla posterizada y nieve que cruza el aire | Niebla ligera, partículas y shader propio |
| Ilustraciones sobre objetos | Etiquetas, carteles, rótulos, envases | Nodos `Decal` y texturas generadas por código (SVG) |

### 9.3 Lenguaje de formas

- **Nada es perfectamente recto.** Las recetas de modelado añaden imperfección controlada: bordes un poco torcidos y grosores exagerados.
- **Biseles generosos** y normales suavizadas, para que el sombreado por bandas quede limpio.
- **Siluetas legibles**: cada objeto se reconoce por su sombra.
- **Arquitectura soviética**: bloques de paneles prefabricados, brutalismo y una estación de metro con mármol, columnas y lámparas de araña (de diseño propio). Es modular por naturaleza, ideal para generarla por código.
- **Personas**: proporciones robustas, ropa por capas (abrigos, bufandas, gorros de piel) y rostros 2D sobre modelos 3D, para que las expresiones sean claras y fáciles de animar.
- **Criaturas**: siluetas muy reconocibles, negros masivos y detalles que se descubren poco a poco.

### 9.4 Escenarios: reglas de construcción

- **Cada espacio tiene una historia visible**: quién vivía ahí y qué pasó.
- **Hitos para orientarse**, imprescindibles para dibujar tus mapas: una torre de radio, un tranvía volcado, la cúpula del mercado, las chimeneas de la fábrica.
- **Detalle de ilustración**: muchos objetos pequeños con carácter (tendederos, buzones, carteles, macetas secas) en lugar de texturas complejas.
- **Composición por planos**, como una ilustración: primer plano oscuro, plano medio iluminado y fondo perdido en la niebla.
- **La luz guía**: la luz cálida atrae; la luz fría, o la ausencia de luz, avisa de peligro.
- **Verticalidad**: azoteas, escaleras y sótanos que abren rutas distintas.
- **Lógica de ciudad**: cada manzana tiene sentido (por dónde se entraba, dónde estaban las tiendas, las calderas, los garajes) y los interiores son coherentes con su exterior.
- **Un depósito que crece**: del abandono a la vida, mejora a mejora.

### 9.5 Paletas

**Depósito: "Ámbar y madera"**

| Uso | Color | Hex |
|---|---|---|
| Papel y cartón | Crema | `#F2E6CF` |
| Tinta | Negro violáceo | `#1B1A22` |
| Bombilla | Ámbar | `#E8A33D` |
| Cajas | Terracota | `#C2603F` |
| Madera | Nogal | `#8A5A3B` |
| Azulejo de la estación | Verde azulado | `#2F6F73` |
| Lo importante | Rojo | `#C8323C` |
| Señalética | Cobalto | `#2D4A8A` |

**Superficie: "Ceniza y óxido"**

| Uso | Color | Hex |
|---|---|---|
| Nieve sucia | Blanco hueso | `#D9D6CC` |
| Ceniza | Gris | `#9A9A94` |
| Hormigón | Gris cálido | `#7D7F7A` |
| Óxido | Marrón rojizo | `#8E4A2F` |
| Cielo | Gris azulado | `#A7B1B4` |
| Sombra | Azul pizarra | `#2A3440` |
| Vegetación muerta | Oliva apagado | `#6B6A4A` |
| Señales de peligro | Amarillo | `#D9A623` |

Regla: **el rojo** se reserva para lo importante (peligro, confirmaciones, lo urgente).

### 9.6 Parámetros por estado (punto de partida para la Fase 1)

| Parámetro | Depósito | Superficie | Pánico |
|---|---|---|---|
| Trazo vivo | 4 fps, muy sutil | 8 fps | 12 fps, amplio |
| Grosor del contorno (a 1080p) | 1,5–2 px | 2–3 px | 3–5 px, roto |
| Tramado | Solo en sombras profundas | En sombras medias | Invade la imagen desde los bordes |
| Saturación | 100 % | 55 % | 30 % |
| Grano | Sutil | Visible | Intenso |

### 9.7 Referencias (inspiración, no copia)

- **Cat Mail Co.**: calidez, tactilidad, ilustraciones sobre objetos, mobiliario robusto.
- **Andréi Tarkovski, *Stalker* (1979)**: la quietud, el silencio y la amenaza que no se ve.
- **Fotografía de Prípiat y de los microdistritos soviéticos**: interiores abandonados, escala, materiales.
- **Estaciones del metro de Moscú**: mármol, columnas, lámparas de araña, mosaicos.
- **Carteles y diseño gráfico soviético**: señalética, tipografía, composición de la interfaz.
- **Grabado y xilografía**: sombras hechas de líneas.
- **Mike Mignola**: negros masivos y siluetas para el terror.
- ***Rain World***: no por el arte, sino por su ecosistema, que funciona sin el jugador.

---

## 10. Interfaz: sin cajas de texto

### 10.1 Reglas

1. **Todo es un objeto.** Si algo hay que mostrarlo, es papel, cartón, un instrumento o una parte de tu cuerpo.
2. **Nunca un rectángulo con texto encima.** El texto vive en papeles con textura, escrito a mano o a máquina.
3. **Iconos dibujados**, con el mismo grosor de trazo que el mundo 3D.
4. **Animación con peso**: los papeles se deslizan y se asientan, las hojas pasan, los sellos golpean.
5. **El tiempo no se detiene**: abrir el cuaderno o la mochila en la superficie lleva su tiempo. Solo el menú de opciones pausa el juego, y únicamente en partidas de un jugador.
6. **Accesible sin romper la estética**: tamaño de texto ajustable, texto "limpio" para dislexia, subtítulos en tiras de papel, trazo vivo reducible y colores siempre acompañados de forma.

### 10.2 Qué es cada cosa

| Función | Objeto |
|---|---|
| Menú principal | El depósito de noche, con la lámpara encendida y tu cuaderno sobre la mesa. Apagar la lámpara es salir del juego |
| Nueva partida | Firmar con tu nombre la escritura del depósito |
| Guardar | Automático al dormir |
| Opciones | La radio del depósito: diales para el volumen, el brillo y la sensibilidad |
| Mapas, notas y planes | Tu cuaderno. No hay otro mapa |
| Planificar | El tablero de la pared: páginas, chinchetas e hilo |
| Encargos | Fichas en el tablón de corcho |
| Cuentas e impuesto | El libro de cuentas y los recibos con el sello **PAGADO** |
| Precios | Etiquetas de cartón atadas con cordel |
| Inventario | La mochila abierta, en 3D |
| Hora | El reloj de pulsera |
| Radiación | El dosímetro: la aguja y los chasquidos |
| Aire | La máscara: se empaña, se agrieta, la respiración cambia |
| Salud, miedo y hambre | Tus manos, tu respiración, tu estómago |
| Avisos de la estación | Una nota que alguien desliza bajo la persiana |
| Interactuar | Un punto de lápiz que se convierte en un pequeño icono dibujado (mano, lupa, ganzúa) |
| Fin de la partida | El depósito cerrado, con un cartel escrito a mano |

### 10.3 Tipografía

Elegidas en la Fase 1 (F1-13). Las cuatro tienen licencia OFL, español completo y cirílico. Están en `assets/fonts/` con su licencia, y la prueba de legibilidad está en [docs/ESTILO.md](docs/ESTILO.md).

| Uso | Familia | Tamaño mínimo a 1080p |
|---|---|---|
| **Manuscrita**: tu cuaderno, notas, etiquetas, fichas | *Caveat* (normal y negrita). Más adelante, otra letra distinta para cada cliente | 30 px |
| **Máquina de escribir**: recibos, impresos, la administración | *PT Mono* | 20 px |
| **Rotulación**: carteles, sellos, cabeceras, de estilo soviético y siempre en español | *Oswald* | 20 px |
| **Texto**: textos largos y opciones | *PT Sans* | 18 px |

![Las primeras piezas de interfaz](docs/capturas/fase1_interfaz.jpg)

---

## 11. Audio

- **Depósito**: la radio, el murmullo de la estación, la estufa, herramientas, papel, cartón, cordel.
- **Superficie**: viento, nieve que cruje, estructuras que gimen, el dosímetro, tu respiración dentro de la máscara, perros a lo lejos. **El silencio también es una herramienta.**
- **Amenazas**: cada una tiene su firma sonora. El Llamador, en concreto, es puro diseño de sonido.
- **Técnica**: sonido 3D con oclusión, reverberación según el tipo de espacio y propagación del sonido por la ciudad. Lo que tú oyes, ellos también lo oyen: el mismo sistema alimenta a la IA. La mezcla cambia según el miedo.
- **Música y fuentes**: está por decidir. El criterio es lo que dé más calidad y encaje mejor con el juego: un compositor por encargo, librerías profesionales libres de derechos, foley grabado por nosotros, o una combinación.

---

## 12. Cooperativo

- **De 2 a 4 jugadores.** Comparten un único depósito (dinero, estanterías y encargos); cada uno tiene su mochila y su cuaderno.
- **Compartir mapas**: se pueden copiar páginas del cuaderno de otro (lleva su tiempo) o pegarlas en el tablero de la pared.
- **Más gente significa más ruido y más huellas**, así que la dificultad sube sola.
- **Muerte**: quien muere queda fuera. La partida sigue mientras quede alguien vivo; si mueren todos, se pierde.
- **Voz**: por decidir. La voz por proximidad sería ideal para el terror, pero requiere trabajo extra.
- **Técnica**: el juego funciona siempre con un anfitrión. En una partida de un jugador, el anfitrión simplemente no tiene invitados, así que todo se construye en red desde el primer día y nada hay que rehacer después. Conexión directa por IP o red local; para jugar por internet sin abrir puertos se valorará un servicio de relé.

---

## 13. Arquitectura técnica (Godot 4)

### 13.1 Decisiones técnicas

- **Godot 4** con el renderer **Forward+** (Vulkan). La versión exacta se fija en la Fase 0 y no se cambia sin motivo.
- **GDScript con tipado estático** obligatorio. C++ (GDExtension) solo si algún sistema lo necesita por rendimiento.
- **Red desde el primer día**: la API multijugador de Godot sobre ENet. El anfitrión tiene la autoridad sobre el mundo (IA, objetos, puertas, inventarios) y cada jugador controla su propio movimiento, para que no haya retraso.
- **Todo lo que existe en el mundo tiene un identificador**, se puede guardar y se puede replicar.
- **Los datos son recursos** (`Resource` guardados como `.tres`): objetos, encargos, clientes, herramientas y amenazas. Se crean y se editan como texto.
- **Muerte permanente**: un solo archivo de partida, que se borra al morir.

### 13.2 Estructura del repositorio

```text
/
├── project.godot
├── addons/                  # plugins (tests, utilidades)
├── assets/
│   ├── models/              # .glb generados (no se editan a mano)
│   ├── textures/            # rampas, tramados, papel, ruido
│   ├── shaders/             # toon, contorno, tramado, nieve, niebla, papel
│   ├── materials/
│   ├── ui/                  # SVG y PNG generados
│   ├── fonts/
│   └── audio/               # music/, ambience/, sfx/, ui/
├── data/                    # recursos .tres: el contenido del juego
│   ├── items/               # fichas de los objetos
│   └── ciudad/              # el plano de la ciudad (plano.json, relieve.png y suelo.png), generado
├── scenes/                  # depot/, station/, surface/, ui/, actors/, props/, debug/
├── scripts/
│   ├── core/                # autoloads y utilidades
│   ├── net/                 # sesión, anfitrión, replicación
│   ├── actors/              # jugador, avatar, manos de primera persona
│   ├── interaction/         # componentes Interactable
│   ├── depot/               # objetos, banco, descontaminación, tienda, economía
│   ├── surface/             # la ciudad (plano, sectores, maqueta), jugador, herramientas, cuaderno…
│   ├── ai/                  # percepción, conocimiento, criaturas, humanos
│   └── ui/
├── tools/
│   ├── blender/             # recetas de modelos (bpy) → .glb
│   ├── svg/                 # generadores de ilustración 2D (rough.js)
│   ├── textures/            # generadores de texturas (numpy, Pillow)
│   ├── ciudad/              # el plano de la ciudad: datos, validación y planos de desarrollo
│   └── capture/             # capturas automáticas para revisión
├── tests/
└── docs/                    # GDD vivo, guía de estilo, registro de decisiones
```

### 13.3 Sistemas principales

| Sistema | Responsabilidad |
|---|---|
| `EventBus` | Señales globales |
| `GameState` | Día, rublos, deuda, encargos, banderas |
| `SaveSystem` | Guardado único con muerte permanente, incluido el estado del mundo (atajos, puertas, marcas de tiza, huellas recientes) |
| `NetSession` | Anfitrión e invitados, replicación, autoridad |
| `SceneRouter` | Cambios de escena con transición dibujada |
| `StyleDirector` | Parámetros del estilo en tiempo real (trazo, tramado, paleta, grano) según la zona, el miedo y la radiación |
| `AudioDirector` | Ambiente, música, mezcla dinámica, oclusión y propagación |
| `TimeAndWeather` | Hora del día, luz, nieve, viento, ventisca |
| `Interaction` | Raycast, componentes `Interactable`, coger e inspeccionar objetos físicos |
| `ItemSystem` | Objetos: categoría, peso, forma en la cuadrícula, estado, contaminación, valor |
| `Shop` | Mostrador, clientes, precios, encargos, impuesto |
| `Backpack` | Cuadrícula, peso, ruido, fragilidad |
| `Notebook` | Páginas, trazos vectoriales, símbolos, notas; copiar y compartir |
| `Perception` | Vista, oído, olfato con viento y vibración por la estructura |
| `Knowledge` | Memoria de cada agente y comunicación entre agentes (siempre audible) |
| `CreatureAI` | Comportamiento de la Jauría, el Inquilino y el Llamador |
| `HumanAI` | Saqueadores: patrullas, investigación, búsqueda en grupo y, más adelante, planificación |
| `Tracks` | Huellas, rastros de olor y de sangre |
| `Survival` | Hambre, heridas, radiación, aire, frío, miedo |
| `WorldSim` | El mundo vivo: reloj, necesidades, rutinas, territorios, relaciones entre especies y simulación en dos niveles |

### 13.4 Inteligencia artificial

- **Percepción → conocimiento → decisión.** Nadie decide nada a partir de información que no haya percibido o que no le hayan comunicado.
- **Criaturas**: máquinas de estados con sentidos propios (olfato con viento para la Jauría, vibración por la estructura del edificio para el Inquilino, oído para el Llamador).
- **Humanos**: IA por utilidad para las decisiones del momento y un planificador (GOAP o HTN, se decide en la Fase 7) para emboscadas, cebos y trampas.
- **Puntos tácticos** marcados en los niveles: coberturas, miradores, pasos obligados, lugares de emboscada.
- **Prueba de justicia automática**: cualquier decisión de la IA que tenga que ver con tu posición debe poder rastrearse hasta un estímulo percibido. Si no se puede, el test falla.
- **Visualización de depuración**: lo que ve, oye, huele y sabe cada agente, en tiempo real.
- **Mundo vivo** (`WorldSim`): cada agente tiene necesidades y una rutina, y vive en una de dos simulaciones. Cerca de los jugadores, la completa: física, percepción y animación. En el resto del mapa, una abstracta y barata: las zonas son nodos de un grafo, los agentes se mueven entre ellos y los encuentros se resuelven con reglas. Al acercarse un jugador, el agente abstracto se convierte en uno completo en el mismo estado. El anfitrión simula todo; los invitados reciben lo que tienen cerca.

### 13.5 El cuaderno

- Los trazos se guardan como **vectores** (listas de puntos suavizados): ocupan poco, se guardan en la partida y se envían por red al copiar páginas.
- Se dibujan sobre la textura de la página del cuaderno 3D, con un shader de grafito.
- Los símbolos funcionan como pequeños sellos; las notas usan la tipografía manuscrita.

### 13.6 Pipelines de producción de arte

Todo se genera por código y todo queda versionado.

- **3D**: recetas en Python ejecutadas con **Blender 5 como módulo** (`bpy`, que se instala con pip). Producen geometría con biseles e imperfección controlada, colores por vértice, UVs, colisiones y LODs, y la exportan a `.glb`. Godot la importa sola: un script post-importación asigna los materiales y las colisiones según el sufijo del nombre. Hay recetas de props (cajas, estanterías, herramientas, botín), un **kit modular de arquitectura soviética** (paneles, ventanas, balcones, escaleras, huecos de ascensor, bajantes, túneles), personas y criaturas.
- **2D**: generadores SVG en Node con **rough.js**, que da un aspecto dibujado a mano. Producen etiquetas, envases, carteles, iconos y papeles. Godot importa SVG directamente; se usa PNG cuando haga falta.
- **Texturas**: scripts de Python (numpy y Pillow) para el grano de papel, los tramados, las rampas y el ruido. Además, horneado en Blender (oclusión y curvatura) para conseguir bordes gastados con aspecto pintado.
- **Revisión visual**: cada cambio visual viene acompañado de **capturas automáticas** de escenas de prueba, para que puedas revisar el aspecto sin abrir el motor.

### 13.7 Calidad

- `gdlint` y `gdformat` (de gdtoolkit) en cada cambio.
- Tests unitarios sin pantalla, con un ejecutor propio (`tests/run_tests.gd`, ver [D-002](docs/DECISIONES.md)) para la lógica: economía, mochila, percepción, guardado.
- Pruebas de red automáticas: dos instancias conectadas ejecutan el mismo escenario y se comparan.
- GitHub Actions: lint, tests y builds de Windows y Linux como artefactos descargables.

### 13.8 Rendimiento objetivo

| Equipo | Resolución | Objetivo |
|---|---|---|
| Ryzen 7 8700G con su gráfica integrada (Radeon 780M), sin gráfica dedicada | 1080p | 60 fps, con escalado FSR 2 si hace falta |
| PC con gráfica dedicada media | 1080p–1440p | 60 fps o más |

La gráfica integrada es el objetivo principal. Para conseguirlo: iluminación horneada en los interiores, nada de iluminación global en tiempo real, sombras dinámicas solo para el sol y la linterna, niebla ligera y un presupuesto de milisegundos fijo para cada efecto de post-proceso. El escalado (nativo, FSR o FSR 2) ya está en los ajustes desde la Fase 0.

---

## 14. Plan por fases

```mermaid
flowchart LR
    F0["Fase 0<br/>Cimientos"] --> F1["Fase 1<br/>Prueba de Tinta"]
    F1 -->|estilo aprobado| F2["Fase 2<br/>Depósito jugable"]
    F1 -->|estilo aprobado| F3["Fase 3<br/>Superficie jugable"]
    F3 --> F4["Fase 4<br/>El mundo vivo"]
    F2 --> F5["Fase 5<br/>Los primeros días<br/>(vertical slice)"]
    F4 --> F5
    F5 --> F6["Fase 6<br/>Producción (alfa)"]
    F6 --> F7["Fase 7<br/>Saqueadores tácticos"]
    F7 --> F8["Fase 8<br/>Pulido (beta)"]
    F8 --> F9["Fase 9<br/>Versión 1.0"]
```

Cada fase tiene un **objetivo**, unas **tareas** (con un ID para seguirlas en la [Hoja de Desarrollo](#15-hoja-de-desarrollo)), un **entregable** y un **criterio de salida**. No se pasa a la fase siguiente sin cumplir el criterio. **Todo se construye en red desde la Fase 0**, aunque se juegue en solitario.

### Fase 0: Cimientos · tamaño S

**Objetivo**: un proyecto que arranca en red, pipelines que producen assets sin pasos manuales y verificación automática.

- [x] **F0-01** Instalar Godot 4.7.2 en el entorno de desarrollo y en CI.
- [x] **F0-02** Crear el proyecto: Forward+, estructura de carpetas, capas de física y de render con nombre, mapa de controles (teclado y ratón, y mando).
- [x] **F0-03** Convenciones: `snake_case` para archivos, `PascalCase` para clases, tipado estático obligatorio, formato de commits y plantilla de PR con capturas.
- [x] **F0-04** Autoloads base, como esqueletos con tests: `EventBus`, `GameState`, `SaveSystem`, `SceneRouter` y `Settings`.
- [x] **F0-05** `NetSession`: el juego arranca siempre como anfitrión; escena de prueba con dos instancias conectadas por ENet.
- [x] **F0-06** Pipeline 3D: Blender 5 (`bpy`) y una receta de ejemplo → `.glb` → importación automática con materiales y colisión.
- [x] **F0-07** Pipeline 2D: generador SVG con rough.js (una etiqueta de ejemplo).
- [x] **F0-08** Pipeline de texturas: papel, tramado y rampa de ejemplo.
- [x] **F0-09** Capturas automáticas de escenas, renderizadas sin pantalla, para la revisión visual.
- [x] **F0-10** CI en GitHub Actions: lint, tests, prueba de red y builds de Windows y Linux.
- [x] **F0-11** Carpeta `docs/`: GDD vivo (este README se divide cuando crezca), guía de estilo y registro de decisiones.

**Entregable**: *Hola, Tumansk*: una caja generada por receta, importada sola, que dos instancias conectadas ven moverse a la vez.
**Criterio de salida**: un asset va de la receta al juego sin tocar nada a mano; las dos instancias están sincronizadas; la CI está en verde.
**Estado**: ✅ terminada. Tests y prueba de red en verde. Captura: [docs/capturas/fase0_hola_tumansk.png](docs/capturas/fase0_hola_tumansk.png).

### Fase 1: La Prueba de Tinta (puerta de estilo) · tamaño M

**Objetivo**: fijar y aprobar el aspecto final antes de producir contenido. Es la fase más importante, porque todo lo demás se construye encima.

- [x] **F1-01** Shader de sombreado por bandas con rampas por material: luz cálida, sombra fría y luz de borde.
- [x] **F1-02** Contorno por post-proceso (profundidad y normales), con grosor variable y trazo irregular. Se hace con un rectángulo a pantalla completa ([D-008](docs/DECISIONES.md)).
- [x] **F1-03** Contorno por casco invertido para objetos clave, personas y criaturas (`InkHull`: normales suavizadas, grosor en píxeles, trazo vivo y miedo). *(En los protagonistas, con `assets/shaders/casco.gdshader`, que también resalta lo que se puede coger.)*
- [x] **F1-04** Tramado en las sombras (*tonal art maps*), con densidad controlable.
- [x] **F1-05** Trazo vivo a saltos (4, 8 y 12 fps), controlado por `StyleDirector`.
- [x] **F1-06** Papel, grano, viñeta y gradación de color por zona (por parámetros en lugar de LUT, [D-011](docs/DECISIONES.md)).
- [x] **F1-07** Nieve acumulada, huellas, niebla y ventisca (huellas de bota y de perro como calcomanías; ventisca con niebla cerrada y ráfagas).
- [x] **F1-08** Kit inicial de props por receta: 57 modelos. En el depósito: la sala, cajas de cartón y de madera, estantería metálica, banco de trabajo, lámpara de taller, persianas, bidón, cubo, botellas, lata, escoba, báscula, máscara, dosímetro y linterna (las telarañas son láminas con un SVG). En el exterior: bloques de paneles con daños (ventanas quemadas, paneles caídos, balcones desplomados), escombros, coches, farolas, postes con cables, árboles, columpio, contenedor, banco de parque y quiosco; el suelo nevado, las ruinas del horizonte y la Zona Cero. *(Además, adelantados para la Fase 2: estufa, radio, catre, mostrador y pila de descontaminación; y para la Fase 3: cuaderno (cerrado y abierto), lápiz, brújula, prismáticos, linterna de dinamo, martillo, palanca, cizalla, cuerda, tablón, navaja y despertador. Sus piezas móviles, en [DESARROLLO.md](docs/DESARROLLO.md#piezas-móviles).)*
- [x] **F1-09** Diorama A: *El depósito*, en dos estados (abandonado y limpio), con sus rincones: el mostrador con la báscula tras la persiana, el almacén, el banco de trabajo con el cuaderno, el catre y la estufa, y la pila de descontaminación. Aparte, la mesa del equipo, con cada pieza y su etiqueta.
- [x] **F1-10** Diorama B: *Un patio de Los Bloques bajo la nieve*, de día, al anochecer y de noche, con el cielo pintado y la Zona Cero en el horizonte.
- [x] **F1-11** Panel de depuración (F1 en el visor) para cambiar en vivo el miedo, la radiación, la hora (interpolada entre día, anochecer y noche), el clima, la linterna, el trazo reducido y el estilo de zona.
- [x] **F1-12** Primeras piezas de interfaz en el estilo final: una página de cuaderno con un mapa dibujado (sale del plano de la ciudad), una etiqueta de precio, un recibo con sello y una ficha de encargo.
- [x] **F1-13** Selección de tipografías (Caveat, PT Mono, Oswald y PT Sans) y prueba de legibilidad.
- [x] **F1-14** Guía de estilo con los parámetros definitivos, más capturas y un [vídeo corto](docs/capturas/fase1_dioramas.mp4) de 33 segundos con los dioramas.
- [x] **F1-15** Plano completo de la ciudad: calles, manzanas, cada edificio, relieve, subsuelo, amenazas, peligros y rutas, como datos validados y cuatro hojas de desarrollo ([docs/CIUDAD.md](docs/CIUDAD.md)).

**Entregable**: dos dioramas a calidad final y la guía de estilo con los valores fijados.
**Criterio de salida**: **tú apruebas el estilo**. Si no convence, se itera aquí; nunca se produce contenido sobre un estilo sin aprobar.
**Estado**: 🟨 todas las tareas hechas; falta tu aprobación final del estilo. Revisión 1: aprobados el contorno, el tramado y los colores cálidos del depósito; el exterior estaba demasiado blanco y pálido, sin ambiente posapocalíptico, y el cielo no podía ser negro. Revisión 2: el exterior ya transmite la sensación; la noche, mucho más oscura, y el anochecer, algo más contenido. Cierre: contorno de casco, huellas y ventisca, el kit completo de modelos (con el equipo y los muebles de la rama de modelos), el panel de depuración, las piezas de interfaz, las tipografías, el vídeo y el plano de la ciudad ([docs/ESTILO.md](docs/ESTILO.md), [docs/CIUDAD.md](docs/CIUDAD.md)).

### Fase 2: El Depósito jugable · tamaño L

**Objetivo**: que trabajar en el depósito sea un placer táctil, de principio a fin.

- [ ] **F2-00** Los protagonistas: el chico y la chica, con esqueleto, animaciones (reposo y caminar, con y sin carga), cara dibujada con 8 expresiones, color por jugador y manos de primera persona con los dedos articulados. *(Hechos; segunda pasada tras tu revisión del tono, pendiente de tu visto bueno.)*
- [x] **F2-01** Controlador en primera persona, versión depósito: tranquila y sin estamina.
- [x] **F2-02** Interacción: raycast, componentes `Interactable` y resaltado dibujado (el punto de lápiz se convierte en una mano y el objeto gana un contorno de tinta).
- [x] **F2-03** Física de objetos: coger, girar, inspeccionar, soltar. El peso se nota: lo pesado tarda en seguirte, cuelga más bajo, te frena y se te cae si lo arrastras contra algo. Las manos agarran lo que llevas lo mires como lo mires: por las esquinas de una caja, por los costados de un bidón y con una sola mano lo que cabe en ella; lo grande se lleva más lejos y más bajo para que no tape la vista. Lo que llevas nunca se mete en el cuerpo ni en la cámara, ni se atraviesa al andar contra una pared; con algo grande en las manos no se puede mirar tan abajo.
- [x] **F2-04** Modelo de datos de los objetos: categoría, peso, forma en la cuadrícula, estado, contaminación, fragilidad y valor. *(10 fichas en `data/items/`.)*
- [ ] **F2-05** El primer día: telarañas, barrer, fregar, basura, cajas del antiguo dueño, bombilla, persiana atascada.
- [ ] **F2-06** Dosímetro y descontaminación: lavar, cepillar, embolsar.
- [ ] **F2-07** Banco de trabajo con reparaciones sencillas (minijuegos táctiles).
- [ ] **F2-08** Báscula, etiquetas de precio (escribir y atar) y clasificación en estanterías.
- [ ] **F2-09** Mostrador: un cliente; compra, venta y regateo sencillo.
- [ ] **F2-10** Tablón de encargos y libro de cuentas.
- [ ] **F2-11** Impuesto diario y comida (el puesto de al lado).
- [ ] **F2-12** El trozo de estación que se recorre: pasillo, puesto vecino, tablón de avisos y escalera mecánica.
- [ ] **F2-13** Respuesta táctil: sonidos, polvo y microanimaciones.
- [ ] **F2-14** Todo sincronizado: dos jugadores pueden trabajar a la vez en el depósito. *(Lo hecho hasta ahora ya lo está: los jugadores se ven, cada uno con su color, y los objetos los mueve el anfitrión. Lo comprueba una prueba con dos instancias.)*

**Entregable**: el depósito, del primer día sucio a la primera venta.
**Criterio de salida**: se juega todo el recorrido sin una sola caja de texto, y lo prueban 2 o 3 personas: "¿da gusto?".
**Estado**: 🟨 en curso. Ya se puede andar por el depósito, coger y dejar cosas, solo o con otro jugador. 38 tests y dos pruebas de red en verde. Falta todo lo que convierte eso en un trabajo: limpiar, procesar el botín, vender, los encargos, el impuesto y el trozo de estación.

### Fase 3: La Superficie jugable · tamaño L

**Objetivo**: una salida corta en la que planificar sirva y la Jauría dé miedo de verdad.

- [ ] **F3-01** Controlador de superficie: agacharse, asomarse, correr con aliento; ruido según el suelo, la postura y el peso.
- [ ] **F3-02** Visibilidad: luz, sombra, silueta y movimiento determinan cuánto se te ve.
- [ ] **F3-03** Mochila en cuadrícula y cinturón de 3 huecos. Abrirla en la superficie es lento.
- [ ] **F3-04** **El cuaderno**: dibujar a mano (lápiz, goma, regla, colores, símbolos, notas), con trazos vectoriales que se guardan.
- [ ] **F3-05** Instrumentos: brújula, podómetro, reloj y prismáticos.
- [ ] **F3-06** Herramientas de acceso: ganzúas, palanca, cuerda y cizalla.
- [ ] **F3-07** Distracciones: lanzables y despertador.
- [ ] **F3-08** Tiza: marcas persistentes.
- [ ] **F3-09** Percepción común (vista, oído, olfato con viento) con su herramienta de depuración.
- [ ] **F3-10** **La Jauría**, completa: manada, líder, tanteo, rodeo, persecución, rastro de olor y de sangre, cebo.
- [ ] **F3-11** Miedo: manos, linterna y trazo que tiemblan; respiración; estilo que reacciona.
- [ ] **F3-12** Heridas básicas: mordeduras y sangrado.
- [ ] **F3-13** Audio: oclusión, reverberación, ambiente dinámico, nieve.
- [ ] **F3-14** **Zona 1, La Plaza**: primero con geometría provisional y después estilizada, con al menos 3 rutas a cada objetivo.
- [x] **F3-15** **Maqueta automática de la ciudad**: un generador en Godot lee `data/ciudad/plano.json` y levanta la ciudad entera en volúmenes sencillos (relieve, calles, edificios a su altura, escombros). Sirve para probar recorridos, vistas, sectores de carga y rendimiento antes de construir. *(Hecha: `scenes/debug/maqueta_ciudad.tscn`, con recorridos de las rutas, hitos a la vista, prueba de rendimiento y 48 sectores con dos niveles de detalle; ver [CIUDAD.md](docs/CIUDAD.md#15-la-maqueta).)*
- [ ] **F3-16** Kit modular de arquitectura soviética para los tipos del plano (jrushchovka, bloque de 9 plantas, casa estalinista), con daños por nivel e interiores de serie. *(Hechos los exteriores de las 138 viviendas del plano, en cuatro familias, con sus daños y los falsos interiores que se ven por las ventanas, y los tres primeros edificios singulares: el vestíbulo del metro y el Edificio Partido, con su interior, y la Casa de los Sóviets con su torre; ver [DESARROLLO.md](docs/DESARROLLO.md#el-kit-de-arquitectura-f3-16). Faltan los interiores de serie que se recorren, el resto de los sitios clave y llevarlos a la maqueta.)*
- [ ] **F3-17** **Red de tránsito de la ciudad** en 3D: calzadas, aceras, bordillos, plazas, sendas, camino, escaleras y el tablero del puente, con muros, pretiles, pasos de cebra, tapas y sumideros, encajados en el relieve y con colisión que se sube andando. *(Hecho en la maqueta todo lo que se pisa y las vías del tren y del tranvía, con la estación, la playa de vías, los desvíos, los topes y los pasos a nivel, y los modelos de detalle de las tapas, los sumideros y las traviesas: ver [CIUDAD.md](docs/CIUDAD.md#16-la-red-de-tránsito). Todo roto como debe estar (el firme levantado en placas, socavones sobre lo que reventó debajo, escombros, basura y farolas caídas, grietas, baches, tapas abiertas o robadas, bordillos que faltan o se han movido, pintura a trozos, óxido y matojos): ver [CIUDAD.md](docs/CIUDAD.md#17-la-superficie-rota). Falta el cruce del tranvía con el apartadero de la fábrica.)*

**Entregable**: una salida de 10 a 20 minutos: subir por la escalera, llegar a un objetivo y volver.
**Criterio de salida**: en las pruebas, los jugadores planifican antes de salir, dibujan su mapa, usan al menos dos rutas distintas y ninguna muerte se siente injusta.
**Estado**: 🟨 empezada por la ciudad: F3-15 hecha, F3-16 con los exteriores de las viviendas hechos y F3-17 (la red de tránsito) casi, a falta de tu revisión. La maqueta es geometría provisional y no depende del estilo, así que se ha adelantado mientras se aprueba la Fase 1; los edificios del kit siguen el estilo de la Fase 1 tal como está.

### Fase 4: El mundo vivo · tamaño L

**Objetivo**: que la ciudad funcione sin el jugador, como en *Rain World*. Lo que pasa ahí fuera no depende de que estés mirando: tú eres un organismo más. Va antes del vertical slice porque todas las amenazas se construyen encima de este sistema.

- [ ] **F4-01** Reloj del mundo: amanecer, día, anochecer y noche, compartido por todos los agentes.
- [ ] **F4-02** Agentes con necesidades (comer, descansar, ponerse a salvo) y rutinas de día y de noche.
- [ ] **F4-03** Territorios, guaridas y madrigueras: dónde duerme cada uno y por dónde se mueve.
- [ ] **F4-04** Relaciones: quién caza a quién, quién evita a quién, carroña, peleas y huidas (ver [7.5](#75-cuando-se-cruzan)).
- [ ] **F4-05** Simulación en dos niveles: completa cerca del jugador y abstracta en el resto del mapa (las zonas son un grafo y los encuentros se resuelven sin dibujarlos).
- [ ] **F4-06** Paso sin costuras entre los dos niveles: lo que estaba pasando "en abstracto" aparece tal cual al llegar.
- [ ] **F4-07** Rastros del mundo: cadáveres, restos, campamentos que se mueven, botín que se llevan otros, refugios forzados.
- [ ] **F4-08** El jugador como un organismo más: cada especie lo trata como presa, competidor o amenaza, igual que a los demás.
- [ ] **F4-09** Herramienta de observación: un mapa de depuración con todos los agentes y un registro de sucesos.
- [ ] **F4-10** Pruebas de estabilidad: el mundo simula 30 días sin el jugador sin que ninguna especie desaparezca ni se descontrole, y en ese tiempo pasan cosas.
- [ ] **F4-11** Red: el anfitrión simula el mundo; cada invitado recibe lo que tiene cerca.

**Entregable**: las zonas 1 y 2 funcionando solas durante días: la Jauría caza y duerme en su madriguera, unos saqueadores básicos salen a saquear y vuelven a su guarida, y todo queda en el registro.
**Criterio de salida**: al entrar en una zona, lo que ves cuadra con lo que el registro dice que pasó, y en las pruebas los jugadores ven peleas y rutinas que no han provocado.

### Fase 5: Los primeros días (vertical slice) · tamaño XL

**Objetivo**: el juego completo en miniatura, a calidad final.

- [ ] **F5-01** El día completo: depósito → planificación → subida → salida → regreso → procesar → vender → impuesto, comida y sueño.
- [ ] **F5-02** Muerte permanente y guardado único (al dormir; salir del juego a mitad de una salida guarda en ese punto; morir borra la partida).
- [ ] **F5-03** Radiación (dosis, enfermedad, pastillas) y aire (máscara, filtros, empañado).
- [ ] **F5-04** **El Inquilino**, completo: territorio, vibraciones por la estructura, huecos y bajantes, señales.
- [ ] **F5-05** Estetoscopio, martillo y clavos (para condenar trampillas) y cuerda por fachada.
- [ ] **F5-06** **Zona 2, Los Bloques**, parcial: Mineros 7 (con la farmacia, el universam y el Inquilino), una jrushchovka, la escuela Nº 21 y los garajes de la Jauría.
- [ ] **F5-07** Encargos con pistas, 3 clientes y una reputación sencilla.
- [ ] **F5-08** Tablero de planificación en el depósito (páginas e hilo).
- [ ] **F5-09** Clima (nieve, viento, ventisca) y luz del día.
- [ ] **F5-10** La escalera mecánica: transición gradual del estilo, el sonido y la música.
- [ ] **F5-11** Menú principal, firma de la escritura, opciones en la radio y pantalla final.
- [ ] **F5-12** **Cooperativo de prueba**: dos jugadores, por red local o IP, durante todo el bucle.
- [ ] **F5-13** Rendimiento en tu Ryzen 7 8700G y accesibilidad básica.
- [ ] **F5-14** El mundo vivo en las zonas 1 y 2: rutinas de la Jauría y del Inquilino, y saqueadores básicos que salen y vuelven a su guarida.

**Contenido**: la estación (depósito, pasillo y escalera), las zonas 1 y 2 (esta parcial), la Jauría y el Inquilino, 12 herramientas, unos 30 objetos de botín y 3 clientes.
**Entregable**: una demo de 60 a 90 minutos, con varias salidas.
**Criterio de salida**: se puede completar sin errores bloqueantes, va a 60 fps en tu PC, la prueban de 3 a 5 personas y las muertes se sienten justas.

### Fase 6: Producción (alfa) · tamaño XXL

**Objetivo**: todo el contenido dentro del juego.

- [ ] **F6-01** Zonas: Los Bloques completa, La Avenida y el Mercado, El Barrio Obrero, La Zona Industrial, El Parque y el Hospital y El Centro, según el plano.
- [ ] **F6-02** Los túneles como rutas alternativas.
- [ ] **F6-03** **El Llamador**, completo.
- [ ] **F6-04** **Los Saqueadores**, primera versión: patrullas, vigías, investigación, búsqueda en grupo, comunicación audible y memoria.
- [ ] **F6-05** Catálogo completo: unas 25 herramientas y unos 100 objetos de botín.
- [ ] **F6-06** Unas 15 mejoras del depósito, más la personalización.
- [ ] **F6-07** Unos 8 clientes con sus encargos.
- [ ] **F6-08** Variación entre salidas: patrullas, desplazamientos de la Jauría, campamentos nuevos, botín.
- [ ] **F6-09** La Zona Cero y la gran expedición: escondites, el final y qué le pasó a tu padre.
- [ ] **F6-10** Rutinas y relaciones de todas las amenazas en el mundo vivo, más la fauna menor.
- [ ] **F6-11** Una ciudad con lógica: portales, escaleras, pisos, sótanos y bajos comerciales que se recorren por dentro, con la misma calidad en toda la parte explorable.

**Entregable**: el juego, completable de principio a fin.
**Criterio de salida**: todo el contenido está dentro, aunque falte pulido.

### Fase 7: Saqueadores tácticos · tamaño L

**Objetivo**: humanos que piensan, planifican y tienden emboscadas, sin hacer trampa nunca.

- [ ] **F7-01** Razonamiento sobre evidencias: huellas, puertas abiertas, marcas de tiza, objetos que faltan.
- [ ] **F7-02** Planificador (GOAP o HTN): emboscadas en pasos obligados, cebos y trampas.
- [ ] **F7-03** Coordinación de grupo: cerrar salidas, rodear, relevos.
- [ ] **F7-04** Memoria a largo plazo: aprenden tus rutas habituales.
- [ ] **F7-05** Comportamiento humano: miedo, cansancio, discusiones, retirada.
- [ ] **F7-06** Validación: la prueba de justicia automática cubre todas sus decisiones.

**Criterio de salida**: en las pruebas, los jugadores caen en emboscadas y, al revisarlas, las entienden y las consideran justas.

### Fase 8: Pulido (beta) · tamaño L

- [ ] **F8-01** Equilibrio: economía, impuesto, hambre, peligro y duración de las salidas.
- [ ] **F8-02** Rendimiento y opciones gráficas.
- [ ] **F8-03** Accesibilidad completa.
- [ ] **F8-04** Mezcla final de audio y música.
- [ ] **F8-05** Cooperativo de hasta 4 jugadores, pulido.
- [ ] **F8-06** Introducción integrada: el primer día de limpieza como tutorial.
- [ ] **F8-07** Pruebas externas y corrección de errores.

**Criterio de salida**: sin errores graves conocidos y con el rendimiento objetivo.

### Fase 9: Versión 1.0 · tamaño M

- [ ] **F9-01** Ejecutables e instalador para Windows (y Linux).
- [ ] **F9-02** Última ronda de control de calidad.
- [ ] **F9-03** Material de presentación (arte, capturas, tráiler) por si algún día se publica.
- [ ] **F9-04** Documentación final del proyecto.

**Criterio de salida**: el juego está listo para publicarse, aunque no se publique.

---

## 15. Hoja de Desarrollo

### 15.1 Hitos

| Hito | Fase | Entregable | Criterio de salida | Tamaño | Estado |
|---|---|---|---|---|---|
| **H0 · Hola, Tumansk** | 0 | Proyecto, red, pipelines y CI | Un asset va de la receta al juego sin pasos manuales; dos instancias sincronizadas | S | ✅ |
| **H1 · Prueba de Tinta** | 1 | 2 dioramas y guía de estilo | Estilo aprobado por ti | M | 🟨 |
| **H2 · El depósito abre** | 2 | Depósito jugable | Del depósito sucio a la primera venta, sin cajas de texto | L | 🟨 |
| **H3 · Primera salida** | 3 | La Plaza, el cuaderno y la Jauría | Se planifica, se dibuja, se usan rutas distintas; muertes justas | L | 🟨 |
| **H4 · El mundo vivo** | 4 | Las zonas 1 y 2 funcionando sin el jugador | Lo que ves al llegar cuadra con lo que pasó; rutinas y peleas que nadie provoca | L | ⬜ |
| **H5 · Los primeros días** | 5 | Vertical slice | Bucle completo, 60 fps en tu PC, cooperativo de 2 | XL | ⬜ |
| **H6 · Alfa** | 6 | Contenido completo | Completable de principio a fin | XXL | ⬜ |
| **H7 · Saqueadores tácticos** | 7 | IA humana avanzada | Emboscadas que se entienden y se sienten justas | L | ⬜ |
| **H8 · Beta** | 8 | Juego pulido | Sin errores graves; cooperativo de 4 | L | ⬜ |
| **H9 · 1.0** | 9 | Versión final | Lista para publicarse | M | ⬜ |

**Leyenda.** Estado: ⬜ pendiente · 🟨 en curso · ✅ hecho · ⛔ bloqueado. El tamaño es relativo (S, M, L, XL, XXL); se convertirá a semanas cuando hayamos medido el ritmo real en las Fases 0 y 1.

### 15.2 Contenido objetivo

| Elemento | Vertical slice (Fase 5) | Versión 1.0 |
|---|---|---|
| Zonas | 1 completa y 1 parcial | 8, más el río y los túneles (la ciudad entera del plano) |
| Amenazas | La Jauría y el Inquilino | La Jauría, el Inquilino, el Llamador y los Saqueadores |
| Herramientas | 12 | Unas 25 |
| Objetos de botín distintos | Unos 30 | Unos 100 |
| Clientes | 3 | Unos 8 |
| Mejoras del depósito | 4 | Unas 15 |
| Mundo vivo | Rutinas de la Jauría, el Inquilino y saqueadores básicos en las zonas 1 y 2 | Todas las amenazas y la fauna menor, en toda la ciudad |
| Jugadores | 1–2 | 1–4 |

### 15.3 Lista de recortes

Si hay que reducir el alcance, se recorta en este orden:

1. Los túneles como rutas alternativas.
2. Interiores hechos a mano en la Zona Industrial y el Barrio Obrero: se quedan con los interiores de serie.
3. La personalización avanzada del depósito.
4. El cooperativo de 4 (se quedaría en 2).
5. El clima variable (se quedaría solo la nieve).

**No se recortan nunca**: el estilo, el cuaderno, la calidad de cada amenaza, el mundo vivo, la muerte permanente, la tactilidad del depósito y el sonido.

### 15.4 Cómo trabajamos

1. Cada sesión parte de una tarea de esta hoja, identificada por su ID.
2. La implemento en una rama, con tests y capturas.
3. Tú revisas las capturas o la build y das el visto bueno.
4. Se marca la tarea y se actualiza la hoja.
5. Las decisiones importantes quedan registradas en `docs/`.

**Qué necesito de ti**: aprobar el estilo (Fase 1); probar las builds en tu PC, porque desde el entorno de desarrollo solo puedo ver capturas y no jugar en tiempo real; resolver las dudas de diseño; y opinar en las pruebas.

---

## 16. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Mundo vivo: estabilidad, rendimiento y depuración | Alto | Fase propia, simulación en dos niveles, mapa de observación con registro de sucesos y pruebas de 30 días simulados |
| IA humana creíble, inteligente y justa | Alto | Una fase dedicada, construcción por capas, la prueba de justicia automática y herramientas de depuración |
| Que el arte generado por código no alcance la calidad buscada | Alto | Puerta de estilo en la Fase 1. El shader hace buena parte del trabajo. Iteración a base de capturas. Si un asset clave no llega al nivel, se modela a mano en Blender o se encarga |
| Animar criaturas (sobre todo cuadrúpedos) | Alto | Pocas amenazas, así que cada una recibe tiempo de sobra; animación "a saltos", que perdona imperfecciones; ajustes procedurales |
| Cooperativo | Alto | Red desde la Fase 0 y pruebas con dos instancias en cada fase |
| Alcance | Alto | Estación pequeña, 4 amenazas, la lista de recortes |
| Tamaño de la ciudad: muchos edificios con interior y la misma calidad en todos | Alto | El plano es un dato validado; maqueta automática antes de construir; kit modular con interiores de serie; solo 44 sitios hechos a mano; carga por sectores de 200 m y manzanas como oclusores |
| Que dibujar mapas en primera persona resulte incómodo | Medio | Prototipo temprano (Fase 3), trazo suavizado, regla, símbolos y pruebas con jugadores |
| Que la muerte permanente frustre | Medio | Amenazas que avisan, herramientas de información, ninguna muerte sin señales previas |
| Rendimiento con gráfica integrada | Medio | Iluminación horneada, presupuesto por efecto, escalado FSR |
| El entorno de desarrollo en la nube no tiene GPU | Medio | Render por software para las capturas; pruebas en tiempo real en tu PC |
| Audio y música | Medio | Se decide más adelante con un único criterio: la mejor calidad posible |
| Propiedad intelectual | Bajo mientras no se publique | Nombre, ciudad, criaturas y arte propios (ver la [sección 18](#18-propiedad-intelectual)) |

---

## 17. Preguntas abiertas

Cada pregunta lleva una propuesta. Si te parece bien, basta con decir "ok".

| # | Pregunta | Propuesta |
|---|---|---|
| 1 | ¿Pasamos la Hoja de Desarrollo a **Issues de GitHub**? Una "issue" es una ficha por tarea dentro de GitHub, con su estado y sus comentarios, y todas juntas se pueden ver como un tablero (pendiente, en curso, hecho). Es opcional: el README ya cumple esa función | No por ahora: seguimos con el README |
| 2 | **Los hitos y la niebla.** Con la niebla de día del estilo, la ciudad desaparece a partir de unos 300 m, y sin mapas el jugador se orienta con los hitos. En la maqueta, los hitos atraviesan la niebla: como mucho los tapa un 78 % ([D-027](docs/DECISIONES.md)). ¿Te parece bien que los hitos se vean siempre, como siluetas apagadas? | Sí, con ese tope; se ajusta mirando la maqueta en tu PC |
| 3 | **Los patios ciegos.** Desde el 92 % de la calle se ven al menos dos hitos, pero desde muchos patios cerrados no se ve ninguno (sobre todo en Los Bloques: solo el 73 % de los puntos ven dos). ¿Cambiamos la regla del plano a «desde cualquier calle», o añadimos hitos que asomen por encima de los tejados? | Cambiar la regla a las calles: un patio cerrado que no deja ver nada da miedo, y eso también sirve |

### Respondidas

| Tema | Respuesta |
|---|---|
| Título | *Tumansk*, como título de trabajo |
| Objetivo de la partida | Llegar a la zona más lejana y saber qué le pasó a tu padre. Muy difícil, al final de la partida |
| Rastros del padre | Pocos y ambiguos |
| Chico o chica | Se elige al firmar la escritura |
| Clima | Invierno largo, con nieve y huellas |
| Beber | No hace falta: solo comer; el agua la da la estación |
| Saqueadores | Matan |
| Muerte en cooperativo | Quien muere queda fuera; la partida sigue mientras quede alguien vivo |
| Amenazas | La Jauría, el Inquilino, el Llamador y los Saqueadores, por ahora |
| Gráfica | Integrada (Radeon 780M): 1080p a 60 fps, con escalado si hace falta |
| Zona más lejana | La Zona Cero: un edificio partido por la mitad muy cerca del cráter, no el cráter |
| Escondites y refugios | Sí, y los refugios los construyes tú, en casi cualquier sitio |
| Duración de la gran expedición | De 60 minutos a 2 o 3 horas, según lo preparado que vayas |
| Estilo, revisión 1 | Contorno y tramado, bien. Depósito cálido, muy bien. Exterior demasiado blanco y pálido; el cielo nunca negro |
| Estilo, revisión 2 | El exterior transmite la sensación. Mantener esa calidad, con lógica de ciudad, en toda la parte explorable. Noche mucho más oscura (sin linterna casi no se ve). Anochecer, bien, con un ligero retoque. La silueta de la Zona Cero se queda así por ahora |
| Historia de fondo | Gobierno civil en la red de túneles; dos años desde la Noche de la Caída de las Bombas |
| Mundo vivo | Como en *Rain World*: el mundo funciona sin el jugador, con fase propia en el plan |
| Ciudad | Una zona grande y continua, con la lógica de una ciudad real y nada plano. Plano completo fijado en [docs/CIUDAD.md](docs/CIUDAD.md) antes de cerrar la Fase 1 |

---

## 18. Propiedad intelectual

*Metro 2033*, *S.T.A.L.K.E.R.*, *Fallout* y *Rain World* son marcas registradas de sus propietarios, y *Cat Mail Co.* es obra de sus autores. Aquí funcionan como referencias de tono, mecánicas y estilo. Este juego tiene nombre, ciudad, personajes, criaturas, arte y música propios: no usa sus nombres, personajes, criaturas, logotipos, música, mapas ni assets. "Stalker" se usa como nombre común del oficio, no como marca. El nombre del repositorio puede quedarse como nombre de trabajo interno.

---

## 19. Glosario

| Término | Significado |
|---|---|
| **Tumansk** | La ciudad |
| **La estación** | Tu refugio bajo tierra. Siempre segura |
| **El depósito** | Tu local en la estación: almacén, taller y tienda |
| **Stalker** | Quien sube a la superficie a buscar lo que queda |
| **La superficie** | La ciudad, arriba |
| **La compuerta** | La puerta hermética entre la estación y la superficie |
| **Rublos** | La moneda |
| **Impuesto** | Lo que pagas cada día al gobierno civil por el local |
| **Noche de la Caída de las Bombas** | La noche de la guerra atómica, hace dos años |
| **Gobierno civil** | El gobierno que se formó en la red de túneles del metro |
| **Mundo vivo** | La ciudad funcionando por su cuenta: rutinas, caza y peleas, estés o no |
| **Encargo** | El pedido de un cliente: algo que hay que encontrar arriba |
| **La Jauría** | Perros asilvestrados y deformados que cazan en manada |
| **El Inquilino** | La criatura que vive dentro de un edificio |
| **El Llamador** | La criatura que imita sonidos y voces |
| **Los Saqueadores** | Personas armadas que viven de lo que encuentran y de lo que roban |
| **El cuaderno** | Tus mapas, tus notas y tus planes. El único mapa que existe |
| **Dosímetro** | El aparato que mide la radiación |
| **Filtros** | Lo que hace respirable el aire dentro de la máscara. Se gastan |
