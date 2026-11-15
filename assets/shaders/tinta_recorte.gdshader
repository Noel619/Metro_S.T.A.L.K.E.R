// Variante de tinta.gdshader con recorte por alfa (papeles, carteles, hojas).
// Se dibuja en la pasada opaca, así que también recibe contorno y tramado.
shader_type spatial;
render_mode diffuse_lambert, specular_disabled, cull_disabled;

#define TINTA_RECORTE
#include "res://assets/shaders/tinta.gdshaderinc"
