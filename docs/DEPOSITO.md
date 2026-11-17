# El depósito jugable (Fase 2)

Cómo es el depósito, qué se hace en él y cómo está construido por dentro. Es la referencia de la Fase 2: el diseño de juego está en el [README](../README.md#5-el-depósito-gestión) (secciones 4 y 5); aquí se concreta.

Objetivo de la fase: **trabajar en el depósito da gusto, de principio a fin**. Se juega el recorrido entero, del primer día sucio a la primera venta, sin una sola caja de texto: todo lo que hay que saber está en papeles, instrumentos y objetos del mundo.

## 1. El sitio: la antigua consigna

El depósito es la **antigua consigna** de la estación: el cuarto donde se dejaba el equipaje, con su ventanilla al pasillo. El gobierno civil te la ha dado por escritura (la firmas al empezar la partida). El antiguo dueño la usó de almacén y se fue (o no volvió) dejándolo todo: sus cajas, sus trastos, su silla, su calendario con los días tachados hasta la Noche de la Caída. Nadie dice quién era.

Mide **9 × 7 m**, con una bóveda rebajada de ladrillo encalado (de 2,7 m en los muros a 3,4 m en el centro): grande para lo que era y pequeño para todo lo que tiene que caber. Zócalo de azulejos de metro, suelo de baldosas, tuberías por la bóveda.

```
                  pasillo de la estación (se recorre)
   ┌──────────[ persiana: mostrador ]───────────┬─puerta─┐
   │ corcho de                     caja    báscula        │
   │ encargos   libro de cuentas   de los         descon- │
   │                               rublos         tamina- │
   │ estante-                                     ción    │
   │ rías       baldas de la                              │
   │ (consigna) consigna                   banco de       │
   │                                       trabajo        │
   │                                                      │
   ├──────── tabique ────┤ manta ├────┐                   │
   │ catre    estufa         mesa de planificación         │
   │ tus cosas, la radio     y el tablero de la pared      │
   └──────────────────────────────────────────────────────┘
```

| Rincón | Dónde (en Godot, metros) | Qué hay |
|---|---|---|
| Mostrador | La ventanilla, x de −1,5 a 1,5 en el muro del pasillo (z = 3,25) | El mostrador atraviesa la ventanilla: el cliente se apoya desde el pasillo y tú desde dentro. La persiana baja por fuera. Encima: la caja de los rublos, la báscula y el libro de cuentas |
| Puerta | x de 3,4 a 4,3, en el mismo muro | La puerta de chapa por la que sales al pasillo (a por comida, a pagar, a tirar la basura) |
| Descontaminación | Junto a la puerta, contra el muro derecho | La pila con su llave, el cepillo, el rollo de bolsas y el dosímetro colgado: lo de arriba se limpia nada más entrar |
| Banco de trabajo | Muro derecho, z de −1,6 a 0,6 | El banco con su tornillo, el tablero de herramientas, el flexo |
| Almacén | Muro izquierdo y una fila de baldas en medio | Las estanterías y las viejas baldas numeradas de la consigna; un cartel por categoría: comida, medicinas, herramientas, electrónica, ropa, chatarra |
| Encargos | Muro del pasillo, a la izquierda de la ventanilla | El tablón de corcho con las fichas |
| Para vivir | Detrás del tabique (z < −1,5), pasando una manta colgada | El catre, la estufa con su tubo hasta la rejilla de la bóveda, la radio, tus cosas |
| Planificar | Fondo derecho | La mesa con el cuaderno y el tablero de la pared (Fase 3) |

**Personalidad**: el antiguo cartel de CONSIGNA pintado encima de la ventanilla; las baldas con sus números de chapa; maletas que nadie recogió; su silla con el cojín hundido; el calendario; una lista de deudas clavada en la pared; dibujos a lápiz en los azulejos; una planta muerta bajo la lámpara; la gotera que deja óxido en la tubería. Lo que pones tú (la manta, tus cosas, los carteles de las categorías) se nota distinto: más nuevo, más cuidado.

## 2. Controles

| Tecla | Qué hace |
|---|---|
| F | Coger y soltar; usar lo que tienes delante (abrir una caja, la puerta, la persiana, la llave de la pila, el catre…) |
| Botón izquierdo (mantener) | Trabajar con lo que llevas sobre lo que tienes delante, moviendo el ratón: barrer, fregar, frotar, atornillar, hacer palanca, cepillar, escribir, comer |
| Botón derecho (mantener) | Acercarte lo que llevas y girarlo para inspeccionarlo |
| Rueda | Con una etiqueta o un fajo de billetes en la mano: cambiar el precio o el dinero |

Todo lo que se trabaja avanza con el movimiento del ratón, no con el tiempo: frotar más rápido limpia antes, y parar es parar. Cada herramienta tiene su gesto: barrer y fregar son pasadas largas; cepillar y limpiar contactos, frotar corto; atornillar y la bombilla, círculos; la palanca, tirar hacia abajo.

## 3. El día

```
mañana: aviso bajo la persiana ─ subir la persiana ─ clientes ─ procesar lo que hay ─ comer ─ pagar ─ dormir (se guarda)
```

- **La hora** corre sola (dos segundos por minuto: un día, de las 7 a medianoche, son unos 34 minutos). La marcan el reloj de pared de la consigna y el de pulsera. A medianoche te quedas dormido donde estés.
- **Cada mañana**, una nota deslizada bajo la persiana: el impuesto del día, y a veces un aviso de la estación.
- **Los clientes** solo vienen con la persiana subida, entre las 9 y las 19.
- **Dormir** en el catre termina el día: se cobra lo que se debe, cuenta lo que has comido y se guarda la partida.

## 4. Los sistemas

### 4.1 El primer día (F2-05)

Te despiertas en el catre el primer día. En la puerta hay clavada una **nota de la administración** con lo que hay que hacer antes de abrir; cada cosa se tacha sola cuando la haces:

1. **Quitar las telarañas**: con la escoba (pasadas) o a mano.
2. **Barrer** el polvo y los escombros del suelo: cada mancha de polvo se va con pasadas de escoba y deja un montoncito de basura.
3. **Fregar** las manchas: mojar la fregona en el cubo y frotar.
4. **Sacar la basura**: los papeles, las latas vacías, los cristales y los montoncitos van a la bolsa del cubo de basura; la bolsa llena se cierra y se lleva al contenedor del pasillo.
5. **Vaciar las cajas del antiguo dueño**: al abrirlas sale lo que tenían (tus primeras herramientas, algo de mercancía, cosas para reparar, alguna contaminada).
6. **Cambiar la bombilla** de la lámpara del mostrador: desenroscar la fundida, enroscar la nueva (están en una de las cajas).
7. **Desatascar la persiana** con la palanca; después sube y baja con F.
8. **Encender la estufa**: leña dentro y una cerilla.

Al acabar, el local ha cambiado: limpio, con luz cálida, la estufa encendida y la persiana arriba. La nota se queda en la puerta, tachada.

### 4.2 Dosímetro y descontaminación (F2-06)

- **El dosímetro** se lleva en la mano: la aguja marca lo que hay cerca (cada objeto contaminado suma según lo cerca que esté) y el piloto parpadea más deprisa cuanto más marca. No hay números en pantalla: es la aguja.
- **La pila**: dejas el objeto dentro y abres la llave; el agua le va quitando contaminación mientras corre. Con el **cepillo** se frota lo que está en la pila (quita más, y más deprisa). Lo que no se limpia (la ropa empapada, lo muy contaminado) se **embolsa**: con una bolsa del rollo en la mano, botón izquierdo sobre el objeto. Embolsado ya no contamina lo de alrededor, pero vale lo que vale contaminado.
- Tener cerca algo contaminado suma dosis (`GameState.dose`); en la Fase 2 solo se acumula y lo marca el dosímetro.

### 4.3 El banco de trabajo (F2-07)

Lo roto se deja en el tapete del banco y se repara por pasos, cada uno con su herramienta y su gesto:

| Paso | Herramienta | Gesto |
|---|---|---|
| Atornillar o desatornillar | Destornillador | Círculos sobre el tornillo |
| Limpiar contactos | Cepillo de alambre | Frotar corto |
| Coser | Aguja e hilo | Pasadas a lo largo de la costura |
| Cambiar una pieza | Las manos | Sacar la pieza de otro objeto roto igual y ponerla |

Cada objeto reparable tiene su receta de pasos (`data/reparaciones/`). Con cada paso, el estado sube; al acabar, queda como nuevo menos lo que ya traía gastado. Para empezar: la radio de bolsillo (tapa con tornillos, contactos, una válvula), la linterna (contactos, bombilla) y las botas (costura).

### 4.4 Báscula, etiquetas y estanterías (F2-08)

- **La báscula**: lo que pones en el plato mueve la aguja. La chatarra y los metales se venden al peso: pesarlos fija su valor.
- **Las etiquetas**: de la caja de etiquetas sale una en blanco. Con la etiqueta en la mano, la rueda cambia el precio y lo escribe a mano en ella; botón izquierdo sobre un objeto la ata con cordel. El precio se ve en la etiqueta, colgando del objeto.
- **Las estanterías**: cada balda lleva el cartel de su categoría. Lo que está en una balda es mercancía: es lo que buscan los clientes.

### 4.5 El mostrador y los clientes (F2-09)

Con la persiana subida, los clientes llegan por el pasillo hasta la ventanilla y dejan en el mostrador **un papelito** con lo que quieren (un dibujo y dos palabras, con su letra). No hablan.

- **Comprarte**: pones en el mostrador lo que piden. El cliente mira la etiqueta. Si le parece bien, deja los billetes; si le parece caro, deja menos (su oferta) y espera. Coger los billetes es aceptar; quitarle el objeto es no venderlo. Si no aceptas, a veces sube una vez; si no, se va. Sin etiqueta, ofrece lo que cree que vale.
- **Venderte**: dejan un objeto con un papel con su precio. Si lo quieres, pones al lado un fajo con ese dinero (de la caja de los rublos: con el fajo en la mano, la rueda cuenta los billetes). Si pones menos, se lo piensa: por poco menos, acepta.
- **La caja de los rublos**: el dinero del depósito. F la abre; de dentro se saca un fajo; los billetes que se cogen del mostrador entran solos.
- El primer cliente es **el relojero**: busca piezas, relojes, radios y herramientas, paga bien lo que está reparado y deja encargos.

### 4.6 Encargos y libro de cuentas (F2-10)

- **Los encargos** son fichas que los clientes clavan en el tablón de corcho: qué quieren, cuánto pagan, hasta qué día y **una pista, no un mapa** ("Bloque 7, cuarto piso, la puerta con un gato pintado"). Se entregan en el mostrador cuando vuelve quien lo encargó. Uno caducado se tacha.
- **El libro de cuentas**, sobre el mostrador: F lo abre y se ve de cerca, escrito a mano, día por día: ventas, compras, comida, el impuesto (con el recibo grapado y su sello de PAGADO) y lo que queda en la caja.

### 4.7 Impuesto, comida y hambre (F2-11)

- **El impuesto**: 20 ₽ al día. Se paga en la **ventanilla de la administración**, en el pasillo: un fajo por la ranura del buzón. A la mañana siguiente aparece el recibo con el sello bajo la persiana. Lo que no se paga se debe; con 60 ₽ de deuda, la administración **precinta el mostrador** (una tira de papel con sellos): no se puede vender hasta pagar.
- **La comida**: el puesto de al lado vende sopa (10 ₽: un día) y pan (4 ₽: medio día). Se paga dejando el dinero en su mostrador; la vendedora te pone el cuenco delante. Se come con el botón izquierdo. También vale lo que encuentres arriba (las latas).
- **El hambre**: un día sin comer, las manos tiemblan y andas más despacio; tres días, el tramado invade los bordes de la vista; cinco, mueres.

### 4.8 El trozo de estación (F2-12)

Se recorre el pasillo frente al depósito (6 m de ancho y unos 30 de largo):

- **El puesto de comida**, pegado al depósito: un quiosco con el samovar, las ollas humeando, la pizarra con los precios y la vendedora.
- **El tablón de avisos**, enfrente: avisos de la administración, objetos perdidos, normas de la estación, dibujos de niños.
- **La ventanilla de la administración**, con su buzón de pagos.
- **El contenedor** de la basura.
- **La escalera mecánica**, al fondo: tres escaleras paradas que suben a oscuras hacia la compuerta (en la Fase 3 se sube). La reja de abajo está cerrada.
- El resto de la estación se ve por los arcos (tiendas de campaña, ropa tendida, luces, humo, gente), pero no se puede pasar: vallas y bultos.

### 4.9 Respuesta táctil (F2-13)

Sin sonido por ahora. Polvo al barrer, al soltar algo en el suelo y al abrir las cajas; los papeles se deslizan y se asientan; el sello golpea; la persiana tiembla atascada; la lámpara se balancea al cambiar la bombilla; las agujas oscilan antes de pararse; lo que se suelta se asienta con un pequeño rebote.

### 4.10 Dos jugadores a la vez (F2-14)

Todo lo hace el anfitrión y lo ven todos: la limpieza, el estado de cada cosa, el dinero, la hora, los clientes y los tratos. Cada jugador trabaja con lo suyo (lo que lleva en las manos, lo que mira de cerca) y pide al anfitrión que lo aplique.

## 5. Cómo está hecho

| Pieza | Qué es |
|---|---|
| `GameState` | El estado de la partida: día, hora, rublos, deuda, hambre, dosis, libro de cuentas, encargos. Lo cambia el anfitrión, se replica a los invitados y se guarda |
| `DepotWorld` | El estado de cada cosa fija del local (cada mancha, cada telaraña, la bombilla, la persiana, la estufa…), por su identificador. Replicado y guardado |
| `Fixture` | Una cosa fija con estado: se pinta según lo que dice `DepotWorld` |
| `Workable` | Lo que se puede trabajar con una herramienta: qué herramientas acepta y cuánto trabajo pide |
| `Player` | Con algo en la mano y el botón izquierdo, mide el gesto y pide al anfitrión que aplique el trabajo |
| `CloseUp` | Ver algo de cerca (el libro, una nota, una ficha) |
| `WorldItems` | Los objetos sueltos; ahora también se guardan |
| `Customer`, `CustomerDirector` | Los clientes: cuándo vienen, cómo andan, qué quieren y el trato |

Los datos: las fichas de los objetos (`data/items/`, con qué herramienta son y qué hacen), las reparaciones (`data/reparaciones/`) y los clientes (`data/clientes/`).

## 6. Estado

| Tarea | Estado |
|---|---|
| F2-00 Los protagonistas | Hecha (aprobada) |
| F2-05 El primer día | Por hacer |
| F2-06 Dosímetro y descontaminación | Por hacer |
| F2-07 Banco de trabajo | Por hacer |
| F2-08 Báscula, etiquetas, estanterías | Por hacer |
| F2-09 Mostrador y cliente | Por hacer |
| F2-10 Encargos y libro de cuentas | Por hacer |
| F2-11 Impuesto y comida | Por hacer |
| F2-12 El trozo de estación | Por hacer |
| F2-13 Respuesta táctil | Por hacer |
| F2-14 Todo sincronizado | Por hacer |
