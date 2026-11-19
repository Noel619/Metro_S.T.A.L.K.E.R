"""Utilidades de las recetas del botín de la superficie (``recipes/botin_*.py``).

Lo que se encuentra arriba lleva dos años de abandono en invierno, así que nada
nace limpio ni nuevo (README, «Nada está intacto»): etiquetas desvaídas y
rasgadas, óxido en la hojalata, desconchones en el esmalte, cartón hinchado por
la humedad, polvo y hollín. No hay letras: una etiqueta es una banda de color con
rayas de tinta, como en una ilustración. Si algo tiene que leerse, lo pone Godot.

Ángulos alrededor de un eje vertical: 0° mira al frente (-Y, hacia la cámara
de los dioramas) y crecen hacia +X.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Iterable

import bpy
from mathutils import Vector

import tumansk_bpy as tb

INK = "#1B1A22"


def grip(root: bpy.types.Object, at: Iterable[float]) -> None:
    """Nodo vacío ``agarre``: por dónde coge la mano lo que se empuña."""
    marker = tb.empty("agarre", root)
    marker.location = Vector(at)


def crumple(obj: bpy.types.Object, amount: float, seed: int) -> None:
    """Arruga una pieza: empuja cada vértice hacia dentro o hacia fuera."""
    rng = random.Random(seed)
    for v in obj.data.vertices:
        v.co += v.normal * rng.uniform(-amount, amount)


def around(radius: float, angle: float, z: float, center: Iterable[float] = (0.0, 0.0, 0.0)) -> Vector:
    """Punto a ``radius`` del eje vertical que pasa por ``center``, a ``angle`` grados del frente."""
    a = math.radians(angle)
    c = Vector(center)
    return Vector((c.x + radius * math.sin(a), c.y - radius * math.cos(a), c.z + z))


def band(
    mb: tb.MeshBuilder,
    radius: float,
    z0: float,
    z1: float,
    color: str,
    *,
    center: Iterable[float] = (0.0, 0.0, 0.0),
    start: float = 0.0,
    end: float = 360.0,
    segments: int = 24,
    rows: int = 1,
    torn: float = 0.0,
    seed: int = 0,
) -> list:
    """Banda de papel pegada alrededor de un eje vertical: la etiqueta de una lata.

    Va de ``start`` a ``end`` grados. Con ``torn`` (en grados), los dos extremos
    quedan rasgados: el papel se ha despegado a jirones y asoma lo de debajo.
    ``rows`` parte la altura para que el borde rasgado y las manchas tengan dónde
    pintarse.
    """
    rng = random.Random(seed)
    span = end - start
    steps = max(1, round(segments * abs(span) / 360.0))
    closed = abs(span) >= 360.0 - 1e-6 and torn <= 0.0
    grid = []
    for j in range(rows + 1):
        z = z0 + (z1 - z0) * j / rows
        first = start + (rng.uniform(0.0, torn) if torn > 0.0 else 0.0)
        last = end - (rng.uniform(0.0, torn) if torn > 0.0 else 0.0)
        row = []
        for i in range(steps + 1):
            if closed and i == steps:
                angle = start
            else:
                angle = first + (last - first) * i / steps
            row.append(around(radius, angle, z, center))
        grid.append(row)
    return mb.sheet(grid, color)


def ink_lines(
    mb: tb.MeshBuilder,
    radius: float,
    heights: Iterable[float],
    *,
    center: Iterable[float] = (0.0, 0.0, 0.0),
    start: float = -30.0,
    end: float = 30.0,
    thickness: float = 0.0016,
    color: str = INK,
    segments: int = 24,
) -> None:
    """Rayas de imprenta sobre una etiqueta redonda: el texto, sin letras."""
    for z in heights:
        band(mb, radius, z, z + thickness, color, center=center, start=start, end=end, segments=segments)


def strap(
    mb: tb.MeshBuilder,
    points: Iterable[Iterable[float]],
    width: float,
    thickness: float,
    color: str,
    *,
    center: Iterable[float],
) -> list:
    """Cinta plana que sigue una línea (fajas, correas, asas de chapa), con la cara
    ancha hacia fuera de ``center``.

    Es ``MeshBuilder.ribbon`` con las caras del derecho: la de ``ribbon`` queda del
    revés (la cara de fuera mira hacia dentro), y con sombras su propia cara de
    fuera la deja a oscuras.
    """
    faces = mb.ribbon(points, width, thickness, color, center=center)
    mb.flip(faces)
    return faces


def rounded_rect(width: float, depth: float, radius: float, steps: int = 3) -> list[tuple[float, float]]:
    """Contorno de un rectángulo de esquinas redondeadas, centrado y en sentido antihorario."""
    radius = min(radius, width / 2.0 - 1e-4, depth / 2.0 - 1e-4)
    hx, hy = width / 2.0 - radius, depth / 2.0 - radius
    points = []
    for cx, cy, a0 in ((hx, -hy, -90.0), (hx, hy, 0.0), (-hx, hy, 90.0), (-hx, -hy, 180.0)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90.0 * k / steps)
            points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return points


def ellipse(width: float, depth: float, steps: int = 16) -> list[tuple[float, float]]:
    """Contorno de una elipse, en sentido antihorario."""
    return [
        (width / 2.0 * math.cos(2.0 * math.pi * k / steps), depth / 2.0 * math.sin(2.0 * math.pi * k / steps))
        for k in range(steps)
    ]


def star(points: int, outer: float, inner: float) -> list[tuple[float, float]]:
    """Contorno de una estrella con una punta hacia +Y, en sentido antihorario."""
    outline = []
    for k in range(points * 2):
        radius = outer if k % 2 == 0 else inner
        a = math.radians(90.0 + 180.0 * k / points)
        outline.append((radius * math.cos(a), radius * math.sin(a)))
    return outline


def sector(inner: float, outer: float, a0: float, a1: float, steps: int = 6) -> list[tuple[float, float]]:
    """Contorno de un trozo de corona circular entre ``a0`` y ``a1`` grados (antihorario)."""
    outline = []
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        outline.append((outer * math.cos(a), outer * math.sin(a)))
    for k in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        outline.append((inner * math.cos(a), inner * math.sin(a)))
    return outline


def disc(
    mb: tb.MeshBuilder,
    center: Iterable[float],
    normal: Iterable[float],
    radius: float,
    color: str,
    *,
    thickness: float = 0.0006,
    segments: int = 8,
    squash: float = 1.0,
) -> list:
    """Disco fino pegado a una superficie (mira hacia ``normal``): desconchones, sellos, manchas."""
    n = Vector(normal).normalized()
    rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(n).to_euler()
    faces = mb.cylinder(
        radius, thickness, Vector(center) + n * (thickness / 2.0), color,
        rotation=[math.degrees(r) for r in rotation], segments=segments,
    )
    if squash != 1.0:
        middle = Vector(center)
        side = n.orthogonal().normalized()
        for vert in dict.fromkeys(v for f in faces for v in f.verts):
            offset = vert.co - middle
            along = offset.dot(side)
            vert.co -= side * along * (1.0 - squash)
    return faces


def recolor(obj: bpy.types.Object, function: Callable[[Vector], str | None]) -> None:
    """Cambia el color base de cada esquina según su posición: ``function(posición)``
    devuelve un color en hexadecimal o ``None`` para dejarlo como estaba.

    Sirve para lo que se pinta encima de una pieza (las rayas del punto de unas
    manoplas, el líquido dentro de un frasco). Hay que llamarla antes de ``paint``.
    """
    mesh = obj.data
    layer = mesh.color_attributes.get("Base")
    if layer is None:
        raise ValueError(f"{obj.name} no tiene colores base: créalo con MeshBuilder")
    cache: dict[str, tuple[float, float, float]] = {}
    for loop in mesh.loops:
        hex_color = function(mesh.vertices[loop.vertex_index].co)
        if hex_color is None:
            continue
        if hex_color not in cache:
            cache[hex_color] = tb.hex_to_linear(hex_color)
        layer.data[loop.index].color = (*cache[hex_color], 1.0)


def scatter(rng: random.Random, count: int, x_range: tuple[float, float], y_range: tuple[float, float]) -> list[tuple[float, float]]:
    """Puntos al azar (con semilla) dentro de un rectángulo."""
    return [(rng.uniform(*x_range), rng.uniform(*y_range)) for _ in range(count)]
