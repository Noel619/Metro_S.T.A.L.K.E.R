extends Node
## Base mínima para los tests unitarios.
##
## Cada método que empieza por "test_" es un test. El ejecutor
## (tests/run_tests.gd) crea una instancia nueva por test, la añade al árbol y
## llama a before_each(), al test y a after_each().

var failures: PackedStringArray = []
var current_test: String = ""


func before_each() -> void:
	pass


func after_each() -> void:
	pass


func assert_true(condition: bool, message: String = "") -> void:
	if not condition:
		_fail("se esperaba verdadero. " + message)


func assert_false(condition: bool, message: String = "") -> void:
	if condition:
		_fail("se esperaba falso. " + message)


func assert_eq(actual: Variant, expected: Variant, message: String = "") -> void:
	if typeof(actual) != typeof(expected) or actual != expected:
		_fail(
			(
				"se esperaba %s y se obtuvo %s. %s"
				% [var_to_str(expected), var_to_str(actual), message]
			)
		)


func assert_almost(
	actual: float, expected: float, tolerance: float = 0.0001, message: String = ""
) -> void:
	if absf(actual - expected) > tolerance:
		_fail("se esperaba %f ± %f y se obtuvo %f. %s" % [expected, tolerance, actual, message])


func _fail(text: String) -> void:
	failures.append(text)
