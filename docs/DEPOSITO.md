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
| F | Coger y soltar; usar lo que tienes delante (la puerta, la persiana, la llave de la pila, la caja de los rublos, la caja de las etiquetas, el rollo de bolsas, el cubo, el catre) y leer los papeles (la nota de la puerta, el libro de cuentas, las fichas del corcho, el aviso de la mañana) |
| Botón izquierdo (mantener) | Trabajar con lo que llevas sobre lo que tienes delante, moviendo el ratón: barrer, fregar, quitar telarañas, abrir cajas, atornillar, hacer palanca, cepillar, coser, atar una etiqueta, embolsar, tirar a la basura, pagar, comer |
| Botón derecho (mantener) | Acercarte lo que llevas y girarlo para inspeccionarlo |
| Rueda | Con una etiqueta o un fajo de billetes en la mano: cambiar el precio o el dinero (de uno en uno hasta 20, de cinco hasta 100 y de diez en adelante) |

Todo lo que se trabaja avanza con el movimiento del ratón, no con el tiempo: frotar más rápido limpia antes, y parar es parar. Cada herramienta tiene su gesto: barrer, fregar, quitar telarañas y coser son pasadas largas; cepillar y limpiar contactos, frotar corto; atornillar y la bombilla, círculos (en el sentido del reloj aprieta, al revés afloja); la palanca y abrir una caja, tirar hacia abajo. Lo que es un momento (atar una etiqueta, embolsar, tirar algo, pagar, comer, cargar la estufa) se hace manteniendo el botón.

## 3. El día

```
mañana: aviso bajo la persiana ─ subir la persiana ─ clientes ─ procesar lo que hay ─ comer ─ pagar ─ dormir (se guarda)
```

- **La hora** corre sola (dos segundos por minuto: un día, de las 7 a medianoche, son unos 34 minutos). La marca el reloj de pared de la consigna, junto a la puerta. A medianoche te quedas dormido donde estés.
- **Cada mañana**, una nota deslizada bajo la persiana: el impuesto del día, y a veces un aviso de la estación.
- **Los clientes** solo vienen con la persiana subida, entre las 9 y las 19.
- **Dormir** en el catre (a partir de las 18; antes solo cruje) termina el día: fundido a negro, se carga el impuesto, cuenta lo que has comido, se guarda la partida y todos despiertan a las 7 junto al catre.

## 4. Los sistemas

### 4.1 El primer día (F2-05)

Te despiertas en el catre el primer día. En la puerta hay clavada una **nota de la administración** con lo que hay que hacer antes de abrir; cada cosa se tacha sola cuando la haces:

1. **Quitar las telarañas** de los rincones: con la escoba o a mano, a pasadas.
2. **Barrer** el polvo del suelo: cada mancha se aclara con cada pasada de escoba y levanta polvo.
3. **Fregar** las manchas oscuras con la fregona, a pasadas.
4. **Sacar la basura**: los papeles, el trapo, las latas aplastadas, la botella rota, la bombilla fundida y el cartón de las cajas vaciadas van al cubo (con la basura en la mano, mantener el botón sobre él); F en el cubo saca la bolsa llena, que se lleva al contenedor del pasillo (mantener el botón sobre él).
5. **Vaciar las cajas del antiguo dueño**: con las manos vacías, tirar de las solapas (botón izquierdo, hacia abajo). Sale lo que tenían alrededor (la bombilla, las cerillas, tus primeras herramientas, cosas para reparar, algo contaminado) y la caja de cartón se queda plegada.
6. **Cambiar la bombilla** de la lámpara del mostrador: con la mano, círculos al revés del reloj hasta que cae la fundida; con la nueva en la mano, círculos en el sentido del reloj. La lámpara se balancea.
7. **Desatascar la persiana** con la palanca (está en el banco), tirando hacia abajo; atascada, F solo la hace temblar. Después sube y baja con F.
8. **Encender la estufa**: un haz de leña dentro (hay dos al lado) y una cerilla (cada caja trae doce). Arde unas catorce horas con la estufa llena.

Al acabar, el local ha cambiado: limpio, con luz cálida, la estufa encendida y la persiana arriba. La nota se queda en la puerta, tachada.

### 4.2 Dosímetro y descontaminación (F2-06)

- **El dosímetro** se lleva en la mano: la aguja marca lo que hay cerca (cada objeto contaminado suma según lo cerca que esté) y el piloto parpadea más deprisa cuanto más marca. No hay números en pantalla: es la aguja.
- **La pila**: dejas el objeto dentro y abres la llave (F); el agua le va quitando contaminación mientras corre. Con el **cepillo** se frota lo que está en la pila (quita más, y más deprisa). Lo que no se limpia (la ropa empapada, lo muy contaminado) se **embolsa**: F en el rollo de bolsas da una, y con ella en la mano se mantiene el botón sobre el objeto. Embolsado ya no contamina lo de alrededor (ni lo marca el dosímetro), pero vale lo que vale contaminado. Los clientes no compran lo contaminado sin embolsar.
- Tener cerca algo contaminado suma dosis (`GameState.dose`); en la Fase 2 solo se acumula y lo marca el dosímetro.

### 4.3 El banco de trabajo (F2-07)

Lo roto se deja en el tapete del banco y se repara por pasos, cada uno con su herramienta y su gesto:

| Paso | Herramienta | Gesto |
|---|---|---|
| Atornillar o desatornillar | Destornillador | Círculos (al revés del reloj afloja, en el sentido del reloj aprieta) |
| Quitar o poner una tapa | Las manos | Tirar hacia abajo; mantener |
| Limpiar contactos | Cepillo de alambre | Frotar corto |
| Coser | Aguja e hilo | Pasadas largas |

Cada objeto reparable tiene su receta de pasos (`data/reparaciones/`). Solo se repara sobre el tapete del banco, y se ve: los tornillos salen girando, la tapa se aparta, los contactos pasan del verde del óxido al latón, la raja de la costura se cierra. Al acabar, queda como nuevo menos lo que ya traía gastado. Las tres recetas:

- **Radio de bolsillo**: quitar los cuatro tornillos de la tapa, quitar la tapa, limpiar los contactos, poner la tapa, apretar los tornillos.
- **Linterna**: limpiar los contactos y apretar el cabezal.
- **Botas**: coser la costura del costado.

### 4.4 Báscula, etiquetas y estanterías (F2-08)

- **La báscula** del mostrador: lo que se deja en los platos mueve la aguja (hasta 20 kg), que oscila antes de pararse. La chatarra y los metales (el cobre, la leña) se venden al peso.
- **Las etiquetas**: la caja de las etiquetas está en el banco; F da una en blanco. Con la etiqueta en la mano, la rueda cambia el precio y lo escribe a lápiz en ella; mantener el botón sobre un objeto la ata con su cordel. El precio se ve en la etiqueta, colgando del objeto.
- **Las estanterías**: cada piso de las baldas de la consigna lleva el cartel de su categoría (comida, medicinas, herramientas, electrónica, ropa, chatarra, envases), escrito en papel nuevo: son tuyos.

### 4.5 El mostrador y los clientes (F2-09)

Con la persiana subida, los clientes llegan por el pasillo hasta la ventanilla y dejan en el mostrador **un papelito** con lo que quieren (un dibujo y dos palabras, con su letra). No hablan.

- **Comprarte**: pones en el mostrador lo que piden. El cliente mira la etiqueta. Si le parece bien, deja esos billetes; si le parece caro, deja lo que cree que vale (su oferta) y espera. Coger los billetes es aceptar; quitarle el objeto es no venderlo. Si no aceptas, sube una vez, a medio camino; si tampoco, se va. Sin etiqueta, ofrece algo menos de lo que cree que vale. Lo reparado lo paga mejor; lo contaminado sin embolsar no lo quiere.
- **Venderte**: dejan un objeto y un papel con su precio. Si lo quieres, pones al lado un fajo con ese dinero (de la caja de los rublos: con el fajo en la mano, la rueda cuenta los billetes). Si pones menos, se lo piensa: por poco menos (hasta un 15 %), acepta; si pones de más, deja la vuelta.
- **La caja de los rublos**: el dinero del depósito. F saca un fajo de diez rublos (la tapa se abre); con él en la mano, la rueda saca o devuelve billetes, y mantener el botón sobre la caja lo guarda entero. Los billetes de un cliente que se cogen del mostrador entran solos.
- El primer cliente es **el relojero**: busca relojes, radios, linternas y brújulas, paga bien lo que está reparado y, si no encuentra nada, deja un encargo: una radio de bolsillo que suene (la de las cajas del antiguo dueño, arreglada en el banco). Luego vienen **la vecina** de la lavandería (comida, medicinas y envases; a veces vende) y **el chatarrero** (compra chatarra y herramientas; vende cobre). Cada uno firma sus papelitos.

### 4.6 Encargos y libro de cuentas (F2-10)

- **Los encargos** son fichas que los clientes dejan en el tablón de corcho: qué quieren, cuánto pagan, hasta qué día y **una pista, no un mapa**. Se entregan en el mostrador cuando vuelve quien lo encargó (a partir del día siguiente, antes que nadie). Uno caducado se tacha; uno entregado se quita. F sobre una ficha la acerca.
- **El libro de cuentas**, sobre el mostrador: F lo abre y se ve de cerca, escrito a mano, día por día: ventas, compras, comida, el impuesto (con el recibo grapado y su sello de PAGADO) y lo que queda en la caja.

### 4.7 Impuesto, comida y hambre (F2-11)

- **El impuesto**: 20 ₽ al día. Se paga en la **ventanilla de la administración**, en el pasillo: un fajo por la ranura del buzón. A la mañana siguiente aparece el recibo con el sello bajo la persiana. Lo que no se paga se debe; con 60 ₽ de deuda, la administración **precinta el mostrador** (una tira de papel con sellos): no se puede vender hasta pagar.
- **La comida**: el puesto de al lado vende sopa (10 ₽: un día) y pan (4 ₽: medio día). Se paga dejando un fajo en su mostrador: la vendedora lo coge, pone el cuenco (o el pan) y, si sobra, la vuelta. Se come manteniendo el botón con la comida en la mano. También valen las latas de conserva.
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

Sin sonido por ahora (decisión del equipo). Polvo al barrer, al quitar telarañas, al soltar algo pesado en el suelo, al abrir las cajas y al sacar la bolsa del cubo; los papeles caen y se asientan; la persiana tiembla atascada; la lámpara se balancea al cambiar la bombilla; las agujas de la báscula y del dosímetro oscilan antes de pararse y el piloto parpadea más deprisa cuanto más marca; las tapas de la caja de los rublos y del contenedor se levantan y caen; el libro se abre al leerlo; el catre cruje; la estufa da luz que tiembla; los clientes ponen cara según el trato.

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
| `PaperCard`, `CloseUp` | Los papeles del mundo (un SVG con el texto escrito encima) y verlos de cerca; el mismo diccionario sirve para los dos |
| `WorldItems` | Los objetos sueltos; también se guardan. Al crear cada uno, `ItemBehaviors` le pone lo que admite (etiquetar, embolsar, cepillar, comer, abrir, reparar) e `ItemView` dibuja su estado (la etiqueta, la bolsa, la cifra, las piezas, la aguja) |
| `DepotRoom`, `Station` | Lo fijo: la consigna con sus muebles y luces, y el pasillo de la estación |
| `DepotChores` | El primer día: manchas, telarañas, persiana, bombilla, estufa, cubo, contenedor, cajas y la nota |
| `DepotWorkshop` | La pila, el cepillo y las bolsas, el banco, la báscula, las etiquetas y la rueda, comer |
| `DepotCounter` | La caja de los rublos, el libro, el corcho, el reloj y los clientes (`Customer`, con sus datos en `CustomerData`) |
| `DepotStation` | El puesto de comida y la vendedora, el buzón de los pagos, los avisos, el recibo y el precinto |
| `DepotDay` | Dormir, medianoche, guardar, despertar y el hambre |

Los datos: las fichas de los objetos (`data/items/`, con qué herramienta son y qué hacen), las reparaciones (`data/reparaciones/`) y los clientes (`data/clientes/`).

Para verlo sin jugar: `scenes/debug/revision_deposito.tscn` monta el depósito con cámaras fijas (el primer día; con `--abierto`, el local limpio y abierto, con el relojero en la ventanilla). Las pruebas están en `tests/unit/test_depot_play.gd` (el recorrido entero en solitario) y `tests/net/net_depot.gd` (dos equipos).

## 6. Estado

| Tarea | Estado |
|---|---|
| F2-00 Los protagonistas | Hecha (aprobada) |
| F2-05 El primer día | Hecha |
| F2-06 Dosímetro y descontaminación | Hecha |
| F2-07 Banco de trabajo | Hecha (tres recetas) |
| F2-08 Báscula, etiquetas, estanterías | Hecha |
| F2-09 Mostrador y cliente | Hecha (tres clientes) |
| F2-10 Encargos y libro de cuentas | Hecha |
| F2-11 Impuesto y comida | Hecha |
| F2-12 El trozo de estación | Hecha |
| F2-13 Respuesta táctil | Hecha, sin sonido (decisión: por ahora no) |
| F2-14 Todo sincronizado | Hecha: lo cambia el anfitrión y lo ven todos; la prueba de red recorre parte del primer día y una venta con dos equipos |

Pendiente para más adelante: el sonido y mojar la fregona en el cubo. Los clientes y la vendedora tienen modelo y cara propios (D-058).
