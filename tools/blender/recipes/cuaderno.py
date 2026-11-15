"""El cuaderno del stalker: el único mapa que existe.

Coordenadas de Blender: X a la derecha, Y hacia el fondo, Z hacia arriba. El
cuaderno descansa sobre la mesa con el pie de la página hacia -Y (en Godot,
hacia +Z), como lo lee quien está sentado delante.

Hay dos modelos: ``cuaderno`` (cerrado, con la goma puesta) y
``cuaderno_abierto`` (abierto de par en par). En el abierto, las dos páginas
donde se dibuja son nodos propios con coordenadas de textura de 0 a 1 (el
origen, arriba a la izquierda de cada página), para que el juego les ponga la
textura del mapa.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Vector

import tumansk_bpy as tb

INK = "#1B1A22"
COVER = "#3F5548"
COVER_WORN = "#6F7F6C"
CLOTH = "#2A2725"
PAPER = "#D9CDB0"
PAPER_OLD = "#C7B992"
PAPER_LIGHT = "#E4DBC2"
ENDPAPER = "#B9AE94"
RIBBON = "#C8323C"
PENCIL = "#B3923F"
PENCIL_WOOD = "#D2B48C"
GRAPHITE = "#3A3A3E"
FERRULE = "#8C918D"
ERASER = "#B98A7E"

# Medidas del cuaderno cerrado: ancho, alto y grosores de tapa y de bloque de hojas.
WIDTH, HEIGHT = 0.148, 0.21
COVER_T, BLOCK_T = 0.003, 0.018
PAGE_W, PAGE_H = WIDTH - 0.012, HEIGHT - 0.008


def _segment(mb: tb.MeshBuilder, start: Vector, end: Vector, radius: float, radius_end: float, color: str, segments: int) -> None:
    """Tronco de cono entre dos puntos."""
    direction = end - start
    rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized()).to_euler()
    mb.cylinder(radius, direction.length, (start + end) / 2.0, color, rotation=[math.degrees(a) for a in rotation], radius_top=radius_end, segments=segments)


def _pencil(mb: tb.MeshBuilder, tip: Vector, direction: Vector, length: float = 0.13) -> None:
    """Lápiz de sección hexagonal, con la punta en ``tip`` y el cuerpo hacia ``direction``."""
    d = direction.normalized()
    radius = 0.0036
    _segment(mb, tip, tip + d * 0.005, 0.0003, 0.0012, GRAPHITE, 6)
    _segment(mb, tip + d * 0.005, tip + d * 0.017, 0.0012, radius, PENCIL_WOOD, 6)
    _segment(mb, tip + d * 0.017, tip + d * (length - 0.016), radius, radius, PENCIL, 6)
    _segment(mb, tip + d * (length - 0.016), tip + d * (length - 0.007), radius + 0.0003, radius + 0.0003, FERRULE, 8)
    _segment(mb, tip + d * (length - 0.007), tip + d * length, radius - 0.0002, radius - 0.0004, ERASER, 8)


def _label(mb: tb.MeshBuilder, rng: random.Random, center: Vector) -> None:
    """Etiqueta de papel de la tapa: cerco doble y dos renglones a lápiz."""
    w, h = 0.078, 0.044
    mb.box((w, h, 0.0006), center, PAPER_LIGHT, rotation=(0.0, 0.0, rng.uniform(-1.2, 1.2)), cuts=2)
    z = center.z + 0.0005
    for inset in (0.004, 0.0065):
        for y in (-1.0, 1.0):
            mb.box((w - 2.0 * inset, 0.0006, 0.0004), (center.x, center.y + y * (h / 2.0 - inset), z), INK)
        for x in (-1.0, 1.0):
            mb.box((0.0006, h - 2.0 * inset, 0.0004), (center.x + x * (w / 2.0 - inset), center.y, z), INK)
    for row, y in enumerate((0.005, -0.007)):
        x = center.x - 0.026
        while x < center.x + (0.02 if row == 0 else 0.005):
            stroke = rng.uniform(0.004, 0.011)
            mb.box((stroke, 0.0012, 0.0004), (x + stroke / 2.0, center.y + y + rng.uniform(-0.0008, 0.0008), z), GRAPHITE, rotation=(0.0, 0.0, rng.uniform(-8.0, 8.0)))
            x += stroke + 0.0025


def _corner(mb: tb.MeshBuilder, corner: Vector, sign_x: float, sign_y: float, z: float) -> None:
    """Cantonera de tela en una esquina de la tapa."""
    leg = 0.02
    points = [(0.0, 0.0), (-sign_x * leg, 0.0), (0.0, -sign_y * leg)]
    if sign_x * sign_y < 0.0:
        points.reverse()
    mb.prism(points, 0.0008, (corner.x + sign_x * 0.0006, corner.y + sign_y * 0.0006, z), CLOTH)


def build_notebook() -> bpy.types.Object:
    """Cuaderno cerrado: tapas de hule, lomo de tela, goma, lápiz en su presilla y cinta.

    El lomo queda a la izquierda. Nodos propios: ``tapa`` (se abre girándola
    sobre el lomo: en Godot, ``rotation.z`` de 0 a 180°), ``goma`` (se oculta
    al abrir) y ``lapiz`` (se saca de la presilla).
    """
    rng = random.Random(191)
    root = tb.empty("cuaderno-fisico")
    half_w, half_h = WIDTH / 2.0, HEIGHT / 2.0
    block_z = COVER_T
    top_z = COVER_T + BLOCK_T
    total = top_z + COVER_T

    body = tb.MeshBuilder(seed=191)
    body.box((WIDTH, HEIGHT, COVER_T), (0.0, 0.0, COVER_T / 2.0), COVER, bevel=0.0012, cuts=5, jitter=0.04)
    # Bloque de hojas: capas algo desiguales, para que el canto se lea como papel.
    layers = 9
    block_x = -half_w + 0.004 + PAGE_W / 2.0
    for index in range(layers):
        z = block_z + (index + 0.5) * BLOCK_T / layers
        body.box(
            (PAGE_W + rng.uniform(-0.0012, 0.0006), PAGE_H + rng.uniform(-0.0012, 0.0008), BLOCK_T / layers - 0.0002),
            (block_x + rng.uniform(-0.0005, 0.0005), rng.uniform(-0.0005, 0.0005), z),
            rng.choice((PAPER, PAPER_OLD, PAPER)),
            jitter=0.05,
        )
    # Hojas sueltas metidas entre las páginas: asoman por el canto y por arriba.
    body.box((PAGE_W, PAGE_H, 0.0005), (block_x + 0.004, 0.003, block_z + BLOCK_T * 0.62), PAPER_LIGHT, rotation=(0.0, 0.0, 1.6))
    body.box((PAGE_W - 0.02, PAGE_H - 0.01, 0.0005), (block_x + 0.002, 0.009, block_z + BLOCK_T * 0.31), PAPER_OLD, rotation=(0.0, 0.0, -2.2))
    # Lomo de tela y presilla del lápiz.
    body.box((0.007, HEIGHT + 0.001, total), (-half_w - 0.0012, 0.0, total / 2.0), CLOTH, bevel=0.0028, segments=2, cuts=3)
    body.box((0.024, HEIGHT + 0.0006, 0.0006), (-half_w + 0.011, 0.0, 0.0002), CLOTH)
    loop_x = half_w + 0.0042
    body.lathe(((0.0048, -0.006), (0.0052, -0.004), (0.0052, 0.004), (0.0048, 0.006)), (loop_x, 0.02, total / 2.0), CLOTH, rotation=(-90.0, 0.0, 0.0), segments=10)
    body.box((0.006, 0.012, 0.0012), (half_w - 0.001, 0.02, top_z - 0.0004), CLOTH)
    # Cinta de registro: sale por el pie y cae sobre la mesa.
    body.ribbon(
        tb.smooth_path(((-0.018, -half_h + 0.02, block_z + BLOCK_T * 0.5), (-0.019, -half_h - 0.004, block_z + BLOCK_T * 0.45), (-0.022, -half_h - 0.014, 0.004), (-0.03, -half_h - 0.03, 0.0012), (-0.027, -half_h - 0.044, 0.001)), 4),
        0.006,
        0.0006,
        RIBBON,
        center=(-0.02, -half_h - 0.02, -0.5),
    )
    body_obj = body.finish("cuerpo", tb.material("cuaderno", PAPER), root)
    tb.stain(body_obj, COVER_WORN, amount=0.5, scale=22.0, coverage=0.3, seed=191)

    cover = tb.MeshBuilder(seed=193)
    cover_z = top_z + COVER_T / 2.0
    cover.box((WIDTH, HEIGHT, COVER_T), (0.0, 0.0, cover_z), COVER, bevel=0.0012, cuts=6, jitter=0.04)
    cover.box((0.024, HEIGHT + 0.0006, 0.0006), (-half_w + 0.011, 0.0, total + 0.0001), CLOTH)
    for sign_y in (-1.0, 1.0):
        _corner(cover, Vector((half_w, sign_y * half_h, 0.0)), 1.0, sign_y, total + 0.0003)
    _label(cover, rng, Vector((0.006, 0.042, total + 0.0003)))
    cover_obj = cover.finish("tapa", tb.material("hule", COVER), root)
    tb.stain(cover_obj, COVER_WORN, amount=0.55, scale=20.0, coverage=0.34, seed=193)
    tb.stain(cover_obj, "#2E3D35", amount=0.5, scale=11.0, coverage=0.25, seed=194)
    tb.dent(cover_obj, (half_w - 0.02, -half_h + 0.03, total), radius=0.03, depth=0.0012)
    tb.set_origin(cover_obj, (-half_w + 0.003, 0.0, top_z))

    band = tb.MeshBuilder(seed=197)
    band_x = half_w - 0.022
    band.box((0.007, HEIGHT + 0.003, 0.0011), (band_x, 0.0, total + 0.00075), CLOTH, rotation=(0.0, 0.0, rng.uniform(-0.6, 0.6)))
    for sign_y in (-1.0, 1.0):
        band.box((0.007, 0.0011, total + 0.001), (band_x, sign_y * (half_h + 0.001), total / 2.0 + 0.0005), CLOTH)
    band_obj = band.finish("goma", tb.material("goma", CLOTH), root)
    tb.set_origin(band_obj, (band_x, 0.0, total))

    pencil = tb.MeshBuilder(seed=199)
    _pencil(pencil, Vector((loop_x, -0.058, total / 2.0)), Vector((0.0, 1.0, 0.0)))
    pencil_obj = pencil.finish("lapiz", tb.material("lapiz", PENCIL), root)
    tb.set_origin(pencil_obj, (loop_x, 0.007, total / 2.0))

    tb.collision_box("cuaderno", (WIDTH + 0.012, HEIGHT, total), (0.003, 0.0, total / 2.0), root)
    tb.paint({body_obj: None, cover_obj: None, band_obj: None, pencil_obj: None}, ao_distance=0.03, ao=0.5, seed=191)
    return root


def _page_height(x: float, thickness: float) -> float:
    """Altura de la hoja de arriba a ``x`` metros del lomo: se hunde en el canal y hace panza al lado."""
    rise = 1.0 - math.exp(-x / 0.011)
    belly = 0.0035 * math.exp(-(((x - 0.026) / 0.02) ** 2))
    return COVER_T + 0.0015 + thickness * rise + belly * rise


def _page_surface(name: str, side: float, thickness: float, parent: bpy.types.Object) -> bpy.types.Object:
    """La cara de una página, con UV de 0 a 1: U de izquierda a derecha y V de arriba abajo."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    columns, rows = 18, 6
    margin = 0.0015
    grid = []
    for i in range(columns + 1):
        distance = margin + (PAGE_W - 2.0 * margin) * i / columns
        column = []
        for j in range(rows + 1):
            y = -PAGE_H / 2.0 + margin + (PAGE_H - 2.0 * margin) * j / rows
            column.append((bm.verts.new((side * distance, y, _page_height(distance, thickness) + 0.0003)), distance, j / rows))
        grid.append(column)
    for i in range(columns):
        for j in range(rows):
            corners = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            if side < 0.0:
                corners.reverse()
            face = bm.faces.new([corner[0] for corner in corners])
            for loop, (_, distance, v) in zip(face.loops, corners):
                across = (distance - margin) / (PAGE_W - 2.0 * margin)
                loop[uv_layer].uv = (across if side > 0.0 else 1.0 - across, v)
    return tb.mesh_object(name, bm, tb.material("papel", PAPER_LIGHT), parent)


def build_open_notebook() -> bpy.types.Object:
    """Cuaderno abierto de par en par sobre la mesa, con el lápiz sobre la página.

    La tapa queda a la izquierda. Nodos propios: ``pagina_izquierda`` y
    ``pagina_derecha`` (las caras donde se dibuja, con el material ``papel.tres``
    y su cuadrícula), ``lapiz`` y ``cinta`` (el registro, para ocultarlos o moverlos).
    """
    rng = random.Random(211)
    root = tb.empty("cuaderno_abierto-fisico")
    half_h = HEIGHT / 2.0
    spine_w = 0.016
    left_t, right_t = 0.007, 0.011

    body = tb.MeshBuilder(seed=211)
    for side in (-1.0, 1.0):
        x = side * (spine_w / 2.0 + WIDTH / 2.0)
        body.box((WIDTH, HEIGHT, COVER_T), (x, 0.0, COVER_T / 2.0), COVER, bevel=0.0012, cuts=5, jitter=0.04)
        body.box((WIDTH - 0.01, HEIGHT - 0.01, 0.0005), (x - side * 0.003, 0.0, COVER_T + 0.0001), ENDPAPER, cuts=3)
        for sign_y in (-1.0, 1.0):
            # Las cantoneras dan la vuelta al canto: asoman un triángulo por dentro.
            _corner(body, Vector((side * (spine_w / 2.0 + WIDTH), sign_y * half_h, 0.0)), side, sign_y, COVER_T + 0.0005)
    body.box((spine_w + 0.006, HEIGHT + 0.001, COVER_T - 0.0006), (0.0, 0.0, (COVER_T - 0.0006) / 2.0), CLOTH, bevel=0.001, cuts=2)
    # Bloques de hojas: el contorno es el corte del bloque visto desde el pie.
    steps = 16
    for side, thickness in ((-1.0, left_t), (1.0, right_t)):
        outline = [(0.0008, COVER_T + 0.0003), (PAGE_W, COVER_T + 0.0003)]
        outline += [(PAGE_W - (PAGE_W - 0.0008) * i / steps, _page_height(PAGE_W - (PAGE_W - 0.0008) * i / steps, thickness)) for i in range(steps + 1)]
        if side < 0.0:
            outline = [(-x, z) for x, z in reversed(outline)]
        faces = body.prism(outline, PAGE_H, (0.0, 0.0, 0.0), rng.choice((PAPER, PAPER_OLD)), rotation=(90.0, 0.0, 0.0), jitter=0.03)
        for face in faces:
            # La cara de arriba, curva, se sombrea suave; los cantos, planos.
            face.normal_update()
            face.smooth = face.normal.z > 0.3 and abs(face.normal.y) < 0.5
        # Cantos: unas hojas asoman más que otras.
        for index in range(4):
            z = COVER_T + 0.001 + (index + 0.5) * (thickness - 0.001) / 4.0
            body.box((0.0012, PAGE_H + rng.uniform(-0.002, 0.001), (thickness - 0.001) / 4.0 - 0.0004), (side * (PAGE_W + rng.uniform(-0.0002, 0.0005)), rng.uniform(-0.0006, 0.0006), z), rng.choice((PAPER, PAPER_OLD, PAPER_LIGHT)), jitter=0.05)
    # Un plano doblado, guardado bajo las hojas de la izquierda.
    body.box((0.11, 0.15, 0.0009), (-spine_w / 2.0 - 0.085, 0.036, COVER_T + 0.0012), PAPER_LIGHT, rotation=(0.0, 0.0, 6.0), cuts=2)
    # La goma, suelta, cuelga del canto de la contratapa.
    edge_x = spine_w / 2.0 + WIDTH - 0.022
    body.ribbon(
        tb.smooth_path(((edge_x, half_h - 0.002, COVER_T + 0.0006), (edge_x + 0.012, half_h + 0.006, 0.0012), (edge_x + 0.03, half_h * 0.5, 0.0008), (edge_x + 0.036, 0.0, 0.0008), (edge_x + 0.028, -half_h * 0.55, 0.0008), (edge_x + 0.011, -half_h - 0.006, 0.0012), (edge_x, -half_h + 0.002, COVER_T + 0.0006)), 4),
        0.007,
        0.0011,
        CLOTH,
        center=(edge_x - 0.2, 0.0, -1.0),
    )
    body_obj = body.finish("cuerpo", tb.material("cuaderno", PAPER), root)
    tb.stain(body_obj, COVER_WORN, amount=0.45, scale=22.0, coverage=0.28, seed=211)

    left = _page_surface("pagina_izquierda", -1.0, left_t, root)
    right = _page_surface("pagina_derecha", 1.0, right_t, root)

    ribbon = tb.MeshBuilder(seed=223)
    ribbon.ribbon(
        # Va por el canal, por encima de las hojas, y cae por el pie una vez pasado el bloque.
        tb.smooth_path(((0.0003, half_h - 0.012, COVER_T + 0.0046), (0.0005, 0.03, COVER_T + 0.0048), (0.0, -PAGE_H / 2.0 + 0.01, COVER_T + 0.0048), (-0.0005, -PAGE_H / 2.0 - 0.002, COVER_T + 0.0046), (-0.002, -half_h - 0.004, COVER_T + 0.0012), (-0.008, -half_h - 0.02, 0.0012), (-0.004, -half_h - 0.036, 0.001)), 4),
        0.0045,
        0.0006,
        RIBBON,
        center=(0.0, 0.0, -1.0),
    )
    ribbon_obj = ribbon.finish("cinta", tb.material("cinta", RIBBON), root)

    pencil = tb.MeshBuilder(seed=227)
    # Tumbado sobre la página derecha, paralelo al lomo: ahí la hoja tiene la misma altura a todo lo largo.
    lie = Vector((0.0, 1.0, 0.0))
    pencil_x = 0.021
    pencil_at = Vector((pencil_x, -0.05, _page_height(pencil_x, right_t) + 0.0003 + 0.0033))
    _pencil(pencil, pencil_at, lie)
    pencil_obj = pencil.finish("lapiz", tb.material("lapiz", PENCIL), root)
    tb.set_origin(pencil_obj, pencil_at + lie * 0.065)

    tb.collision_box("cuaderno_abierto", (2.0 * WIDTH + spine_w, HEIGHT, COVER_T + right_t), (0.0, 0.0, (COVER_T + right_t) / 2.0), root)
    tb.paint({body_obj: None, left: PAPER_LIGHT, right: PAPER_LIGHT, ribbon_obj: None, pencil_obj: None}, ao_distance=0.03, ao=0.45, seed=211)
    return root


def build_pencil() -> bpy.types.Object:
    """Lápiz suelto, tumbado sobre la mesa con la punta hacia -X."""
    root = tb.empty("lapiz-fisico")
    mb = tb.MeshBuilder(seed=229)
    _pencil(mb, Vector((-0.065, 0.0, 0.0034)), Vector((1.0, 0.0, 0.0)))
    pencil = mb.finish("lapiz", tb.material("lapiz", PENCIL), root)
    tb.stain(pencil, "#8F7430", amount=0.5, scale=40.0, coverage=0.3, seed=229)
    tb.collision_box("lapiz", (0.13, 0.008, 0.007), (0.0, 0.0, 0.0035), root)
    tb.paint({pencil: None}, ao_distance=0.01, ao=0.3, seed=229)
    return root


def models() -> dict:
    return {
        "cuaderno": build_notebook,
        "cuaderno_abierto": build_open_notebook,
        "lapiz": build_pencil,
    }
