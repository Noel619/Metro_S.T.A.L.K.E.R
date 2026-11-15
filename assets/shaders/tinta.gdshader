// Sombreado por bandas de Tumansk: el material de todos los objetos.
//
// - La luz directa se reparte en tres bandas (sombra, medio tono, luz) leyendo
//   una fila de assets/textures/rampas.png. La banda de sombra vale 0: ahí solo
//   llega la luz ambiente, así que las sombras propias y las proyectadas tienen
//   el mismo color, como en una ilustración.
// - El color base sale del color por vértice (pintado en Blender con oclusión y
//   cavidades), multiplicado por el color y la textura del material.
// - Opcional: nieve en lo que mira hacia arriba, borde de luz y emisión.
// El contorno, el tramado y el papel los añade el post-proceso (post_tinta).
shader_type spatial;
render_mode diffuse_lambert, specular_disabled;

#include "res://assets/shaders/tinta.gdshaderinc"
