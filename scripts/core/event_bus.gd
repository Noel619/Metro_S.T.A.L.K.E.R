extends Node
## Bus de señales globales. Solo declara señales: aquí no se guarda estado.
##
## Sirve para avisar de hechos que interesan a sistemas que no se conocen entre
## sí (por ejemplo, la economía y la interfaz). Para hablar entre nodos
## cercanos, mejor usar señales propias del nodo.

@warning_ignore_start("unused_signal")

## Empieza un día nuevo en la estación.
signal day_started(day: int)
## Termina el día, después de dormir y guardar.
signal day_ended(day: int)
## Cambian los rublos del depósito. [param delta] puede ser negativo.
signal rubles_changed(total: int, delta: int)
## La partida se ha guardado en disco.
signal game_saved
## Un jugador ha muerto. En solitario, es el final de la partida.
signal player_died(peer_id: int)
## Todos los jugadores han muerto: la partida se borra.
signal game_over
## Un jugador gira la rueda con algo en la mano (en el anfitrión): el precio de
## una etiqueta, los billetes de un fajo. [param step] es +1 o -1.
signal item_adjusted(player: Node, item: Node, step: int)
## Algo ha hecho ruido en [param where] (un paso, algo que cae, un golpe), con esa
## [param loudness] (un paso normal es 0,35; correr, casi 1). Lo oirán las criaturas
## y los saqueadores (F3-09). Solo en el anfitrión.
signal noise_made(where: Vector3, loudness: float, source: Node)

@warning_ignore_restore("unused_signal")
