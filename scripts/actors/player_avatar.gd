class_name PlayerAvatar
extends Node3D
## El cuerpo de un jugador tal como lo ven los demás.
##
## Carga el modelo del protagonista (chico o chica), lo tiñe con el color del
## jugador y lo anima. El movimiento es "a saltos", como en el dibujo animado:
## la animación solo avanza unas pocas veces por segundo ([member animation_fps]).
##
## Quien controla al jugador solo tiene que decirle a qué velocidad anda, si
## lleva algo en las manos y hacia dónde mira; en la superficie, también si va
## agachado, si corre y lo que se asoma (F3-01). El avatar mira hacia -Z, como
## cualquier cuerpo de Godot.

## Los dos protagonistas y la gente de la estación (tools/blender/recipes/personajes.py).
const MODELS: Dictionary = {
	"chico": "res://assets/models/jugador_chico.glb",
	"chica": "res://assets/models/jugador_chica.glb",
	"relojero": "res://assets/models/persona_relojero.glb",
	"vendedora": "res://assets/models/persona_vendedora.glb",
	"vecina": "res://assets/models/persona_vecina.glb",
	"chatarrero": "res://assets/models/persona_chatarrero.glb",
}
## Color de la bufanda de cada jugador, por orden de llegada (docs/ESTILO.md).
## El rojo se reserva para lo importante, así que no hay jugador rojo.
const PLAYER_COLORS: Array[Color] = [
	Color("#9a7a2e"),
	Color("#2c6468"),
	Color("#7a4a30"),
	Color("#42558a"),
]
## Casillas de la lámina de caras (tools/svg/generate.mjs), en orden.
const EXPRESSIONS: Array[StringName] = [
	&"neutro", &"parpadeo", &"esfuerzo", &"miedo", &"sonrisa", &"sorpresa", &"dolor", &"cansado"
]
const FACE_COLUMNS: int = 4
const FACE_ROWS: int = 2
## Expresiones con los ojos abiertos: las únicas en las que se parpadea.
const BLINKING: Array[StringName] = [&"neutro", &"esfuerzo", &"cansado"]
## Metros que avanza el ciclo de caminar, el de andar agachado y el de correr
## (tools/blender/personaje_anim.py).
const WALK_DISTANCE: float = 0.9
const CROUCH_WALK_DISTANCE: float = 0.7
const RUN_DISTANCE: float = 2.4
const WALK_THRESHOLD: float = 0.15
const BLEND_TIME: float = 0.25
const BLINK_TIME: float = 0.13
## Cadenas de huesos sueltos que se mueven solas: [raíz, punta].
const LOOSE_CHAINS: Array[PackedStringArray] = [["Bufanda1", "Bufanda2"], ["Trenza1", "Trenza3"]]

@export_enum("chico", "chica") var variant: String = "chico":
	set(value):
		variant = value
		if is_node_ready():
			_rebuild()
## Puesto del jugador en la partida (0 es el anfitrión): decide su color.
@export_range(0, 3) var player_slot: int = 0:
	set(value):
		player_slot = value
		_apply_color()
## Otro color para la bufanda (los que no son jugadores: los clientes, la
## vendedora). Transparente: el del puesto del jugador.
@export var cloth_color: Color = Color(0, 0, 0, 0):
	set(value):
		cloth_color = value
		_apply_color()
## Fotogramas por segundo del movimiento "a saltos".
@export_range(4.0, 60.0) var animation_fps: float = 12.0
@export var backpack_visible: bool = true:
	set(value):
		backpack_visible = value
		_apply_equipment()
@export var bag_visible: bool = true:
	set(value):
		bag_visible = value
		_apply_equipment()
## La mascarilla colgada al pecho (se oculta cuando la lleva puesta).
@export var mask_visible: bool = true:
	set(value):
		mask_visible = value
		_apply_equipment()
## Solo se ve su sombra: para el jugador local, que mira desde dentro.
@export var shadow_only: bool = false:
	set(value):
		shadow_only = value
		_apply_shadow_only()

## Velocidad a la que anda, en m/s.
var speed: float = 0.0
## Lleva algo entre las manos.
var carrying: bool = false
## Va agachado; corre (con la cara del esfuerzo).
var crouching: bool = false
var running: bool = false
## Lo que se asoma, de -1 (a la izquierda) a 1 (a la derecha): inclina el tronco.
var lean: float = 0.0:
	set(value):
		lean = value
		if _look != null:
			_look.lean = value
## Hacia dónde mira, en radianes: positivo hacia arriba.
var look_pitch: float = 0.0:
	set(value):
		look_pitch = value
		if _look != null:
			_look.pitch = value
var expression: StringName = &"neutro":
	set(value):
		expression = value if EXPRESSIONS.has(value) else &"neutro"
		_show_face(expression)

var _model: Node3D
var _player: AnimationPlayer
var _skeleton: Skeleton3D
var _look: LookModifier
var _face: ShaderMaterial
var _cloth: ShaderMaterial
var _pending: float = 0.0
var _frozen: bool = false
var _blink_in: float = 3.0
var _blink_left: float = 0.0
var _rng: RandomNumberGenerator = RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = hash(name) + player_slot
	_rebuild()


func _process(delta: float) -> void:
	if _player == null:
		return
	_blink(delta)
	if _frozen:
		return
	_choose_animation()
	_pending += delta
	if _pending >= 1.0 / animation_fps:
		_player.advance(_pending)
		_pending = 0.0


## Deja el cuerpo quieto en un instante de una animación (para capturas y pruebas).
func preview(animation: StringName, at: float) -> void:
	_frozen = true
	_player.play(animation)
	_player.seek(at, true)
	_player.advance(0.0)


## Vuelve a animarse solo después de [method preview].
func resume() -> void:
	_frozen = false


func get_skeleton() -> Skeleton3D:
	return _skeleton


## La animación que está sonando (para las pruebas).
func animation() -> StringName:
	return StringName(_player.current_animation) if _player != null else &""


func _rebuild() -> void:
	if _model != null:
		_model.free()
	_model = load(MODELS[variant]).instantiate()
	# Los modelos miran a +Z (perfil humanoide); los cuerpos de Godot, a -Z.
	_model.rotation.y = PI
	add_child(_model)
	_skeleton = _model.find_child("Skeleton3D", true, false) as Skeleton3D
	_player = _model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	_player.play(&"reposo")
	_player.advance(0.0)
	_look = LookModifier.new()
	_look.name = "Mirada"
	_look.pitch = look_pitch
	_look.lean = lean
	_skeleton.add_child(_look)
	_add_loose_chains()
	_face = _own_material("cara")
	_cloth = _own_material("bufanda")
	_apply_color()
	_apply_equipment()
	_apply_shadow_only()
	_show_face(expression)


## Cada avatar necesita su copia del material que cambia (el color, la cara).
func _own_material(mesh_name: String) -> ShaderMaterial:
	var mesh: MeshInstance3D = _model.find_child(mesh_name, true, false) as MeshInstance3D
	if mesh == null:
		return null
	var material: ShaderMaterial = mesh.get_surface_override_material(0).duplicate()
	mesh.set_surface_override_material(0, material)
	return material


## La bufanda y la trenza cuelgan: siguen al cuerpo con algo de retraso.
func _add_loose_chains() -> void:
	var chains: Array[PackedStringArray] = []
	for chain: PackedStringArray in LOOSE_CHAINS:
		if _skeleton.find_bone(chain[0]) >= 0:
			chains.append(chain)
	if chains.is_empty():
		return
	var springs: SpringBoneSimulator3D = SpringBoneSimulator3D.new()
	springs.name = "Colgantes"
	_skeleton.add_child(springs)
	springs.setting_count = chains.size()
	for index: int in chains.size():
		springs.set_root_bone_name(index, chains[index][0])
		springs.set_end_bone_name(index, chains[index][1])
		springs.set_stiffness(index, 2.5)
		springs.set_drag(index, 0.55)
		springs.set_gravity(index, 0.4)
		springs.set_radius(index, 0.02)


func _choose_animation() -> void:
	var walking: bool = speed > WALK_THRESHOLD
	var animation: String = "caminar" if walking else "reposo"
	var distance: float = WALK_DISTANCE
	if crouching:
		animation = "caminar_agachado" if walking else "agachado"
		distance = CROUCH_WALK_DISTANCE
	elif walking and running:
		animation = "correr"
		distance = RUN_DISTANCE
	if carrying:
		animation += "_cargando"
	_player.speed_scale = speed / distance if walking else 1.0
	if _player.current_animation != animation:
		_player.play(StringName(animation), BLEND_TIME)


func _blink(delta: float) -> void:
	if _blink_left > 0.0:
		_blink_left -= delta
		if _blink_left <= 0.0:
			_show_face(expression)
		return
	_blink_in -= delta
	if _blink_in <= 0.0:
		_blink_in = _rng.randf_range(2.0, 6.0)
		if BLINKING.has(expression):
			_blink_left = BLINK_TIME
			_show_face(&"parpadeo")


func _show_face(face: StringName) -> void:
	if _face == null:
		return
	var index: int = maxi(0, EXPRESSIONS.find(face))
	var cell: Vector2 = Vector2(index % FACE_COLUMNS, index / FACE_COLUMNS)
	_face.set_shader_parameter("uv_offset", cell / Vector2(FACE_COLUMNS, FACE_ROWS))


func _apply_color() -> void:
	if _cloth != null:
		var color: Color = cloth_color if cloth_color.a > 0.0 else PLAYER_COLORS[player_slot]
		_cloth.set_shader_parameter("albedo_color", color)


func _apply_equipment() -> void:
	if _model == null:
		return
	for pair: Array in [
		["mochila", backpack_visible], ["zurron", bag_visible], ["mascarilla", mask_visible]
	]:
		var mesh: Node3D = _model.find_child(pair[0], true, false) as Node3D
		if mesh != null:
			mesh.visible = pair[1]


func _apply_shadow_only() -> void:
	if _model == null:
		return
	var mode: GeometryInstance3D.ShadowCastingSetting = (
		GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		if shadow_only
		else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	)
	for mesh: Node in _model.find_children("*", "MeshInstance3D", true, false):
		(mesh as MeshInstance3D).cast_shadow = mode
