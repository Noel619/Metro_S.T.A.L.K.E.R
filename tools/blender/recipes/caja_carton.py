"""Caja de cartón: lo más básico del depósito y del botín.

Tres tamaños. Cada una tiene su propia semilla: las caras se hinchan un poco,
tienen alguna abolladura y la cinta no está pegada del todo recta.
"""

from __future__ import annotations

import random

import bpy
from mathutils import Vector

import tumansk_bpy as tb

CARDBOARD = "#B9773F"
TAPE = "#D8B26A"

VARIANTS = {
    "caja_carton": {"size": (0.55, 0.40, 0.38), "seed": 11},
    "caja_carton_pequena": {"size": (0.34, 0.26, 0.22), "seed": 23},
    "caja_carton_grande": {"size": (0.75, 0.55, 0.50), "seed": 37},
}


def build_box(name: str, size: tuple[float, float, float], seed: int) -> bpy.types.Object:
    rng = random.Random(seed)
    width, depth, height = size
    center = Vector((0.0, 0.0, height / 2.0))
    half = Vector((width / 2.0, depth / 2.0, height / 2.0))
    bulge = 0.022 * max(size)

    root = tb.empty(f"{name}-fisico")
    body = tb.box(
        "caja",
        size,
        center,
        cuts=6,
        bevel=0.012,
        segments=2,
        mat=tb.material("carton", CARDBOARD),
        parent=root,
    )
    tb.apply_bulge(body, center, half, bulge)
    for _ in range(rng.randint(1, 2)):
        corner = Vector(
            (
                rng.choice((-1, 1)) * half.x * 0.85,
                rng.choice((-1, 1)) * half.y * 0.85,
                height * rng.choice((0.12, 0.88)),
            )
        )
        tb.dent(body, corner, radius=0.07, depth=0.008)
    tb.wobble(body, amount=0.003, scale=5.0, seed=seed)

    # Cinta: recorre la tapa a lo largo y baja un poco por los dos lados.
    tape_width = 0.065
    tape_drop = height * 0.32
    thickness = 0.003
    skew = rng.uniform(-0.012, 0.012)
    pieces = [
        ((width + 0.004, tape_width, thickness), (0.0, skew, height + thickness / 2.0)),
        ((thickness, tape_width, tape_drop), (half.x + thickness / 2.0, skew, height - tape_drop / 2.0)),
        ((thickness, tape_width, tape_drop), (-half.x - thickness / 2.0, skew, height - tape_drop / 2.0)),
    ]
    tape_parts = []
    for index, (piece_size, piece_center) in enumerate(pieces):
        tape = tb.box(
            f"cinta_{index}",
            piece_size,
            piece_center,
            cuts=4,
            mat=tb.material("cinta", TAPE),
            parent=root,
        )
        tb.apply_bulge(tape, center, half, bulge)
        tb.wobble(tape, amount=0.0015, scale=6.0, seed=seed + index)
        tape_parts.append(tape)

    tb.collision_box(name, size, center, root)
    tb.paint({body: CARDBOARD, **{tape: TAPE for tape in tape_parts}}, seed=seed)
    return root


def models() -> dict:
    return {
        name: (lambda name=name, spec=spec: build_box(name, spec["size"], spec["seed"]))
        for name, spec in VARIANTS.items()
    }
