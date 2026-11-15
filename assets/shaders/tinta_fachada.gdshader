// Fachadas de la maqueta (F3-15): el sombreado por bandas de tinta.gdshader con
// las ventanas pintadas (albedo_texture) solo donde el alfa del color de vértice
// lo pide; las cubiertas y las caras sin ventanas llevan alfa 0.
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#define TINTA_FACHADA
#include "res://assets/shaders/tinta.gdshaderinc"
