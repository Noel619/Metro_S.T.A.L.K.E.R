// Hitos de la ciudad: como las fachadas, pero la niebla nunca los tapa del todo
// (hito_niebla_max). Sin mapas, el jugador se orienta con lo que ve de lejos: la
// torre de la Casa de los Sóviets, las chimeneas, el elevador… (docs/CIUDAD.md).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_FACHADA
#define TINTA_HITO
#include "res://assets/shaders/tinta.gdshaderinc"
