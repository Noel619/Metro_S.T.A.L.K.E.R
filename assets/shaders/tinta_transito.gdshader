// Pavimentos de la ciudad (la red de tránsito de la maqueta): el sombreado por bandas de
// tinta.gdshader con la textura del pavimento (asfalto, losas, granito…) multiplicada por
// el color de cada superficie, y nieve a parches: el alfa del color de vértice dice cuánta
// cubre cada clase (más en las aceras que en la calzada; nada en lo vertical).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_TRANSITO
#include "res://assets/shaders/tinta.gdshaderinc"
