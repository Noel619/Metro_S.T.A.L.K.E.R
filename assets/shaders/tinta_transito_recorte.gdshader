// La pintura vial de la red de tránsito: como tinta_transito, pero recortada por el alfa
// de su textura (la pintura se ha ido a trozos y debajo se ve el asfalto).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_TRANSITO
#define TINTA_RECORTE
#include "res://assets/shaders/tinta.gdshaderinc"
