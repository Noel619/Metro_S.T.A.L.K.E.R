class_name ItemData
extends Resource
## Ficha de un tipo de objeto: lo que es igual en todas las latas de conserva.
##
## Lo que cambia de un ejemplar a otro (su estado, lo contaminado que está) va
## en [ItemState]. Las fichas son recursos de texto en data/items/.

enum Category { COMIDA, MEDICINAS, HERRAMIENTAS, ELECTRONICA, ROPA, CHATARRA, ENVASES }

## Lo que pierde de valor un objeto contaminado del todo.
const CONTAMINATION_PENALTY: float = 0.8
## Por debajo de este estado, el objeto solo vale como chatarra.
const BROKEN_CONDITION: float = 0.15
const SCRAP_SHARE: float = 0.1

## Identificador único, igual que el nombre del archivo.
@export var id: StringName = &""
## Nombre para las etiquetas y el libro de cuentas.
@export var display_name: String = ""
@export var category: Category = Category.CHATARRA
## Modelo de assets/models/, sin extensión.
@export var model: String = ""
@export_range(0.01, 100.0, 0.01, "suffix:kg") var weight: float = 1.0
## Casillas que ocupa en la mochila, desde la esquina de arriba a la izquierda.
@export var grid_shape: Array[Vector2i] = [Vector2i.ZERO]
## De 0 (aguanta golpes) a 1 (se rompe si corres o te caes).
@export_range(0.0, 1.0) var fragility: float = 0.0
## Rublos por un ejemplar en perfecto estado y limpio.
@export var base_value: int = 1
## Se vende al peso (chatarra, metales): el valor es por kilo.
@export var sold_by_weight: bool = false
## Para qué sirve en la mano: lo que se trabaja con él ([Workable]). Por ejemplo
## &"escoba", &"fregona", &"palanca", &"destornillador", &"cepillo", &"cerillas",
## &"bombilla", &"bolsa", &"etiqueta", &"billetes", &"dosimetro", &"aguja" o
## &"comida". Vacío: no sirve de herramienta.
@export var tool: StringName = &""
## La punta con la que trabaja, en sus propios ejes (las cerdas de la escoba, la
## punta del destornillador). Cero: el centro del objeto.
@export var tip: Vector3 = Vector3.ZERO
## Lo que alimenta: 1 es la comida de un día. 0: no se come.
@export_range(0.0, 2.0, 0.05) var nutrition: float = 0.0
## Es basura: su sitio es la bolsa del cubo.
@export var trash: bool = false


## Ancho y alto de la forma en la cuadrícula de la mochila.
func grid_size() -> Vector2i:
	var size: Vector2i = Vector2i.ZERO
	for cell: Vector2i in grid_shape:
		size = size.max(cell + Vector2i.ONE)
	return size


## Las casillas que ocupa girado un cuarto de vuelta ([param turns] veces).
func rotated_shape(turns: int) -> Array[Vector2i]:
	var cells: Array[Vector2i] = grid_shape.duplicate()
	for _i in posmod(turns, 4):
		var height: int = 0
		for cell: Vector2i in cells:
			height = maxi(height, cell.y + 1)
		var turned: Array[Vector2i] = []
		for cell: Vector2i in cells:
			turned.append(Vector2i(height - 1 - cell.y, cell.x))
		cells = turned
	return cells


## Valor en rublos de un ejemplar según su estado y su contaminación (de 0 a 1).
func value(condition: float, contamination: float) -> int:
	var worth: float = base_value * (weight if sold_by_weight else 1.0)
	var state: float = clampf(condition, 0.0, 1.0)
	if state < BROKEN_CONDITION:
		worth *= SCRAP_SHARE
	else:
		worth *= lerpf(0.35, 1.0, state)
	worth *= 1.0 - CONTAMINATION_PENALTY * clampf(contamination, 0.0, 1.0)
	return maxi(0, roundi(worth))
