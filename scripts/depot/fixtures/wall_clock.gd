class_name WallClock
extends Node
## El reloj de pared de la consigna: marca la hora de la partida
## ([member GameState.minute]). La aguja de los minutos salta minuto a minuto,
## como los relojes de estación.

var model: Node3D
var _hours: Node3D
var _minutes: Node3D


func _ready() -> void:
	_hours = model.find_child("aguja_horas", true, false) as Node3D
	_minutes = model.find_child("aguja_minutos", true, false) as Node3D


func _process(_delta: float) -> void:
	var whole: int = int(GameState.minute)
	if _minutes != null:
		_minutes.rotation.z = -TAU * float(whole % 60) / 60.0
	if _hours != null:
		_hours.rotation.z = -TAU * fmod(GameState.minute / 60.0, 12.0) / 12.0
