# La superficie jugable (Fase 3)

Cómo es una salida, qué se hace arriba y cómo está construido por dentro. Es la referencia de la Fase 3: el diseño de juego está en el [README](../README.md#6-la-superficie-táctica-y-terror) (secciones 6 y 7) y el plano de la ciudad en [CIUDAD.md](CIUDAD.md); aquí se concreta.

Objetivo de la fase: **una salida corta en la que planificar sirva y la Jauría dé miedo de verdad.** Subir por la escalera, llegar a un objetivo de La Plaza y volver, en 10 a 20 minutos, sin un solo marcador en pantalla.

**Sin sonido todavía** (decisión de la fase, D-061): el ruido se simula entero para la inteligencia artificial (los perros oyen), pero no suena nada. Mientras no haya audio, lo que suena se ve: cada ruido fuerte deja en el suelo unas **ondas de tinta** que se abren desde donde sonó, del tamaño de lo lejos que se oye (los tuyos y los que oirías). Es la misma convención de los dibujos animados, y cuando llegue el sonido se quedará como opción de accesibilidad.

## 1. La salida

- **Subir.** Al fondo del pasillo de la estación, las tres escaleras mecánicas paradas suben hacia la compuerta. La reja de abajo la abre la guardia de 7 a 20. Cuando todos los jugadores vivos están en la escalera, se sube: fundido, y aparecéis arriba, en la **esclusa** del vestíbulo del metro (PLZ-06), delante de la compuerta blindada.
- **La compuerta** se abre girando el volante (círculos con el ratón). Detrás, la sala redonda del vestíbulo, el equipaje de la evacuación y la puerta principal, con una hoja abierta, a la avenida.
- **Volver.** Todos los vivos dentro de la esclusa y la compuerta cerrada: se baja. Apareces al pie de la escalera, en la estación, con lo que traigas.
- **La hora no se para.** Arriba corre igual que abajo (un día son unos 34 minutos). Salir a las 9 y volver a las 14 es una salida de unos 10 minutos de juego real; se puede volver de noche, pero casi nunca es buena idea.
- **Lo que subes** es lo que llevas: la mochila, el cinturón y lo que tengas en las manos.

```
                     N
        primer patio · trasteros · palomar
   Juventud 1 ┌────────────────────────┐ Banco (la cámara acorazada)
              │ Casa Curva Norte        │
              │ Correos Nº 1 · librería │   Torre Norte (14 plantas)
              └─────── Q2 · Q1 ─────────┘
     boca O ╲                         ╱ boca NE
  vestíbulo  ╲    plaza del Trabajo  ╱
  del metro ──●── · (Minero) · ──────●── boca E         Torre Este
  (tu salida) ╱  paso subterráneo   ╲    control del ejército
     boca SO ╱    en cruz bajo ella  ╲
              ┌──── Q4 · Q3 ─────────┐
              │ Casa Curva Sur         │  patio sur · trasteros
              │ Gastronom Nº 1 · farmacia · peluquería │ transformador
              └────────────────────────┘
   avenida hacia el sur: el atasco de la evacuación ··· la plaza de la Estación
   (las tiendas de la evacuación, el tren, la autoestación) ··· al oeste, los garajes Volga: la guarida
```

## 2. Controles

| Tecla | Qué hace |
|---|---|
| WASD, ratón | Andar y mirar |
| Mayúsculas (mantener) | Correr, mientras haya aliento |
| C o Control | Agacharse y levantarse |
| Q, E (mantener) | Asomarse a un lado (sin mover los pies) |
| Espacio | Saltar un poco o encaramarse a lo que llega a la cintura |
| F | Coger, soltar y usar lo que tienes delante (puertas, la compuerta, cajones, cuerdas) |
| Botón izquierdo | Trabajar con lo que llevas (la ganzúa, la palanca, la cizalla, la tiza); con algo que se lanza, mantener y soltar para tirarlo |
| Botón derecho | Inspeccionar lo que llevas; con los prismáticos, mirar por ellos |
| 1, 2, 3 | Sacar lo que llevas en ese hueco del cinturón, o guardar ahí lo que tienes en la mano |
| I | Arrodillarte y abrir la mochila (o guardar en ella lo que llevas en la mano) |
| Tab | Abrir el cuaderno |
| T | Encender y apagar la linterna |
| R (mantener) | Mirar el reloj de pulsera |

## 3. El cuerpo: moverse, ruido y visibilidad (F3-01, F3-02)

### 3.1 Moverse

| Paso | Velocidad | Aliento | Notas |
|---|---|---|---|
| Agachado | 1,0 m/s | se recupera | Ojos a 0,95 m; ocupas la mitad |
| Andando | 2,3 m/s | se recupera | Como en el depósito |
| Corriendo | 4,8 m/s | se gasta en unos 8 s | Sin aliento no se corre y se jadea |

- **El aliento** no tiene barra: se ve en el vaho de tu respiración (más seguido cuanto más cansado), en el balanceo de la vista y en que, sin aliento, correr no arranca. Se recupera en unos 12 s andando y antes quieto.
- **El peso** (lo que llevas en las manos, el cinturón y la mochila) frena (la mitad de rápido con 22 kg), gasta el aliento antes y hace más ruido.
- **Asomarse** desplaza la cabeza 0,35 m a un lado e inclina la vista; el cuerpo no se mueve, así que se asoma solo la cabeza.
- **Caerse** de más de 1,5 m hace ruido; de más de 3,5 m, además, una torcedura (andas cojeando hasta vendarla) y lo frágil de la mochila se puede romper.

### 3.2 Ruido

Cada ruido tiene un **alcance**: los metros a los que se oye con el aire en calma y sin nada en medio. Los pasos hacen un ruido por paso:

| Paso | Alcance base |
|---|---|
| Agachado | 3 m |
| Andando | 9 m |
| Corriendo | 22 m |
| Al caer | 4 m por metro de caída |

Se multiplica por **el suelo** (nieve 1,0; asfalto, losas y granito 0,85; tierra 0,7; grava y cascotes 1,3; cristales 2,0; chapa y escaleras metálicas 1,8; madera 1,1; hielo y charcos 1,4) y por **la carga** (+2 % por kilo a partir de 6 kg). Lo que va suelto en la mochila (latas, herramientas, botellas que no van entre ropa) **suena al moverse**: 4 m andando y 10 corriendo por cada cosa mal guardada.

Otros ruidos: abrir una puerta (6 m; con bisagras oxidadas, 12), la palanca (30 m al ceder), un cristal roto (25 m), la cizalla (12 m), la ganzúa (2 m), lo que se lanza al caer (de 12 m una piedra en la nieve a 30 m una botella en el granito), el despertador (35 m mientras suena), jadear sin aliento (5 m) y el estómago vacío (2 m).

**Lo que tapa:** el viento quita hasta un 40 % del alcance y la ventisca, un 65 %. **Lo que hay en medio:** cada muro entre el ruido y quien escucha deja un 35 %; dentro de un edificio y fuera, otra mitad.

### 3.3 Visibilidad

Lo lejos que alguien puede verte es un **alcance de vista** que se multiplica:

| Factor | Valores |
|---|---|
| Base | 120 m (una persona de pie, andando, a plena luz) |
| Luz donde estás | Día 1,0; a la sombra, 0,7; dentro de un edificio, 0,4; anochecer, 0,5; noche, 0,08. Tu linterna encendida te hace visible a 250 m si te apunta y a 120 m si no |
| Postura | De pie 1,0; agachado 0,55 |
| Movimiento | Quieto 0,5; andando 1,0; corriendo 1,4 (los perros ven sobre todo el movimiento: quieto, 0,35) |
| Silueta | Si detrás de ti, visto desde quien mira, solo hay cielo: 1,6 |
| Clima | Nevando 0,7; ventisca 0,35 |
| Cobertura | La parte de ti (pies, pecho, cabeza) que se ve desde sus ojos |

Dentro de su campo de visión y de ese alcance, **no te ven de golpe**: se van fijando (más rápido cuanto más cerca). Si sales del campo antes de que se fijen del todo, solo saben que "algo se movió por ahí".

## 4. Lo que llevas (F3-03, F3-05 a F3-08)

### 4.1 La mochila y el cinturón

- **La mochila** es una cuadrícula de 6 × 5. Cada objeto ocupa su forma (la de su ficha) y se puede girar. Abrirla en la superficie es **arrodillarse, quitársela y abrirla** (un segundo y medio en el que estás agachado y quieto); se ve en 3D delante de ti, con las cosas en sus huecos, y se colocan con el ratón. El tiempo no se para.
- **Guardar deprisa**: I con algo en la mano lo mete en el primer hueco donde quepa (un segundo, agachado).
- **El cinturón** tiene 3 huecos para cosas pequeñas (1 × 1 o 1 × 2: la linterna, la brújula, la tiza, las ganzúas, una lata para lanzar). Sacar o guardar es casi instantáneo.
- **Lo que suena**: lo de metal y cristal suena si no tiene al lado (en la cuadrícula) algo blando (ropa, trapos, papeles). Empaquetar bien es sigilo.
- **Lo frágil** (cristal, electrónica) se puede romper al caer o al correr mucho rato.
- En el depósito, la mochila se prepara en la mesa de planificación, con calma.

### 4.2 Instrumentos

| Instrumento | Cómo se usa |
|---|---|
| Brújula | En la mano: la aguja señala el norte de verdad. Con el viento, la brújula dice de dónde sopla |
| Reloj de pulsera | Siempre puesto: R levanta la muñeca y se leen las agujas |
| Podómetro | Cuenta los pasos (de verdad, uno por zancada). En la mano se lee la cifra; con el botón izquierdo se pone a cero |
| Prismáticos | En la mano, el botón derecho los lleva a los ojos: mucho aumento y el borde de las dos lentes. De día, si miras hacia donde está el sol, el cristal brilla (los saqueadores, en la Fase 7, lo verán) |

### 4.3 Herramientas de acceso

| Herramienta | Para qué | Gesto | Ruido |
|---|---|---|---|
| Ganzúas | Cerraduras de puertas y cajones | Buscar con el ratón el punto de cada pin, despacio; el miedo hace temblar la mano. Pueden partirse | 2 m |
| Palanca | Forzar puertas, cajones y la trampilla del almacén | Tirar hacia abajo, como en el depósito | 30 m al ceder |
| Cizalla | Cadenas y candados | Apretar (tirar hacia abajo) | 12 m |
| Cuerda | Bajar por el socavón o desde un sitio alto | Atarla donde hay de qué (una barandilla, un tubo) y bajar o subir por ella. Se queda puesta: es un atajo para la próxima vez | — |

Cómo está hecho:

- **Las puertas** (`SurfaceDoor`) giran sobre su bisagra y su estado vive en el mundo (`DepotWorld`, que se guarda): abierta o no, su cierre (cerradura, candado, cadena, atrancada, rota o nada) y lo que se lleva hecho con la palanca y la cizalla. Cerrada, con F se sacude y suena un poco: así se sabe. El candado y la cadena se ven; la cerradura y lo atrancado, no. Cómo empieza cada una sale de su nombre (siempre igual).
- **La palanca** son tirones (cuatro; cada uno cruje): al ceder, la puerta se abre de golpe y se oye en 30 m. **La cizalla**, dos apretones: corta y se oye en 12 m. Las dos van como los trabajos del depósito (`Workable`).
- **Las ganzúas** abren una vista de la cerradura delante de ti (`LockpickView`): la cerradura cortada, con sus pines, la ganzúa y la llave de tensión. Con el ratón, a los lados se pasa de pin en pin (con la ganzúa abajo) y arriba se sube el pin; en su punto, quieto un momento, se queda puesto y la llave cede un poco. Pasarse lo atasca (hay que bajar la ganzúa) y forzar deprisa tuerce la ganzúa hasta partirla (se gastan las ganzúas). El miedo hace temblar la punta. Una cerradura tiene 4 o 5 pines; un candado, 3. Ver D-068.
- **Trepar** (`Climbable`): por una escalera o una cuerda se sube empujando hacia ella; arriba se sale al rellano y, desde el rellano, andando hacia el borde se agarra uno mirando abajo para bajar (mirando abajo, adelante es bajar). Saltar suelta, y la caída cuenta desde donde se soltó (bajar por la escalera no es caerse). Los demás te ven trepar: el estado se replica y el personaje tiene su ciclo (`trepar`, dos peldaños por ciclo, a la velocidad a la que sube). Los perros no trepan.
- **La cuerda** (`RopeAnchor`): con la cuerda en la mano, mantener el botón sobre una argolla la ata; queda colgando hasta el suelo y se guarda con el mundo.

### 4.4 Distracciones

- **Lo que se lanza** (una lata vacía, una botella, un cascote): mantener el botón izquierdo y soltar; cuanto más se mantiene, más lejos. Al caer suena según lo que es y dónde cae, y quien lo oye va a ver qué ha sido.
- **El despertador**: se le da cuerda (círculos: cada vuelta, un minuto de juego), se deja y suena 30 s donde tú ya no estás.

### 4.5 La tiza

Con la tiza en la mano, el botón izquierdo sobre una pared o el suelo dibuja una marca: una flecha, una cruz (peligro), un círculo (botín), una X (sin salida) o un perro; la rueda cambia de marca. Las marcas se quedan de una salida a otra (se guardan con el mundo) y las ve cualquiera.

## 5. El cuaderno (F3-04)

- **Tab** saca el cuaderno: lo sujetas abierto con las dos manos y la vista baja a la página. Hace falta luz para ver lo que dibujas (de noche, la linterna). El tiempo sigue.
- **Se dibuja con el ratón** sobre la página cuadriculada: lápiz de grafito; la rueda cambia a la goma y a los lápices de colores (rojo, azul, verde); con el botón derecho pulsado, la regla (líneas rectas).
- **Sellos**: unos símbolos pequeños que se estampan (peligro, entrada, botín, radiación, refugio, perro, y el reloj, que escribe la hora que marca el tuyo: "visto a las 14:20").
- **Notas**: se escriben con el teclado y quedan a mano, en la letra del cuaderno.
- **Las páginas** se pasan con A y D; hay 24.
- **Los trazos son vectores** (listas de puntos suavizados) y se guardan con la partida. El miedo hace temblar el trazo. Si mueres, el cuaderno se pierde contigo.

Cómo está hecho:

- **Los datos** (`Notebook`): 24 páginas con sus trazos (la tinta y los puntos de la página, de 0 a 1, aligerados con Ramer-Douglas-Peucker al guardarlos), sus sellos y sus notas. Viven en el estado de la partida, por el puesto de cada jugador (`GameState.notebooks`), como la mochila: se guardan con ella y llegan a todos los equipos. Lo cambia el anfitrión cuando lo pide su dueño (`PlayerNotebook`); nadie más puede escribir en él. Al morir, se borra.
- **La vista** (`NotebookView`): el modelo del cuaderno abierto delante de la cámara, con las dos hojas pintadas por dos `SubViewport` (`NotebookPage`: el papel cuadriculado, los trazos, los sellos con la tinta violeta de un tampón y las notas en Caveat). El papel lo ilumina la escena, así que a oscuras no se ve lo que se dibuja. Un lápiz (el modelo de verdad) sigue al ratón con la punta en el papel; con la goma se le da la vuelta. Abajo, con letra de cuaderno, la herramienta que llevas.
- **Las manos**: hay que tenerlas libres para sacarlo; mientras está abierto no se anda y el botón izquierdo dibuja (no lanza ni trabaja).
- `scenes/style/primera_persona_cuaderno.tscn` abre el cuaderno en el depósito con un mapa de La Plaza dibujado desde el plano, para las capturas.

## 6. Percepción y conocimiento (F3-09)

Nadie decide nada a partir de lo que no ha percibido. Cada agente tiene **sentidos**, que producen **percepciones**, que se guardan en su **memoria**; sus decisiones solo leen la memoria.

- **Vista**: un cono (los perros, 220° de ancho y 140 m de alcance base), el alcance de vista de quien mira (3.3) y rayos a los pies, el pecho y la cabeza. Se fija poco a poco.
- **Oído**: cada ruido llega con su alcance, lo que tapa el clima y lo que hay en medio (3.2). Los perros oyen un 30 % más lejos que una persona.
- **Olfato**: cada jugador huele (más si suda, si sangra, si lleva comida). El olor lo lleva el viento: quien está a sotavento te huele hasta 60 m con viento fuerte; a barlovento, solo a 5 m; sin viento, a 15 m en redondo. Además, al andar dejas un **rastro** que dura unos 10 minutos (3 si nieva) y la sangre, 30. Los perros lo siguen hacia donde es más fresco.
- **Memoria**: por cada cosa percibida, dónde y cuándo, por qué sentido y con cuánta certeza. La certeza baja con el tiempo; lo que no se renueva se olvida.
- **Prueba de justicia**: cada decisión que tiene que ver con dónde estás guarda la percepción de la que sale. Una prueba automática recorre las decisiones y falla si alguna no tiene percepción detrás.
- **La herramienta de depuración** (F3 en el teclado): los conos de vista, lo lejos que se oye cada ruido, el cono de olor con el viento, el rastro, lo que recuerda cada perro (dónde cree que estás y con qué certeza) y por qué hace lo que hace.

## 7. La Jauría (F3-10)

### 7.1 Ficha

- **Qué es.** Seis perros asilvestrados, más grandes de lo que deberían (80 cm a la cruz), con calvas, bultos y el pelo apelmazado de nieve. Los guía **la Vieja**, una hembra gris con una oreja partida. Los demás: dos jóvenes atrevidos que se adelantan, dos que rodean y uno cojo que se queda atrás.
- **Dónde.** La guarida está en los garajes Volga (88, 72). Su territorio es Los Bloques, la playa de vías y **la plaza de la Estación**; la avenida es su camino a la plaza.
- **Rutina.**

  | Hora | Qué hace |
  |---|---|
  | 21–5 | Duerme en los garajes |
  | 5–8 y 16–19 | **Caza**: recorre el territorio en abanico y va a por cualquier cosa que perciba, también fuera del territorio |
  | 8–16 | **Ronda**: recorre el territorio en grupo, despacio, parándose a descansar en sitios fijos |

- **Sentidos.** Olfato muy fino (manda el viento), vista que capta el movimiento (lo quieto apenas lo ven) y buen oído.
- **Señales que deja.** Huellas en la nieve por donde pasa la ronda, excrementos, huesos roídos en la plaza de la Estación, los garajes con el suelo pisoteado.

### 7.2 Cómo caza

| Estado | Qué hace la manada | Qué lo provoca |
|---|---|---|
| Descanso | Echados, uno de guardia con la cabeza alta | La rutina |
| Ronda | En fila suelta, la Vieja delante, olisqueando | La rutina |
| Investigar | Uno o dos van a ver; los demás esperan mirando | Un ruido, un rastro o algo que se movió, sin saber qué es |
| Tanteo | Se acercan a unos 30 m, se paran, te miran, se mueven de lado; a ratos uno avanza un poco | Te han identificado como presa |
| Rodeo | Se abren: los rodeadores van a tus lados y por detrás, a cortar tus salidas (las calles, las puertas abiertas); la Vieja se queda delante | Tras el tanteo, si sigues ahí; o si te alejas despacio |
| Persecución | Todos a la carrera | **Correr delante de ellos**, o cuando el rodeo se cierra |
| Ataque | Uno salta, muerde, sacude y suelta; se aparta y salta otro | Te alcanzan |
| Comer | La Vieja come primero; los demás, alrededor, gruñendo | Un cebo o comida que encuentran. Dura unos 40 s |
| Seguir el rastro | Con el hocico en el suelo, hacia lo más fresco | Un rastro de olor; uno de sangre lo siguen sin descanso |

- **Lo que no pueden**: abrir puertas, subir por cuerdas o escaleras de mano, saltar más de un metro. Las escaleras de un portal sí las suben.
- **Cómo sobrevivir** (lo que el jugador aprende): avanzar con el viento de cara, no correr nunca delante de ellos, subir a un piso alto y cerrar la puerta, sacrificar comida como cebo, vendarse para no dejar rastro de sangre.
- **No se les puede matar.** Se les puede entender.

### 7.3 Cómo está hecha

- **Modelo** (`tools/blender/recipes/perros.py`): malla con esqueleto (columna, cuello, cabeza, mandíbula, cola, cuatro patas) y variantes de pelaje, calvas y bultos.
- **Animación propia, por código**: ciclos de paso, trote y galope "a saltos" (la pose cambia 12 veces por segundo, como el dibujo animado), con las patas apoyadas en el suelo, la cabeza siguiendo lo que percibe, y las poses de olfatear, vigilar, echarse, comer, morder y aullar.
- **Moverse por la ciudad**: una rejilla de navegación de 1 m sobre el plano (los edificios, los vehículos, las vallas y los escombros son obstáculo), con capas para el paso subterráneo y los interiores que se recorren, unidas por las escaleras; las puertas cerradas cortan el paso.
- **Tres escenarios de prueba**: "corres y te persiguen", "con el viento de cara pasas a 40 m sin que te huelan" y "el cebo los entretiene y pasas".

## 8. El miedo y las heridas (F3-11, F3-12)

- **El miedo** no tiene barra. Sube al ver un perro cerca, al oírlo, al sentirte perseguido, al ser mordido y en la oscuridad; baja despacio cuando estás a salvo. Se nota en las manos y en lo que llevan (la linterna, la ganzúa, el lápiz tiemblan), en el vaho (respiras más rápido) y en el dibujo: el trazo vibra más y el tramado invade los bordes (el parámetro `tinta_miedo` del estilo).
- **Las heridas**: una mordedura quita sangre de golpe y **sangra** mientras no la vendes. La sangre que pierdes gotea (se ve en la nieve y los perros la huelen) y, con poca, la vista se oscurece y no puedes correr. Sin sangre, mueres. Vendarse (con vendas en la mano, mantener el botón izquierdo unos segundos, agachado) corta la hemorragia de una herida. La sangre se recupera durmiendo.
- **La torcedura** (al caer de alto): cojeas hasta vendarla.
- **La muerte**: en solitario, la partida se borra (la última imagen, el depósito cerrado con el cartel). En cooperativo, quien muere ve a los demás hasta que vuelven o mueren todos.

## 9. La Plaza (F3-14)

### 9.1 Objetivos y rutas

En la Fase 3 los sitios que se saquean son los edificios menores, que se recorren enteros (D-067); Correos, el Gastronom y el paso subterráneo quedan para cuando se puedan recorrer las casas. Lo que hay hoy:

| Objetivo | Qué hay | Cómo se entra | Rutas |
|---|---|---|---|
| Los quioscos de la plaza (Q1 a Q5) · ● | Periódicos, cerillas, latas, tabaco, algún billete | La puerta de atrás: cerradura (ganzúas o palanca), candado (cizalla o ganzúas) o atrancada (palanca). Los de la avenida, destrozados, sin puerta ni cristales: se entra encaramándose | **Por la plaza**: el granito abierto, rápido y a la vista. **Pegado a las fachadas** de las Casas Curvas, a la sombra. **Desde el mirador**: se mira antes de salir y se baja por la cuerda hacia la plaza |
| Los trasteros del primer patio (P1, P2) y el palomar (P3) · ● | Leña, tarros de conservas, herramientas, bombillas; en el altillo del palomar, los prismáticos del palomero | Cada caseta con su candado (o una cadena, o atrancada); alguna hundida, abierta. El altillo del palomar, con candado, por su escalera | **Por el arco** de Juventud 1. **Rodeando** la Casa Curva Norte. Desde el palomar se ve el patio y los perros no suben |
| Las tiendas de la evacuación y los quioscos de la Estación (C1 a C4, Q6 a Q9) · ●● | Trapos, latas, vendas, botas, cuerda, alguna máscara o linterna | Las tiendas están abiertas (la puerta de lona enrollada); se entra agachado y dentro no se ve desde fuera | **Por la avenida**: abierta, con mucha vista y el viento de lado. **Entre el atasco**: de coche en coche, a cubierto, pero la chapa suena. **Por detrás de las casas de la avenida**. Es territorio de la Jauría: hay huesos roídos |
| El centro de transformación (T1) y los trasteros del patio sur (P4) · ●● | Chatarra de cobre (pesa y vale), bombillas | La puerta de chapa del transformador, con cadena (cizalla) | **Por la plaza** hasta la Casa Curva Sur y por su lado. **Por el control del ejército** y la boca este. El transformador es además el refugio |

El plan de cada objetivo era este (queda para cuando se recorran las casas):

| Objetivo | Qué hay | Rutas |
|---|---|---|
| Los quioscos del norte (Q1, Q2) · ● | Latas, cerillas, periódicos, tabaco | **Por la plaza**: 100 m de granito abierto; rápida y a la vista de todo. **Por el paso subterráneo**: de la boca oeste a la boca noreste, a oscuras y sin ver lo que hay tras las esquinas. **Por los soportales**: pegado a las fachadas de la Casa Curva Norte, a la sombra; más larga |
| Correos Nº 1 · ● | Paquetes sin repartir en la sala de clasificación | **La puerta de la plaza**: cristales rotos que crujen. **Desde la boca noreste** del paso subterráneo. **Por el primer patio**: por el arco de Juventud 1, entre los trasteros y el palomar, hasta la puerta de atrás (cerrada: ganzúas) |
| El almacén del Gastronom Nº 1 · ●● | Conservas, azúcar, sal: "el almacén de atrás no lo encontró nadie" | **Por la tienda**: forzar la puerta del almacén con la palanca (se oye en toda la plaza). **Por el patio sur**: el muelle de carga, con la persiana encadenada (cizalla). **Por el sótano**: bajando por el portal, a oscuras, hasta la trampilla del almacén |
| La plaza de la Estación · ●● | Las tiendas de la evacuación (ropa, mantas, latas) y el equipaje del andén | **Por la avenida**: abierta, con mucha vista y el viento de lado. **Entre el atasco**: de coche en coche y de autobús en autobús; a cubierto, pero la chapa suena. **Por los portales de la avenida**: por los bajos y los patios de Avenida 14 y 16. Es territorio de la Jauría |

### 9.2 Sitios

- **El mirador**: la azotea del peristilo del vestíbulo. En la sala, una escalera de pates de servicio sube (diez metros, apartada del muro para salvar la cornisa) hasta un ventanal alto sin cristal; por él se sale, agachado, a la azotea, y desde allí se ve la plaza entera y la avenida. En el antepecho que da a la plaza hay una argolla: con una cuerda, se baja por fuera hasta el basamento (y se sube por ella la próxima vez). Los perros no llegan.
- **El palomar** del primer patio: su plataforma, a tres metros, por su escalera de mano.
- **Refugio**: el centro de transformación (puerta de chapa, sin ventanas: la luz no sale). La cámara acorazada del Banco, cuando se recorran las casas.
- **Pasos obligados**: la puerta del vestíbulo y el arco del primer patio.
- **Las señales de la Jauría**: huesos roídos donde come (la plaza de la Estación, la avenida y cerca del vestíbulo) y, en la nieve, sus huellas.
- **La marca de tu padre**: en el muro del vestíbulo, junto a la puerta, una flecha de tiza azulada y gastada señala al noreste.

## 10. El tiempo y el viento

- **La hora** es la de `GameState` y mueve el cielo, la luz, la niebla y el estilo (`Atmosphere`), y la rutina de la Jauría.
- **El tiempo de cada día** sale de una semilla del día: el viento (de dónde sopla y su fuerza: calma, brisa, viento, ventisca) y si nieva. El viento gira despacio durante el día.
- **El viento se ve**: la nieve que cae y la que barre el suelo van con él, los trapos atados a las farolas y a la barrera del control ondean hacia donde sopla, el humo se tumba. Con la brújula se traduce a puntos cardinales.
- **Las huellas**: los pies de cada jugador y las patas de los perros dejan huellas en la nieve. Duran horas si no nieva y unos minutos si nieva.

## 11. En red

- El anfitrión simula la Jauría, la percepción, el viento, las heridas y todo lo que cambia el mundo (puertas, cerraduras, cuerdas, marcas, lo que se recoge). Los ruidos de los jugadores los calcula él a partir de lo que ya se replica (dónde está cada uno, cómo se mueve, si va agachado, qué suelo pisa, cuánto pesa lo que lleva): no se fía de lo que diga cada equipo.
- Los perros se replican como los jugadores (posición, rumbo y pose) y cada equipo los anima.
- Cada jugador tiene su mochila, su cinturón y su cuaderno; el anfitrión los guarda en la partida.
- El miedo, el temblor y las ondas de tinta son de cada equipo: se calculan con lo que ese jugador ve.

## 12. Depuración y pruebas

- **F3**: la herramienta de percepción (sección 6). **F1**: el panel de depuración, con la hora, el viento y el clima, traer la Jauría cerca, invulnerable y ver la rejilla de navegación.
- `scenes/debug/revision_superficie.tscn`: cámaras fijas sobre La Plaza para las capturas.
- Las pruebas: el ruido y la visibilidad (cálculo), los sentidos (oído con muros, vista con cono y cobertura, olfato con viento), la memoria, la justicia, los tres escenarios de la Jauría, la mochila, el cuaderno guardado y cargado, y la salida entera (subir, coger algo, volver) en solitario y con dos equipos.

## 13. Estado

| Tarea | Estado |
|---|---|
| F3-01 Controlador de superficie | Hecha: agacharse, asomarse, correr con aliento, saltar y encaramarse; los pasos suenan según el paso, el suelo y la carga, y se ven en las ondas de tinta |
| F3-02 Visibilidad | Hecha (el cálculo): la luz de la hora, la sombra del sol, el techo, la silueta contra el cielo, la postura, el movimiento, el clima y lo que te tapa; la usa la vista de la IA |
| F3-03 Mochila y cinturón | Hecha: la cuadrícula de 6 × 5 con formas y giros, el cinturón de 3 huecos, el peso y lo que suena suelto; abrirla y guardar en la superficie es arrodillarse. La mochila abierta se ve en 3D y se coge con el ratón |
| F3-04 El cuaderno | Hecho: 24 páginas cuadriculadas en 3D, lápiz de grafito y de colores, goma, regla, siete sellos (el del reloj escribe la hora), notas a mano, el temblor del miedo; se guarda con la partida y se pierde al morir |
| F3-05 Instrumentos | Hechos: la brújula (la aguja busca el norte), el reloj de pulsera (R), el podómetro (cuenta las zancadas desde que se pone a cero) y los prismáticos (botón derecho) |
| F3-06 Herramientas de acceso | Hechas: las puertas con su cierre (cerradura, candado, cadena, atrancada), la palanca, la cizalla, las ganzúas con su vista de la cerradura y el temblor del miedo, trepar por escaleras y cuerdas, y la cuerda atada que se queda |
| F3-07 Distracciones | Hechas: lanzar lo que se lleva (mantener y soltar), el ruido al caer según lo que es y dónde cae, las botellas que se rompen y el despertador con cuerda |
| F3-08 Tiza | Hecha: cinco símbolos (la rueda los cambia), dibujados a mano en paredes y suelo, guardados con el mundo |
| F3-09 Percepción | Hecha: vista que se fija poco a poco, oído con muros y viento, olfato con viento y rastros; memoria, prueba de justicia y la herramienta de depuración (F3) |
| F3-10 La Jauría | Hecha: seis perros con su modelo y sus animaciones, la manada con sus modos, su rutina, sus rutas por la rejilla del plano, sus ladridos y sus tres escenarios de prueba |
| F3-11 Miedo | Hecho: sube con los perros a la vista o al oído, los golpes, la oscuridad y la sangre perdida; tiemblan las manos y la linterna y reacciona el dibujo |
| F3-12 Heridas | Hechas: la mordedura, la sangre que gotea y se huele, vendarse, morir y perder la partida |
| F3-13 Audio | Aplazado: sin sonido por ahora (D-061); el ruido existe para la IA y se ve en las ondas de tinta |
| F3-14 La Plaza | La salida entera (la reja y la escalera del depósito, la esclusa y la compuerta del vestíbulo, y la vuelta, con el depósito como se dejó); los edificios menores enteros y por dentro (quioscos, tiendas, trasteros, palomar, transformador) con sus puertas y su botín; el mirador del vestíbulo con su escalera y su argolla; las señales de la Jauría y la marca de tu padre. Pendientes: Correos, el Gastronom, el Banco y el paso subterráneo (D-067) |
