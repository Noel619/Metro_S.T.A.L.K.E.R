// Muros del kit de arquitectura (F3-16): el sombreado por bandas de tinta.gdshader con
// la suciedad, los chorretones, el ladrillo, la plaqueta, el revoque caído y el hollín de
// los incendios. Todo se calcula en el espacio del mundo (sigue de una pieza a otra) o
// con los datos de cada instancia (BuildingKit los pone en INSTANCE_CUSTOM).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_MURO
#include "res://assets/shaders/tinta.gdshaderinc"
