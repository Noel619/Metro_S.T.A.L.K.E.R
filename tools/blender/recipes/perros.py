"""La Jauría (F3-10, README 7.1): perros asilvestrados que la radiación ha deformado.

Más grandes de lo que deberían (80 cm a la cruz), flacos, con el pelo apelmazado de nieve,
calvas de piel gris rosada y bultos. Tres pelajes, que el juego reparte entre los seis de la
manada (y escala un poco a cada uno):

- **la Vieja** (``perro_vieja``): la hembra que guía la manada. Gris, con la oreja izquierda
  partida y una cicatriz en el hocico; la más grande.
- **el pardo** (``perro_pardo``): marrón sucio, con bultos en el lomo y en el costado.
- **el negro** (``perro_negro``): negro tiznado, con calvas en el costado y en la cadera.

Cada modelo lleva su esqueleto de cuadrúpedo y sus animaciones (``perro_anim.py``), las
mismas para los tres. Coordenadas: el perro mira a -Y; su izquierda es +X; z arriba, con el
suelo en z = 0.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import bpy
from mathutils import Vector

import perro_anim as anim
import personaje_bpy as pb
import tumansk_bpy as tb
from personaje_bpy import FRONT, LEFT, UP, Ring, lerp

SKIN_BALD = "#8C7670"
NOSE = "#161414"
EYE = "#1E1A15"
TOOTH = "#C9BFA3"
GUM = "#5A2E2C"


@dataclass
class Coat:
    name: str
    back: str  # el lomo, más oscuro
    side: str  # los costados
    belly: str  # la tripa y las patas por dentro
    scale: float
    seed: int
    torn_ear: bool = False
    lumps: int = 0
    bald: int = 0


VIEJA = Coat("vieja", "#4A4743", "#6B6862", "#8A867D", 1.06, 801, torn_ear=True, lumps=1, bald=1)
PARDO = Coat("pardo", "#3E3226", "#5C4A39", "#7A6650", 1.0, 811, lumps=4, bald=1)
NEGRO = Coat("negro", "#2A2826", "#3B3835", "#57524B", 0.97, 821, lumps=1, bald=3)


@dataclass
class DogJoints:
    hips: Vector
    spine: Vector
    chest: Vector
    neck: Vector
    head: Vector
    snout: Vector
    jaw: Vector
    jaw_tip: Vector
    ear: Vector
    ear_tip: Vector
    tail: list[Vector]
    shoulder: Vector
    elbow: Vector
    wrist: Vector
    front_paw: Vector
    hip: Vector
    stifle: Vector
    hock: Vector
    hind_paw: Vector


def dog_joints() -> DogJoints:
    """Las articulaciones del lado izquierdo (+X), de pie."""
    return DogJoints(
        hips=Vector((0.0, 0.40, 0.74)),
        spine=Vector((0.0, 0.16, 0.77)),
        chest=Vector((0.0, -0.10, 0.79)),
        neck=Vector((0.0, -0.36, 0.81)),
        head=Vector((0.0, -0.53, 0.99)),
        snout=Vector((0.0, -0.82, 0.93)),
        jaw=Vector((0.0, -0.59, 0.925)),
        jaw_tip=Vector((0.0, -0.80, 0.885)),
        ear=Vector((0.07, -0.55, 1.055)),
        ear_tip=Vector((0.105, -0.535, 1.17)),
        tail=[Vector((0.0, 0.50, 0.76)), Vector((0.0, 0.63, 0.70)), Vector((0.0, 0.74, 0.58)), Vector((0.0, 0.80, 0.44))],
        shoulder=Vector((0.115, -0.31, 0.67)),
        elbow=Vector((0.12, -0.26, 0.42)),
        wrist=Vector((0.12, -0.285, 0.13)),
        front_paw=Vector((0.12, -0.33, 0.03)),
        hip=Vector((0.125, 0.38, 0.69)),
        stifle=Vector((0.13, 0.27, 0.43)),
        hock=Vector((0.13, 0.45, 0.17)),
        hind_paw=Vector((0.13, 0.42, 0.03)),
    )


def mx(v: Vector, sign: float) -> Vector:
    return Vector((v.x * sign, v.y, v.z))


SIDES = ((1.0, "Left"), (-1.0, "Right"))


def dog_bones(j: DogJoints) -> list[pb.BoneSpec]:
    bones = [
        pb.BoneSpec("Hips", None, j.hips, j.spine),
        pb.BoneSpec("Spine", "Hips", j.spine, j.chest),
        pb.BoneSpec("Chest", "Spine", j.chest, j.neck),
        pb.BoneSpec("Neck", "Chest", j.neck, j.head),
        pb.BoneSpec("Head", "Neck", j.head, j.snout),
        pb.BoneSpec("Jaw", "Head", j.jaw, j.jaw_tip),
        pb.BoneSpec("Tail1", "Hips", j.tail[0], j.tail[1]),
        pb.BoneSpec("Tail2", "Tail1", j.tail[1], j.tail[2]),
        pb.BoneSpec("Tail3", "Tail2", j.tail[2], j.tail[3]),
    ]
    for sign, side in SIDES:
        bones += [
            pb.BoneSpec(f"{side}Ear", "Head", mx(j.ear, sign), mx(j.ear_tip, sign)),
            pb.BoneSpec(f"{side}UpperArm", "Chest", mx(j.shoulder, sign), mx(j.elbow, sign)),
            pb.BoneSpec(f"{side}ForeArm", f"{side}UpperArm", mx(j.elbow, sign), mx(j.wrist, sign)),
            pb.BoneSpec(f"{side}Hand", f"{side}ForeArm", mx(j.wrist, sign), mx(j.front_paw, sign)),
            pb.BoneSpec(f"{side}UpperLeg", "Hips", mx(j.hip, sign), mx(j.stifle, sign)),
            pb.BoneSpec(f"{side}LowerLeg", f"{side}UpperLeg", mx(j.stifle, sign), mx(j.hock, sign)),
            pb.BoneSpec(f"{side}Foot", f"{side}LowerLeg", mx(j.hock, sign), mx(j.hind_paw, sign)),
        ]
    return bones


def _srgb(hex_color: str) -> Vector:
    """Un color en sRGB (lo que guardan los colores base de las piezas)."""
    value = hex_color.lstrip("#")
    return Vector(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _shaggy(seed: int, amount: float = 0.07):
    """Pelo apelmazado: el radio de cada vértice del anillo varía un poco, siempre igual."""
    rng = random.Random(seed)
    values = [1.0 + rng.uniform(-amount, amount) for _ in range(64)]
    return lambda index: values[index % len(values)]


def _spine_weights(y: float) -> dict[str, float]:
    """Pesos del cuerpo a lo largo del lomo: la cadera atrás, el pecho delante."""
    hips = pb.ramp(y, 0.12, 0.36)
    chest = pb.ramp(-y, 0.0, 0.24)
    spine = max(0.0, 1.0 - hips - chest)
    return {"Hips": hips + 1e-3, "Spine": spine, "Chest": chest}


class Dog:
    def __init__(self, coat: Coat) -> None:
        self.coat = coat
        self.j = dog_joints()
        self.root = tb.empty(f"perro_{coat.name}")
        self.specs = dog_bones(self.j)
        self.names = [spec.name for spec in self.specs]
        self.fur = pb.Sculpt(self.names, coat.seed)
        self.skin = pb.Sculpt(self.names, coat.seed + 1)
        self.rng = random.Random(coat.seed)

    # -- piezas ----------------------------------------------------------------

    def body(self) -> None:
        c = self.coat
        # (y, z del centro, medio ancho, lomo, tripa): de la grupa al pecho.
        rows = [
            (0.58, 0.70, 0.05, 0.045, 0.05),
            (0.52, 0.71, 0.115, 0.09, 0.12),
            (0.42, 0.72, 0.14, 0.10, 0.15),
            (0.28, 0.73, 0.13, 0.09, 0.13),
            (0.14, 0.745, 0.12, 0.08, 0.11),
            (-0.02, 0.745, 0.145, 0.085, 0.22),
            (-0.18, 0.74, 0.16, 0.095, 0.30),
            (-0.32, 0.745, 0.15, 0.105, 0.28),
            (-0.42, 0.77, 0.12, 0.10, 0.21),
            (-0.48, 0.79, 0.065, 0.065, 0.10),
        ]
        rings = []
        for index, (y, z, rx, top, bottom) in enumerate(rows):
            rings.append(
                Ring(
                    Vector((0.0, y, z)), rx, top, bottom, LEFT.copy(), UP.copy(), 2.0,
                    _spine_weights(y), ripple=_shaggy(c.seed + index, 0.05),
                )
            )
        faces = self.fur.tube(rings, c.side, segments=16, cap_start=0.03, cap_end=0.03)
        self._shade_body(faces)

    def _shade_body(self, faces) -> None:
        """El lomo más oscuro y la tripa más clara, por la altura de cada vértice."""
        c = self.coat
        dark, light, mid = _srgb(c.back), _srgb(c.belly), _srgb(c.side)
        for face in faces:
            for loop in face.loops:
                co = loop.vert.co
                local = co.z - 0.74
                if local > 0.0:
                    color = mid.lerp(dark, min(1.0, local / 0.07))
                else:
                    color = mid.lerp(light, min(1.0, -local / 0.16))
                loop[self.fur.base] = (*color, 1.0)

    def neck_and_head(self) -> None:
        c, j = self.coat, self.j
        neck_rings = pb.path_rings(
            [Vector((0.0, -0.34, 0.80)), Vector((0.0, -0.44, 0.88)), Vector((0.0, -0.53, 0.97))],
            [(0.105, 0.10, 0.12), (0.09, 0.085, 0.10), (0.075, 0.075, 0.08)],
            forward=UP,
            weights=[{"Chest": 0.6, "Neck": 0.4}, {"Neck": 1.0}, {"Neck": 0.5, "Head": 0.5}],
        )
        for ring in neck_rings:
            ring.ripple = _shaggy(c.seed + 31, 0.08)
        self.fur.tube(neck_rings, c.side, segments=14, cap_start=None, cap_end=None)
        # El cráneo y el hocico: un tubo que se estrecha hacia la nariz.
        skull = [
            Ring(Vector((0.0, -0.49, 1.0)), 0.08, 0.075, 0.07, LEFT.copy(), UP.copy(), 2.0, {"Head": 1.0}),
            Ring(Vector((0.0, -0.57, 1.005)), 0.092, 0.08, 0.075, LEFT.copy(), UP.copy(), 2.0, {"Head": 1.0}),
            Ring(Vector((0.0, -0.65, 0.98)), 0.07, 0.058, 0.058, LEFT.copy(), UP.copy(), 2.0, {"Head": 1.0}),
            Ring(Vector((0.0, -0.73, 0.957)), 0.047, 0.04, 0.034, LEFT.copy(), UP.copy(), 2.0, {"Head": 1.0}),
            Ring(Vector((0.0, -0.80, 0.942)), 0.032, 0.03, 0.022, LEFT.copy(), UP.copy(), 2.0, {"Head": 1.0}),
        ]
        self.fur.tube(skull, c.side, segments=14, cap_start=0.04, cap_end=0.015)
        jaw = [
            Ring(Vector((0.0, -0.60, 0.935)), 0.05, 0.025, 0.03, LEFT.copy(), UP.copy(), 2.0, {"Jaw": 1.0}),
            Ring(Vector((0.0, -0.70, 0.912)), 0.035, 0.018, 0.022, LEFT.copy(), UP.copy(), 2.0, {"Jaw": 1.0}),
            Ring(Vector((0.0, -0.785, 0.898)), 0.022, 0.012, 0.015, LEFT.copy(), UP.copy(), 2.0, {"Jaw": 1.0}),
        ]
        self.fur.tube(jaw, c.belly, segments=12, cap_start=0.01, cap_end=0.01)
        # Los dientes: se ven cuando gruñe o muerde.
        for sign in (1.0, -1.0):
            for k in range(3):
                y = -0.70 - k * 0.035
                self.skin.blob((sign * (0.024 - k * 0.004), y, 0.932), (0.005, 0.005, 0.011), TOOTH, {"Head": 1.0}, segments=6, rings=3)
                self.skin.blob((sign * (0.02 - k * 0.004), y + 0.012, 0.912), (0.004, 0.004, 0.009), TOOTH, {"Jaw": 1.0}, segments=6, rings=3)
        self.skin.blob((0.0, -0.815, 0.95), (0.024, 0.02, 0.018), NOSE, {"Head": 1.0}, segments=8, rings=4)
        for sign in (1.0, -1.0):
            self.skin.blob((sign * 0.042, -0.645, 1.005), (0.012, 0.01, 0.009), EYE, {"Head": 1.0}, segments=8, rings=4)
            # La encía, en la comisura.
            self.skin.blob((sign * 0.03, -0.66, 0.925), (0.008, 0.02, 0.006), GUM, {"Head": 1.0}, segments=6, rings=3)
        self._ears()

    def _ears(self) -> None:
        c, j = self.coat, self.j
        for sign, side in SIDES:
            base = mx(j.ear, sign)
            tip = mx(j.ear_tip, sign)
            torn = c.torn_ear and sign > 0.0
            if torn:
                tip = base.lerp(tip, 0.55) + Vector((0.01 * sign, 0.0, 0.0))
            rings = [
                Ring(base, 0.032, 0.02, 0.01, LEFT.copy(), FRONT.copy(), 2.0, {"Head": 0.4, f"{side}Ear": 0.6}),
                Ring(base.lerp(tip, 0.55), 0.022 if not torn else 0.03, 0.012, 0.006, LEFT.copy(), FRONT.copy(), 2.0, {f"{side}Ear": 1.0}),
                Ring(tip, 0.006 if not torn else 0.02, 0.004, 0.003, LEFT.copy(), FRONT.copy(), 2.0, {f"{side}Ear": 1.0}),
            ]
            self.fur.tube(rings, c.back, segments=8, cap_start=None, cap_end=0.004)

    def legs(self) -> None:
        c, j = self.coat, self.j
        for sign, side in SIDES:
            front = [mx(j.shoulder, sign) + Vector((0, 0, 0.05)), mx(j.shoulder, sign), mx(j.elbow, sign), mx(j.wrist, sign), mx(j.front_paw, sign) + Vector((0, 0, 0.01))]
            front_radii = [(0.08, 0.09, 0.08), (0.075, 0.085, 0.072), (0.052, 0.058, 0.05), (0.033, 0.036, 0.032), (0.031, 0.034, 0.03)]
            front_weights = [
                {"Chest": 0.6, f"{side}UpperArm": 0.4},
                {"Chest": 0.2, f"{side}UpperArm": 0.8},
                {f"{side}UpperArm": 0.5, f"{side}ForeArm": 0.5},
                {f"{side}ForeArm": 0.5, f"{side}Hand": 0.5},
                {f"{side}Hand": 1.0},
            ]
            rings = pb.path_rings(front, front_radii, forward=FRONT, weights=front_weights)
            for ring in rings:
                ring.ripple = _shaggy(c.seed + 51, 0.05)
            self.fur.tube(rings, c.side, segments=10, cap_start=None, cap_end=0.01)
            hind = [mx(j.hip, sign) + Vector((0, -0.02, 0.05)), mx(j.hip, sign), mx(j.stifle, sign), mx(j.hock, sign), mx(j.hind_paw, sign) + Vector((0, 0, 0.01))]
            hind_radii = [(0.10, 0.125, 0.11), (0.095, 0.115, 0.10), (0.058, 0.064, 0.056), (0.035, 0.038, 0.034), (0.031, 0.034, 0.03)]
            hind_weights = [
                {"Hips": 0.6, f"{side}UpperLeg": 0.4},
                {"Hips": 0.2, f"{side}UpperLeg": 0.8},
                {f"{side}UpperLeg": 0.5, f"{side}LowerLeg": 0.5},
                {f"{side}LowerLeg": 0.5, f"{side}Foot": 0.5},
                {f"{side}Foot": 1.0},
            ]
            rings = pb.path_rings(hind, hind_radii, forward=FRONT, weights=hind_weights)
            for ring in rings:
                ring.ripple = _shaggy(c.seed + 61, 0.05)
            self.fur.tube(rings, c.side, segments=10, cap_start=None, cap_end=0.01)
            # Las patas: almohadilla y dedos, un poco hacia delante.
            for paw, bone in ((mx(j.front_paw, sign), f"{side}Hand"), (mx(j.hind_paw, sign), f"{side}Foot")):
                self.fur.blob(paw + Vector((0.0, -0.03, -0.005)), (0.034, 0.045, 0.024), c.back, {bone: 1.0}, segments=10, rings=4)

    def tail(self) -> None:
        c, j = self.coat, self.j
        radii = [(0.045, 0.045, 0.045), (0.04, 0.042, 0.04), (0.03, 0.032, 0.03), (0.016, 0.018, 0.016)]
        weights = [{"Hips": 0.5, "Tail1": 0.5}, {"Tail1": 0.5, "Tail2": 0.5}, {"Tail2": 0.5, "Tail3": 0.5}, {"Tail3": 1.0}]
        rings = pb.path_rings(j.tail, radii, forward=UP, weights=weights)
        for ring in rings:
            ring.ripple = _shaggy(c.seed + 71, 0.12)
        self.fur.tube(rings, c.back, segments=10, cap_start=None, cap_end=0.02)

    def lumps(self) -> None:
        """Los bultos de la radiación: en el lomo, el costado o el cuello."""
        spots = [
            (0.07, 0.30, 0.815, 0.032), (-0.13, -0.05, 0.79, 0.026), (0.15, -0.20, 0.69, 0.03),
            (-0.07, 0.42, 0.815, 0.022), (0.05, -0.42, 0.89, 0.02),
        ]
        for x, y, z, r in spots[: self.coat.lumps]:
            weights = _spine_weights(y) if y > -0.38 else {"Neck": 1.0}
            self.skin.blob((x, y, z), (r, r * 1.2, r * 0.55), SKIN_BALD, weights, segments=8, rings=4)

    # -- final -----------------------------------------------------------------

    def finish(self) -> bpy.types.Object:
        c = self.coat
        armature = pb.build_armature("esqueleto", self.specs, self.root)
        fur = self.fur.finish("pelo", tb.material("pelo", c.side), self.root)
        skin = self.skin.finish("piel_perro", tb.material("pelo", SKIN_BALD), self.root, subdivide=0)
        # Las calvas: piel gris rosada en el costado y en la cadera.
        bald = [(0.14, 0.05, 0.70), (-0.13, 0.36, 0.74), (0.12, -0.24, 0.62)]
        for center in bald[: c.bald]:
            pb.tint(fur, center, 0.07, SKIN_BALD, 0.85)
        if c.torn_ear:
            # La cicatriz del hocico.
            pb.tint(fur, (0.03, -0.72, 0.965), 0.02, "#B9A69A", 0.8)
        tb.stain(fur, "#2A2622", amount=0.45, scale=9.0, coverage=0.35, seed=c.seed)
        pb.grime(fur, 0.0, 0.35, "#4A4038", 0.6, seed=c.seed)
        tb.paint({fur: None, skin: None}, samples=12, ao=0.55, ao_distance=0.12, cavity_dark=0.35, edge_light=0.06, mottling=0.07, seed=c.seed)
        pb.bind([fur, skin], armature)
        anim.dog_animations(pb.Rig(armature), self.j)
        self.root.scale = (c.scale, c.scale, c.scale)
        return self.root


def build(coat: Coat) -> bpy.types.Object:
    dog = Dog(coat)
    dog.body()
    dog.neck_and_head()
    dog.legs()
    dog.tail()
    dog.lumps()
    return dog.finish()


def models() -> dict:
    return {
        "perro_vieja": lambda: build(VIEJA),
        "perro_pardo": lambda: build(PARDO),
        "perro_negro": lambda: build(NEGRO),
    }
