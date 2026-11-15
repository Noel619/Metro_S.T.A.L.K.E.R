// Suelo de la ciudad: el sombreado por bandas de tinta.gdshader con el color y la
// nieve de data/ciudad/suelo.png (calzadas, aceras, plazas, hielo, vías, patios
// y escombros), proyectado desde arriba. Lo usa la maqueta (F3-15).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_SUELO
#include "res://assets/shaders/tinta.gdshaderinc"
