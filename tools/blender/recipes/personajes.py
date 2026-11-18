"""Los protagonistas: el chico y la chica.

Son hijos de un stalker y demasiado jóvenes para el oficio. Llevan dos años
bajo tierra: están flacos, ojerosos y sucios, y todo lo que llevan puesto es
heredado, remendado o encontrado.

- **El chico** lleva la chaqueta acolchada de su padre con las mangas vueltas,
  su gorro de orejeras con unas gafas de soldador, rodilleras de neumático y
  un macuto de lona con la lona enrollada, una cuerda y la palanca.
- **La chica** lleva un capote militar que le llega a las rodillas, atado con
  una cuerda, el cuello subido, gorro de punto, trenza, botas de fieltro con
  chanclos y un petate con la tetera colgando.

Los dos llevan al pecho la mascarilla de filtros, el zurrón de la máscara en
bandolera y una bufanda (ella, además, el trapo que ata la trenza) del
material ``prenda_jugador``, que el juego tiñe con el color de cada jugador.

Cada modelo sale con su esqueleto (perfil humanoide de Godot) y sus
animaciones. ``manos_*`` son los antebrazos y las manos que se ven en primera
persona, con los dedos articulados.

Coordenadas: el personaje mira a -Y; su izquierda es +X. Las manos de primera
persona se modelan ya en el espacio de la cámara: miran a +Y y la derecha es +X.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import bpy
from mathutils import Quaternion, Vector

import personaje_anim as anim
import personaje_bpy as pb
import tumansk_bpy as tb
from personaje_bpy import FRONT, LEFT, UP, Ring, blend, bump, lerp, ramp, spread

# --------------------------------------------------------------------------
# Paleta de los personajes (docs/ESTILO.md): apagada, sucia, sin colores limpios
# --------------------------------------------------------------------------

SKIN = "#C9A58B"
SKIN_COLD = "#B5766A"
SKIN_DIRT = "#7C6455"
LINING = "#26231F"
LEATHER = "#3E2C21"
LEATHER_WORN = "#5F4532"
DULL_METAL = "#6F6B5C"
IRON = "#34373A"
RUBBER = "#222224"
GLASS = "#14171B"
KNIT_GLOVE = "#4B4844"
KNIT_GLOVE_CUFF = "#393633"
TAPE = "#1F2733"
HEMP = "#85765A"
THREAD = "#1E1B19"
# La bufanda se modela casi blanca: el color lo pone el material del jugador.
PLAYER_CLOTH = "#E2DDD2"
CANVAS_BAG = "#555D47"
CANVAS_BAG_DARK = "#434A39"
MASK_RUBBER = "#454846"
MASK_FILTER = "#565A42"
GRIME = "#26221E"
DUST = "#8B8576"
MUD = "#4E4233"

SIDES = ((1.0, "Left"), (-1.0, "Right"))


@dataclass
class Look:
    """Lo que distingue a un protagonista de otro."""

    name: str
    scale: float
    shoulder: float
    coat: str
    coat_dark: str
    cuff: str
    trousers: str
    hair: str
    boot: str
    boot_cuff: str
    seed: int


CHICO = Look(
    name="chico", scale=1.0, shoulder=0.16,
    coat="#676650", coat_dark="#525240", cuff="#7E775F",
    trousers="#48463F", hair="#221C19",
    boot="#302D2A", boot_cuff="#3D3935", seed=100,
)
CHICA = Look(
    name="chica", scale=0.965, shoulder=0.148,
    coat="#5B5A54", coat_dark="#494842", cuff="#6E6A5F",
    trousers="#40392F", hair="#5E4630",
    boot="#6A655D", boot_cuff="#57534C", seed=200,
)


def mx(vector: Vector, sign: float) -> Vector:
    """El mismo punto en el otro lado del cuerpo."""
    return Vector((vector.x * sign, vector.y, vector.z))


def band(
    sculpt: pb.Sculpt, center: Vector, axis: Vector, radius: float, height: float,
    color: str, weights: pb.WeightSpec, *, thick: float = 0.005, segments: int = 12,
) -> None:
    """Cinta, correa o vuelta de cuerda alrededor de algo redondo."""
    axis = Vector(axis).normalized()
    side = axis.orthogonal().normalized()
    forward = axis.cross(side)
    rings = [
        Ring(Vector(center) + axis * offset, r, r, None, side, forward)
        for offset, r in (
            (-height / 2.0, radius - thick), (-height / 2.0, radius + thick),
            (height / 2.0, radius + thick), (height / 2.0, radius - thick),
        )
    ]
    sculpt.tube(rings, color, segments=segments, weights=weights, closed=True)


# --------------------------------------------------------------------------
# Anatomía: dónde está cada articulación
# --------------------------------------------------------------------------


@dataclass
class Joints:
    hips: Vector
    spine: Vector
    chest: Vector
    neck: Vector
    head: Vector
    head_top: Vector
    shoulder: Vector
    arm: Vector
    elbow: Vector
    wrist: Vector
    hand_end: Vector
    thigh: Vector
    knee: Vector
    ankle: Vector
    toe: Vector
    chin: float
    head_height: float


def joints(look: Look) -> Joints:
    """Articulaciones del lado izquierdo (+X) en reposo, con los brazos en A.

    Proporciones de adolescente: unas siete cabezas de alto, piernas largas.
    """
    k = look.scale
    arm = Vector((look.shoulder, 0.014, 1.36 * k))
    upper = Vector((0.574, 0.0, -0.819))
    lower = Vector((0.55, -0.14, -0.82)).normalized()
    elbow = arm + upper * 0.265 * k
    wrist = elbow + lower * 0.24 * k
    head_height = 0.232
    chin = 1.452 * k
    return Joints(
        hips=Vector((0.0, 0.0, 0.925 * k)),
        spine=Vector((0.0, 0.0, 1.04 * k)),
        chest=Vector((0.0, 0.008, 1.19 * k)),
        neck=Vector((0.0, 0.012, 1.405 * k)),
        head=Vector((0.0, 0.004, chin + 0.01)),
        head_top=Vector((0.0, 0.0, chin + head_height)),
        shoulder=Vector((0.03, 0.012, 1.36 * k)),
        arm=arm,
        elbow=elbow,
        wrist=wrist,
        hand_end=wrist + lower * 0.08,
        thigh=Vector((0.086, 0.0, 0.885 * k)),
        knee=Vector((0.092, -0.014, 0.485 * k)),
        ankle=Vector((0.095, 0.012, 0.08)),
        toe=Vector((0.095, -0.15, 0.03)),
        chin=chin,
        head_height=head_height,
    )


def body_bones(j: Joints) -> list[pb.BoneSpec]:
    bones = [
        pb.BoneSpec("Hips", None, j.hips, j.spine),
        pb.BoneSpec("Spine", "Hips", j.spine, j.chest),
        pb.BoneSpec("Chest", "Spine", j.chest, j.neck),
        pb.BoneSpec("Neck", "Chest", j.neck, j.head),
        pb.BoneSpec("Head", "Neck", j.head, j.head_top),
    ]
    for sign, side in SIDES:
        bones += [
            pb.BoneSpec(f"{side}Shoulder", "Chest", mx(j.shoulder, sign), mx(j.arm, sign)),
            pb.BoneSpec(f"{side}UpperArm", f"{side}Shoulder", mx(j.arm, sign), mx(j.elbow, sign)),
            pb.BoneSpec(f"{side}LowerArm", f"{side}UpperArm", mx(j.elbow, sign), mx(j.wrist, sign)),
            pb.BoneSpec(f"{side}Hand", f"{side}LowerArm", mx(j.wrist, sign), mx(j.hand_end, sign)),
            pb.BoneSpec(f"{side}UpperLeg", "Hips", mx(j.thigh, sign), mx(j.knee, sign)),
            pb.BoneSpec(f"{side}LowerLeg", f"{side}UpperLeg", mx(j.knee, sign), mx(j.ankle, sign)),
            pb.BoneSpec(f"{side}Foot", f"{side}LowerLeg", mx(j.ankle, sign), mx(j.toe, sign)),
        ]
    return bones


# --------------------------------------------------------------------------
# Manos (las comparten el cuerpo y la vista en primera persona)
# --------------------------------------------------------------------------

# nombre: (x de la base, y de la base, falanges, radio, apertura en grados)
FINGERS = {
    "Index": (0.029, 0.078, (0.036, 0.023, 0.021), 0.0092, 6.0),
    "Middle": (0.010, 0.082, (0.039, 0.026, 0.022), 0.0094, 1.0),
    "Ring": (-0.009, 0.079, (0.036, 0.024, 0.021), 0.0089, -5.0),
    "Little": (-0.027, 0.072, (0.028, 0.019, 0.018), 0.0080, -11.0),
}
FINGER_BONES = ("Proximal", "Intermediate", "Distal")
THUMB_BONES = ("Metacarpal", "Proximal", "Distal")


@dataclass
class HandFrame:
    """Ejes de una mano: X hacia el pulgar, Y hacia los dedos, Z hacia el dorso."""

    origin: Vector
    x: Vector
    y: Vector
    z: Vector
    size: float = 1.0

    def at(self, local: Vector) -> Vector:
        return self.origin + (self.x * local.x + self.y * local.y + self.z * local.z) * self.size

    def turn(self, local: Vector) -> Vector:
        return (self.x * local.x + self.y * local.y + self.z * local.z).normalized()


def finger_chain(name: str, curl: tuple[float, float, float]) -> tuple[list[Vector], list[Vector], Vector]:
    """Articulaciones de un dedo en ejes de la mano: puntos, direcciones y eje lateral."""
    if name == "Thumb":
        base = Vector((0.028, 0.012, -0.012))
        lengths = (0.026, 0.030, 0.027)
        yaw = Quaternion(Vector((0, 0, 1)), math.radians(-50.0)) @ Quaternion(Vector((0, 1, 0)), math.radians(-35.0))
        bends = (curl[0] * 0.3, curl[1] * 0.5, curl[2] * 0.7)
    else:
        x, y, lengths, _, splay = FINGERS[name]
        base = Vector((x, y, 0.0))
        yaw = Quaternion(Vector((0, 0, 1)), math.radians(-splay))
        bends = curl
    side = yaw @ Vector((1.0, 0.0, 0.0))
    points, directions = [base], []
    total = 0.0
    for length, bend in zip(lengths, bends):
        total += bend
        direction = yaw @ (Quaternion(Vector((1, 0, 0)), math.radians(-total)) @ Vector((0.0, 1.0, 0.0)))
        directions.append(direction)
        points.append(points[-1] + direction * length)
    return points, directions, side


def hand_bones(side: str, frame: HandFrame, curl: tuple[float, float, float]) -> list[pb.BoneSpec]:
    """Huesos de los dedos (solo en las manos de primera persona)."""
    bones = []
    for finger in ("Thumb", *FINGERS):
        points, _, _ = finger_chain(finger, curl)
        names = THUMB_BONES if finger == "Thumb" else FINGER_BONES
        parent = f"{side}Hand"
        for k, part in enumerate(names):
            name = f"{side}{finger}{part}"
            bones.append(pb.BoneSpec(name, parent, frame.at(points[k]), frame.at(points[k + 1])))
            parent = name
    return bones


def build_hand(
    cloth: pb.Sculpt,
    skin: pb.Sculpt,
    side: str,
    frame: HandFrame,
    curl: tuple[float, float, float],
    *,
    articulated: bool,
    taped: str | None = None,
) -> None:
    """Mano con mitones de punto: la palma y la primera falange van cubiertas.

    ``taped`` es el dedo que lleva un esparadrapo de cinta aislante.
    """
    hand = {f"{side}Hand": 1.0}

    def ring(y: float, rx: float, rz: float, color=None) -> Ring:
        return Ring(
            frame.at(Vector((0.0, y, 0.0))), rx * frame.size, rz * frame.size, None,
            frame.x, frame.z, 2.6, None, color,
        )

    # Palma, con el puño del mitón en la muñeca.
    cloth.tube(
        [
            ring(-0.030, 0.024, 0.020, KNIT_GLOVE_CUFF),
            ring(-0.024, 0.033, 0.028, KNIT_GLOVE_CUFF),
            ring(-0.004, 0.033, 0.027),
            ring(0.004, 0.031, 0.023),
            ring(0.026, 0.039, 0.021),
            ring(0.056, 0.044, 0.019),
            ring(0.080, 0.043, 0.016),
        ],
        KNIT_GLOVE, segments=12, weights=hand, cap_start=0.0, cap_end=0.009 * frame.size,
    )
    for finger in ("Thumb", *FINGERS):
        points, directions, lateral = finger_chain(finger, curl)
        names = THUMB_BONES if finger == "Thumb" else FINGER_BONES
        radius = 0.0112 if finger == "Thumb" else FINGERS[finger][3]
        bones = [f"{side}{finger}{part}" for part in names] if articulated else [f"{side}Hand"] * 3
        side_axis = frame.turn(lateral)

        def section(point: Vector, direction: Vector, r: float, weights, color=None) -> Ring:
            return Ring(
                frame.at(point), r * frame.size, r * frame.size, None,
                side_axis, side_axis.cross(frame.turn(direction)).normalized(), 2.0, weights, color,
            )

        first, second, third = ({bones[0]: 1.0}, {bones[1]: 1.0}, {bones[2]: 1.0})
        if finger == "Thumb":
            # El arranque del pulgar es un bulto de la palma.
            cloth.tube(
                [
                    section(points[0] - directions[0] * 0.012, directions[0], 0.014, hand),
                    section(points[0] + directions[0] * 0.008, directions[0], 0.0155, blend(hand, first, 0.5)),
                    section(points[1], directions[0].lerp(directions[1], 0.5), 0.0142, blend(first, second, 0.5)),
                    section(points[1] + directions[1] * 0.012, directions[1], radius + 0.0026, second),
                    section(points[1] + directions[1] * 0.015, directions[1], radius - 0.001, second),
                ],
                KNIT_GLOVE, segments=8, cap_start=0.004, cap_end=None,
            )
            skin_rings = [
                section(points[1] + directions[1] * 0.004, directions[1], radius, second),
                section(points[2], directions[1].lerp(directions[2], 0.5), radius, blend(second, third, 0.5)),
                section(points[3] - directions[2] * radius * 0.9, directions[2], radius * 0.96, third),
            ]
        else:
            cover = points[0] + directions[0] * (points[1] - points[0]).length * 0.62
            cloth.tube(
                [
                    section(points[0] - directions[0] * 0.010, directions[0], radius + 0.0022, hand),
                    section(points[0] + directions[0] * 0.006, directions[0], radius + 0.0026, blend(hand, first, 0.6)),
                    section(cover, directions[0], radius + 0.0030, first),
                    section(cover + directions[0] * 0.003, directions[0], radius - 0.001, first),
                ],
                KNIT_GLOVE, segments=8, cap_start=0.003, cap_end=None,
            )
            skin_rings = [
                section(cover - directions[0] * 0.008, directions[0], radius, first),
                section(points[1], directions[0].lerp(directions[1], 0.5), radius * 1.04, blend(first, second, 0.5)),
                section(points[1].lerp(points[2], 0.5), directions[1], radius * 0.97, second),
                section(points[2], directions[1].lerp(directions[2], 0.5), radius * 0.99, blend(second, third, 0.5)),
                section(points[3] - directions[2] * radius * 0.9, directions[2], radius * 0.9, third),
            ]
            if finger == taped:
                middle = points[1].lerp(points[2], 0.5)
                cloth.tube(
                    [
                        section(middle - directions[1] * 0.009, directions[1], radius - 0.001, second),
                        section(middle - directions[1] * 0.008, directions[1], radius + 0.0016, second),
                        section(middle + directions[1] * 0.008, directions[1], radius + 0.0016, second),
                        section(middle + directions[1] * 0.009, directions[1], radius - 0.001, second),
                    ],
                    TAPE, segments=8, cap_start=None, cap_end=None,
                )
        skin.tube(skin_rings, SKIN, segments=8, cap_start=0.0, cap_end=radius * 0.75 * frame.size)


# --------------------------------------------------------------------------
# El cuerpo
# --------------------------------------------------------------------------


class Character:
    """Construye un protagonista pieza a pieza."""

    def __init__(self, look: Look, torso: pb.Profile, hem_follow: float, prefix: str = "jugador") -> None:
        self.look = look
        self.j = joints(look)
        self.torso = torso
        self.hem_follow = hem_follow
        self.root = tb.empty(f"{prefix}_{look.name}")
        self.specs = body_bones(self.j)
        names = [spec.name for spec in self.specs]
        self.cloth = pb.Sculpt(names, look.seed)
        self.skin = pb.Sculpt(names, look.seed + 1)
        self.scarf = pb.Sculpt(names, look.seed + 2)
        self.pack = pb.Sculpt(names, look.seed + 3)
        self.bag = pb.Sculpt(names, look.seed + 4)
        self.mask = pb.Sculpt(names, look.seed + 5)
        self.rng = random.Random(look.seed)
        self.head = self._head_profile()
        self.hand_frames: dict[str, HandFrame] = {}

    def add_bones(self, specs: list[pb.BoneSpec]) -> None:
        """Huesos propios de un personaje (el cabo de la bufanda, la trenza)."""
        self.specs += specs
        for sculpt in (self.cloth, self.skin, self.scarf, self.pack, self.bag, self.mask):
            sculpt.bones += [spec.name for spec in specs]
            sculpt.index = {name: i for i, name in enumerate(sculpt.bones)}

    # -- pesos ---------------------------------------------------------------

    def torso_weights(self, co: Vector) -> pb.Weights:
        """Pesos de todo lo que va pegado al tronco, según dónde esté."""
        j = self.j
        weights = blend({"Hips": 1.0}, {"Spine": 1.0}, ramp(co.z, j.spine.z - 0.05, j.spine.z + 0.05))
        weights = blend(weights, {"Chest": 1.0}, ramp(co.z, j.chest.z - 0.06, j.chest.z + 0.06))
        side = "Left" if co.x >= 0.0 else "Right"
        shoulder = 0.6 * ramp(abs(co.x), 0.08, 0.17) * ramp(co.z, j.arm.z - 0.11, j.arm.z - 0.02)
        weights = blend(weights, {f"{side}Shoulder": 1.0}, shoulder)
        # El faldón acompaña un poco al muslo de su lado al andar.
        follow = self.hem_follow * ramp(j.thigh.z - co.z, 0.0, 0.3) * ramp(abs(co.x), 0.015, 0.07)
        return blend(weights, {f"{side}UpperLeg": 1.0}, follow)

    # -- cabeza ----------------------------------------------------------------

    def _head_profile(self) -> pb.Profile:
        j = self.j
        rows = [
            # t, rx, frente, espalda
            (0.02, 0.028, 0.048, 0.018),
            (0.10, 0.050, 0.075, 0.040),
            (0.20, 0.064, 0.087, 0.058),
            (0.32, 0.073, 0.092, 0.078),
            (0.44, 0.079, 0.093, 0.091),
            (0.56, 0.082, 0.092, 0.098),
            (0.68, 0.083, 0.093, 0.101),
            (0.80, 0.078, 0.087, 0.097),
            (0.90, 0.062, 0.069, 0.080),
            (0.97, 0.036, 0.040, 0.046),
        ]
        return pb.Profile(
            [(j.chin + t * j.head_height, rx, front, back, -0.004) for t, rx, front, back in rows], power=2.1
        )

    def head_z(self, t: float) -> float:
        return self.j.chin + t * self.j.head_height

    def _face_relief(self, co: Vector) -> Vector:
        """Relieve de la cara: cejas, cuencas, pómulos y mejillas hundidas.

        Es lo que hace que la luz de arriba deje los ojos en sombra.
        """
        radial = Vector((co.x, co.y + 0.004, 0.0))
        if radial.length < 1e-5:
            return Vector()
        t = (co.z - self.j.chin) / self.j.head_height
        angle = math.degrees(math.atan2(co.x, -(co.y + 0.004)))
        side = abs(angle)
        depth = 0.0
        depth += 0.0065 * bump(angle, 0.0, 50.0) * bump(t, 0.635, 0.04)
        depth -= 0.009 * bump(side, 23.0, 12.0) * bump(t, 0.555, 0.045)
        depth += 0.006 * bump(side, 46.0, 14.0) * bump(t, 0.455, 0.05)
        depth -= 0.0075 * bump(side, 48.0, 17.0) * bump(t, 0.27, 0.075)
        depth += 0.004 * bump(angle, 0.0, 18.0) * bump(t, 0.06, 0.05)
        depth -= 0.004 * bump(side, 82.0, 20.0) * bump(t, 0.6, 0.08)
        return radial.normalized() * depth

    def build_head(self) -> None:
        j = self.j
        head = {"Head": 1.0}
        heights = (0.02, 0.07, 0.13, 0.2, 0.27, 0.34, 0.41, 0.48, 0.55, 0.61, 0.67, 0.74, 0.81, 0.88, 0.94, 0.975)
        rings = [self.head.ring(self.head_z(t)) for t in heights]
        faces = self.skin.tube(rings, SKIN, segments=32, weights=head, cap_start=0.005, cap_end=0.008)
        self.skin.move(faces, self._face_relief)
        # Nariz: una cuña, estrecha arriba y con la punta caída.
        nose = []
        for t, width, depth in ((0.585, 0.0045, 0.002), (0.52, 0.0065, 0.007), (0.45, 0.0085, 0.013), (0.395, 0.0118, 0.0185), (0.37, 0.011, 0.012)):
            center = self.head.surface(90.0, self.head_z(t)) - FRONT * 0.006
            nose.append(Ring(center, width, depth + 0.006, 0.004, LEFT.copy(), FRONT.copy(), 2.0, head))
        self.skin.tube(nose, SKIN, segments=8, cap_start=0.0, cap_end=0.004)
        # Orejas.
        for sign in (1.0, -1.0):
            center = self.head.surface(90.0 - sign * 90.0, self.head_z(0.47), 0.003) + Vector((0.0, 0.014, 0.0))
            self.skin.blob(
                center, (0.0075, 0.016, 0.03), SKIN, head,
                rotation=Quaternion(UP, math.radians(-sign * 16.0)), segments=8, rings=4,
            )
        # Cuello flaco.
        self.skin.tube(
            [
                Ring(Vector((0.0, 0.014, j.neck.z - 0.04)), 0.047, 0.045, weights={"Chest": 1.0}),
                Ring(Vector((0.0, 0.012, j.neck.z + 0.015)), 0.041, 0.042, weights={"Neck": 1.0}),
                Ring(Vector((0.0, 0.008, j.head.z + 0.035)), 0.041, 0.043, weights=head),
            ],
            SKIN, segments=10,
        )

    def face_rays(self) -> list[list[tuple[Vector, Vector]]]:
        """Rayos que pegan la cara dibujada sobre la cabeza (ver ``pb.sticker``)."""
        grid = []
        for z in spread(self.head_z(0.74), self.head_z(0.10), 15):
            row = []
            for degrees in spread(148.0, 32.0, 15):
                theta = math.radians(degrees)
                radial = LEFT * math.cos(theta) + FRONT * math.sin(theta)
                row.append((Vector((0.0, -0.004, z)) + radial * 0.4, -radial))
            grid.append(row)
        return grid

    # -- brazos y manos ----------------------------------------------------------

    def build_sleeves(self, quilted: bool, taped: float = 0.0, elbow_patch: float = 0.0) -> None:
        """Mangas demasiado largas, con el puño vuelto.

        ``taped`` es el lado (1 izquierdo, -1 derecho) que lleva cinta aislante
        en el antebrazo; ``elbow_patch``, el de la codera.
        """
        j, look = self.j, self.look
        upper_len = (j.elbow - j.arm).length
        lower_len = (j.wrist - j.elbow).length
        total = upper_len + lower_len
        for sign, side in SIDES:
            arm, elbow, wrist = mx(j.arm, sign), mx(j.elbow, sign), mx(j.wrist, sign)
            d1, d2 = (elbow - arm).normalized(), (wrist - elbow).normalized()

            def along(s: float) -> Vector:
                return arm + d1 * s if s <= upper_len else elbow + d2 * (s - upper_len)

            end = total - 0.012
            stations = [-0.04, 0.012] + spread(0.05, end - 0.07, 11)
            points, radii, weights, colors = [], [], [], []
            for index, s in enumerate(stations):
                base = lerp(0.067, 0.054, max(0.0, s) / total)
                if s < 0.0:
                    base = 0.052
                elif quilted and index >= 2:
                    base += 0.0035 if index % 2 == 0 else -0.003
                else:
                    # Arrugas de una manga que sobra.
                    base += 0.003 * math.sin(index * 2.4)
                bend = ramp(s, upper_len - 0.07, upper_len + 0.07)
                w = blend({f"{side}UpperArm": 1.0}, {f"{side}LowerArm": 1.0}, bend)
                w = blend({f"{side}Shoulder": 1.0}, w, ramp(s, -0.06, 0.07))
                points.append(along(s))
                radii.append((base, base))
                weights.append(w)
                colors.append(None)
            lower = {f"{side}LowerArm": 1.0}
            for s, r, color in ((end - 0.066, 0.066, look.cuff), (end - 0.004, 0.067, look.cuff), (end + 0.004, 0.046, LINING)):
                points.append(along(s))
                radii.append((r, r))
                weights.append(lower)
                colors.append(color)
            rings = pb.path_rings(points, radii, forward=FRONT, weights=weights, colors=colors)
            self.cloth.tube(rings, look.coat, segments=12, cap_start=0.01, cap_end=0.0)
            if sign == taped:
                for offset in (0.035, 0.062):
                    band(self.cloth, elbow + d2 * (lower_len * 0.42 + offset), d2, 0.058, 0.022, TAPE, lower, thick=0.003)
            if sign == elbow_patch:
                back = (-FRONT - d1 * (-FRONT).dot(d1)).normalized()
                self.cloth.blob(
                    elbow + back * 0.046 - d1 * 0.01, (0.04, 0.016, 0.052), LEATHER_WORN,
                    blend({f"{side}UpperArm": 1.0}, lower, 0.5),
                    rotation=UP.rotation_difference(d1), segments=8, rings=4,
                )

    def build_hands(self, taped: tuple[str, str] | None = None) -> None:
        j = self.j
        for sign, side in SIDES:
            wrist, elbow = mx(j.wrist, sign), mx(j.elbow, sign)
            y = (wrist - elbow).normalized()
            x = (FRONT - y * FRONT.dot(y)).normalized()
            z = x.cross(y) * sign
            frame = HandFrame(wrist + y * 0.012, x, y, z, 1.04)
            self.hand_frames[side] = frame
            finger = taped[1] if taped is not None and taped[0] == side else None
            build_hand(self.cloth, self.skin, side, frame, (32.0, 36.0, 22.0), articulated=False, taped=finger)

    # -- piernas y botas -----------------------------------------------------

    def build_legs(self, kneepads: bool) -> None:
        j, look = self.j, self.look
        self.cloth.blob((0.0, 0.006, j.thigh.z - 0.01), (0.166, 0.118, 0.115), look.trousers, {"Hips": 1.0}, segments=12)
        for sign, side in SIDES:
            thigh, knee, ankle = mx(j.thigh, sign), mx(j.knee, sign), mx(j.ankle, sign)
            upper, lower = {f"{side}UpperLeg": 1.0}, {f"{side}LowerLeg": 1.0}
            d2 = ankle - knee
            points = [
                thigh + Vector((0.0, 0.0, 0.05)),
                thigh.lerp(knee, 0.12),
                thigh.lerp(knee, 0.4),
                thigh.lerp(knee, 0.62),
                thigh.lerp(knee, 0.82),
                knee,
                knee + d2 * 0.14,
                knee + d2 * 0.26,
                knee + d2 * 0.34,
            ]
            # Pantalón acolchado: se arruga y se abomba sobre la bota.
            radii = [
                (0.09, 0.098), (0.098, 0.104), (0.092, 0.097), (0.087, 0.091), (0.082, 0.086),
                (0.081, 0.085), (0.083, 0.086), (0.086, 0.088), (0.058, 0.06),
            ]
            weights = [
                blend({"Hips": 1.0}, upper, 0.5), blend({"Hips": 1.0}, upper, 0.85), upper, upper,
                blend(upper, lower, 0.25), blend(upper, lower, 0.5), blend(upper, lower, 0.85), lower, lower,
            ]
            rings = pb.path_rings(points, radii, forward=FRONT, weights=weights)
            self.cloth.tube(rings, look.trousers, segments=12, cap_start=0.02, cap_end=0.0)
            if kneepads:
                # Rodillera de neumático, sujeta con dos tiras.
                bend = blend(upper, lower, 0.5)
                self.cloth.blob(knee + FRONT * 0.07 + UP * 0.005, (0.056, 0.024, 0.074), RUBBER, bend, segments=10, rings=5)
                band(self.cloth, knee + UP * 0.062, UP, 0.089, 0.02, LEATHER, blend(upper, lower, 0.2), thick=0.004)
                band(self.cloth, knee - UP * 0.052 + FRONT * -0.003, UP, 0.088, 0.02, LEATHER, blend(upper, lower, 0.8), thick=0.004)

    def build_boots(self, felt: bool, taped: float = 0.0) -> None:
        """Botas de caña: de cuero basto, o de fieltro con chanclos de goma."""
        j, look = self.j, self.look
        top = j.knee.z * (0.80 if felt else 0.82)
        for sign, side in SIDES:
            knee, ankle = mx(j.knee, sign), mx(j.ankle, sign)
            lower, foot = {f"{side}LowerLeg": 1.0}, {f"{side}Foot": 1.0}

            def shin(z: float) -> Vector:
                return knee.lerp(ankle, (knee.z - z) / (knee.z - ankle.z))

            thick = 0.008 if felt else 0.0
            stations = [
                (top - 0.01, 0.056, look.boot_cuff), (top + 0.004, 0.074, look.boot_cuff), (top - 0.03, 0.075, None),
                (0.30, 0.072, None), (0.22, 0.067, None), (0.165, 0.071, None), (0.13, 0.064, None), (0.10, 0.068, None), (0.075, 0.062, None),
            ]
            points = [shin(z) for z, _, _ in stations]
            radii = [(r + thick, r + thick * 1.2) for _, r, _ in stations]
            colors = [color for _, _, color in stations]
            weights = [lower] * 6 + [blend(lower, foot, 0.3), blend(lower, foot, 0.6), blend(lower, foot, 0.85)]
            self.cloth.tube(
                pb.path_rings(points, radii, forward=FRONT, weights=weights, colors=colors),
                look.boot, segments=12, cap_start=0.0, cap_end=0.0,
            )
            # El pie: de talón a puntera, con la suela plana.
            length = 0.3 if felt else 0.295
            heel_y = ankle.y + 0.082
            sections = [
                (0.03, 0.04, 0.046, 0.052),
                (0.16, 0.054, 0.058, 0.061),
                (0.34, 0.059, 0.062, 0.064),
                (0.56, 0.061, 0.05, 0.053),
                (0.78, 0.059, 0.042, 0.046),
                (0.93, 0.046, 0.034, 0.039),
            ]
            rings, sole = [], []
            for f, rx, up, zc in sections:
                center = Vector((ankle.x, heel_y - f * length, zc + thick * 0.5))
                rings.append(Ring(center, rx + thick, up + thick * 0.5, zc - 0.006, LEFT.copy(), UP.copy(), 2.7, foot))
                sole.append(Ring(Vector((center.x, center.y, 0.0)), rx + thick + 0.006, 0.0, 0.0, LEFT.copy(), UP.copy(), 3.0, foot))
            self.cloth.tube(rings, look.boot, segments=12, cap_start=0.01, cap_end=0.014)
            if felt:
                # Chanclo de goma: cubre el pie hasta media altura.
                for ring in sole:
                    ring.center.z, ring.front, ring.back = 0.024, 0.026, 0.024
                self.cloth.tube(sole, RUBBER, segments=12, cap_start=0.014, cap_end=0.018)
            else:
                for ring in sole:
                    ring.center.z, ring.front, ring.back = 0.012, 0.011, 0.012
                self.cloth.tube(sole, LINING, segments=12, cap_start=0.012, cap_end=0.014)
                self.cloth.box((0.106, 0.085, 0.032), (ankle.x, heel_y - 0.05, 0.013), LINING, foot, bevel=0.008)
            if sign == taped:
                band(self.cloth, shin(0.2), ankle - knee, 0.071 + thick, 0.026, TAPE, lower, thick=0.003)

    # -- bufanda y mascarilla --------------------------------------------------------

    def scarf_path(self, tail_side: float, tail_length: float) -> list[tuple[Vector, Vector]]:
        """El cabo de la bufanda: baja por el pecho, pegado a la chaqueta."""
        degrees = 90.0 - 24.0 * tail_side
        top = self.j.neck.z + 0.01
        return [
            self.torso.on(degrees - 3.0 * tail_side * f, top - (tail_length + 0.03) * f, 0.014 + 0.004 * f)
            for f in spread(0.0, 1.0, 6)
        ]

    def scarf_bones(self, tail_side: float, tail_length: float) -> list[pb.BoneSpec]:
        path = self.scarf_path(tail_side, tail_length)
        top, middle, end = path[1][0], path[3][0], path[5][0]
        return [pb.BoneSpec("Bufanda1", "Chest", top, middle), pb.BoneSpec("Bufanda2", "Bufanda1", middle, end)]

    def build_scarf(self, tail_side: float, tail_length: float) -> None:
        """Bufanda raída: dos vueltas flojas al cuello y un cabo corto."""
        j = self.j
        chest = {"Chest": 1.0}
        center = Vector((0.0, 0.006, j.neck.z + 0.022))
        count = 16
        for turn, (radius, drop, fat) in enumerate(((0.07, 0.0, 0.03), (0.078, 0.032, 0.026))):
            rings = []
            for i in range(count):
                theta = 2.0 * math.pi * i / count
                radial = LEFT * math.cos(theta) + FRONT * math.sin(theta)
                point = center + LEFT * radius * math.cos(theta) + FRONT * radius * 0.96 * math.sin(theta)
                point.z -= drop + 0.014 * math.sin(theta) + 0.008 * math.cos(2.0 * theta + turn * 1.3)
                size = fat * (1.0 + 0.14 * math.sin(3.0 * theta + 1.0 + turn * 2.0))
                rings.append(Ring(point, size, size * 0.9, None, radial, UP.copy(), 2.3, blend(chest, {"Neck": 1.0}, 0.35 - 0.2 * turn)))
            self.scarf.tube(rings, PLAYER_CLOTH, segments=8, closed=True)
        path = self.scarf_path(tail_side, tail_length)
        rings = []
        for index, (point, normal) in enumerate(path):
            f = index / (len(path) - 1)
            w = blend(chest, {"Bufanda1": 1.0}, ramp(f, 0.1, 0.45))
            w = blend(w, {"Bufanda2": 1.0}, ramp(f, 0.5, 0.9))
            across = UP.cross(normal).normalized()
            width = 0.036 * (1.0 + 0.12 * math.sin(index * 2.1))
            rings.append(Ring(point, width, 0.011, None, across, normal, 3.0, w))
        self.scarf.tube(rings, PLAYER_CLOTH, segments=8, cap_start=0.0, cap_end=0.003)
        # Flecos desiguales: los que quedan.
        end, normal = path[-1]
        across = UP.cross(normal).normalized()
        for k in (-2, -1, 1, 2):
            start = end + across * k * 0.014 - UP * 0.003
            length = self.rng.uniform(0.012, 0.034)
            self.scarf.tube(
                [
                    Ring(start, 0.0055, 0.0055, None, across, normal),
                    Ring(start - UP * length + across * self.rng.uniform(-0.005, 0.005), 0.005, 0.005, None, across, normal),
                ],
                PLAYER_CLOTH, segments=6, weights={"Bufanda2": 1.0}, cap_end=0.003,
            )

    def build_respirator(self) -> None:
        """Mascarilla de dos filtros, colgada al pecho mientras no hace falta."""
        j = self.j
        weights = self.torso_weights
        z = j.arm.z - 0.075
        center, _ = self.torso.on(90.0, z, 0.03)
        self.mask.blob(center, (0.05, 0.03, 0.046), MASK_RUBBER, weights, segments=10, rings=5)
        self.mask.blob(center + FRONT * 0.022 - UP * 0.02, (0.02, 0.012, 0.018), LINING, weights, segments=8, rings=3)
        for sign in (1.0, -1.0):
            axis = Vector((sign * 0.78, -0.56, -0.16)).normalized()
            start = center + axis * 0.026
            rings = pb.path_rings(
                [start, start + axis * 0.01, start + axis * 0.04, start + axis * 0.046],
                [(0.018, 0.018), (0.032, 0.032), (0.032, 0.032), (0.022, 0.022)],
                forward=UP, colors=[MASK_RUBBER, None, LINING, LINING],
            )
            self.mask.tube(rings, MASK_FILTER, segments=10, weights=weights, cap_start=0.0, cap_end=0.0)
            strap = [
                self.torso.on(90.0 - sign * 16.0, z + 0.03, 0.012),
                self.torso.on(90.0 - sign * 26.0, z + 0.08, 0.012),
                self.torso.on(90.0 - sign * 40.0, j.neck.z - 0.01, 0.012),
            ]
            self.mask.strap(strap, 0.016, 0.006, LINING, weights)

    # -- zurrón de la máscara ---------------------------------------------------

    def build_gas_mask_bag(self, side_sign: float) -> None:
        """Zurrón de lona en bandolera, sobre la cadera."""
        j = self.j
        z = j.hips.z - 0.05
        hip_x = self.torso.at(z)[0]
        center = Vector((side_sign * (hip_x + 0.036), 0.035, z))
        hips = {"Hips": 1.0}
        faces = self.bag.box((0.086, 0.165, 0.2), center, CANVAS_BAG, hips, bevel=0.022, cuts=2)
        self.bag.move(faces, lambda co: tb.box_bulge_offset(co, center, Vector((0.043, 0.0825, 0.1)), 0.012))
        # Solapa con su botón.
        flap_x = center.x + side_sign * 0.047
        grid = [
            [
                Vector((flap_x - side_sign * (0.05 if k == 0 else 0.0), center.y + y, center.z + 0.105 - 0.045 * max(0, k - 1)))
                for y in spread(-0.088, 0.088, 4)
            ]
            for k in range(4)
        ]
        self.bag.panel(grid, 0.012, CANVAS_BAG_DARK, hips, normals=[[LEFT * side_sign] * 4 if k > 0 else [UP] * 4 for k in range(4)])
        self.bag.blob((flap_x + side_sign * 0.008, center.y, center.z + 0.03), (0.006, 0.012, 0.012), DULL_METAL, hips, segments=8, rings=3)
        # Correa: sube por la espalda, cruza el hombro contrario y baja por el pecho.
        back = [(205.0, 0.04), (242.0, 0.2), (258.0, 0.45), (284.0, 0.72), (300.0, 0.92)]
        front = [(60.0, 0.92), (78.0, 0.72), (102.0, 0.45), (124.0, 0.2), (152.0, 0.04)]
        low, high = z + 0.07, j.arm.z + 0.012
        path = []
        for degrees, f in back:
            path.append(self.torso.on(degrees if side_sign < 0 else 540.0 - degrees, lerp(low, high, f), 0.012))
        path.append((Vector((-side_sign * 0.095, 0.014, self.shoulder_top(0.095) + 0.012)), UP.copy()))
        for degrees, f in front:
            path.append(self.torso.on(degrees if side_sign < 0 else 180.0 - degrees, lerp(low, high, f), 0.012))
        self.bag.strap(path, 0.034, 0.008, CANVAS_BAG_DARK, self.torso_weights)

    def shoulder_top(self, x: float) -> float:
        """Altura de la parte de arriba del hombro a esa distancia del centro."""
        best = self.torso.rows[0][0]
        for z in spread(self.j.arm.z - 0.05, self.torso.rows[-1][0], 40):
            if self.torso.at(z)[0] >= x:
                best = z
        return best

    def pack_strap(
        self, sign: float, back_degrees: float, top_x: float, bottom_z: float, color: str,
        width: float = 0.036, thickness: float = 0.009,
    ) -> None:
        """Hombrera de mochila: de la espalda, por encima del hombro, a la axila."""
        j = self.j
        shoulder_z = self.shoulder_top(top_x)

        def degrees(value: float) -> float:
            return value if sign > 0 else 180.0 - value

        path = [
            self.torso.on(degrees(back_degrees), shoulder_z - 0.10, 0.014),
            self.torso.on(degrees(back_degrees), shoulder_z - 0.035, 0.014),
            (Vector((sign * top_x, 0.016, shoulder_z + 0.014)), UP.copy()),
            self.torso.on(degrees(64.0), shoulder_z - 0.03, 0.014),
            self.torso.on(degrees(62.0), shoulder_z - 0.10, 0.013),
            self.torso.on(degrees(52.0), j.chest.z + 0.02, 0.013),
            self.torso.on(degrees(30.0), j.chest.z - 0.07, 0.013),
            self.torso.on(degrees(2.0), bottom_z + 0.03, 0.013),
            self.torso.on(degrees(-40.0), bottom_z, 0.013),
        ]
        self.pack.strap(path, width, thickness, color, self.torso_weights)

    def patch(self, degrees: list[float], heights: list[float], color: str) -> None:
        """Remiendo cosido sobre el abrigo, con las puntadas a la vista."""
        weights = self.torso_weights
        grid, normals = self.torso.patch(degrees, heights, 0.006)
        self.cloth.panel(grid, 0.008, color, weights, normals=normals, jitter=0.04)
        rows, cols = len(heights), len(degrees)
        border = (
            [(0, j) for j in range(cols)] + [(i, cols - 1) for i in range(rows)]
            + [(rows - 1, j) for j in range(cols)] + [(i, 0) for i in range(rows)]
        )
        for i, j in border:
            if self.rng.random() < 0.25:
                continue  # puntada saltada
            point = self.torso.surface(degrees[j], heights[i], 0.012)
            self.cloth.box((0.011, 0.005, 0.005), point, THREAD, weights, rotation=Quaternion(FRONT, self.rng.uniform(-0.6, 0.6)))

    def ragged_hem(self, faces: list, hem: float, amount: float) -> None:
        """Bajo deshilachado: el borde de abajo sube y baja sin orden."""
        rng = self.rng
        offsets: dict[int, float] = {}

        def fray(co: Vector) -> Vector:
            if co.z > hem + 0.03:
                return Vector()
            key = round(math.degrees(math.atan2(co.y, co.x)) / 15.0)
            if key not in offsets:
                offsets[key] = rng.uniform(-amount, amount * 0.4)
            return UP * offsets[key]

        self.cloth.move(faces, fray)

    # -- final ---------------------------------------------------------------

    def finish(self, face: str) -> bpy.types.Object:
        look = self.look
        armature = pb.build_armature("esqueleto", self.specs, self.root)
        body = self.cloth.finish("cuerpo", tb.material("ropa", look.coat), self.root)
        skin = self.skin.finish("piel", tb.material("piel", SKIN), self.root)
        scarf = self.scarf.finish("bufanda", tb.material("prenda_jugador", PLAYER_CLOTH), self.root)
        pack = self.pack.finish("mochila", tb.material("ropa", look.coat), self.root)
        bag = self.bag.finish("zurron", tb.material("ropa", look.coat), self.root)
        mask = self.mask.finish("mascarilla", tb.material("ropa", look.coat), self.root)
        seed = look.seed
        # Frío y mugre: la nariz y las orejas enrojecidas, la piel sin lavar.
        pb.tint(skin, self.head.surface(90.0, self.head_z(0.39), 0.02), 0.03, SKIN_COLD, 0.55)
        for sign in (1.0, -1.0):
            pb.tint(skin, self.head.surface(90.0 - sign * 90.0, self.head_z(0.47), 0.012), 0.04, SKIN_COLD, 0.5)
        tb.stain(skin, SKIN_DIRT, amount=0.5, scale=14.0, coverage=0.3, seed=seed)
        # La ropa: grasa y hollín, roces más claros y barro de rodillas abajo.
        for obj, mud_top in ((body, 0.5), (pack, 0.0), (bag, 0.0), (mask, 0.0)):
            tb.stain(obj, GRIME, amount=0.6, scale=6.0, coverage=0.36, seed=seed + 3)
            tb.stain(obj, DUST, amount=0.3, scale=11.0, coverage=0.28, seed=seed + 5)
            if mud_top > 0.0:
                pb.grime(obj, 0.02, mud_top, MUD, 0.75, seed=seed)
        tb.stain(scarf, "#6C6660", amount=0.55, scale=10.0, coverage=0.4, seed=seed + 7)
        tb.wobble(body, amount=0.003, scale=7.0, seed=seed % 97)
        tb.wobble(pack, amount=0.004, scale=6.0, seed=seed % 89)
        tb.paint(
            {body: None, skin: None, scarf: None, pack: None, bag: None, mask: None},
            samples=16, ao=0.6, ao_distance=0.14, cavity_dark=0.38, edge_light=0.08, mottling=0.05, seed=7,
        )
        surface = pb.bvh_of([skin])
        sticker = pb.sticker("cara", self.face_rays(), surface, "Head", tb.material(face, "#FFFFFF"), self.root)
        pb.bind([body, skin, scarf, pack, bag, mask, sticker], armature)
        anim.body_animations(pb.Rig(armature), self)
        return self.root


# --------------------------------------------------------------------------
# El chico
# --------------------------------------------------------------------------


def build_chico() -> bpy.types.Object:
    look = CHICO
    torso = pb.Profile(
        [
            (0.760, 0.180, 0.131, 0.129, 0.004),
            (0.840, 0.185, 0.136, 0.133, 0.004),
            (0.930, 0.176, 0.128, 0.126, 0.004),
            (0.998, 0.161, 0.118, 0.116, 0.004),
            (1.070, 0.171, 0.126, 0.122, 0.005),
            (1.170, 0.187, 0.134, 0.128, 0.007),
            (1.270, 0.195, 0.132, 0.126, 0.010),
            (1.338, 0.187, 0.120, 0.118, 0.012),
            (1.388, 0.134, 0.098, 0.100, 0.012),
            (1.422, 0.078, 0.068, 0.072, 0.010),
        ],
        power=2.5,
    )
    c = Character(look, torso, hem_follow=0.3)
    c.add_bones(c.scarf_bones(1.0, 0.17))
    weights = c.torso_weights

    # Chaqueta acolchada: los canales verticales salen de alternar el radio.
    def quilt(index: int) -> float:
        return 0.972 if index % 2 == 0 else 1.0

    rings = [torso.ring(0.778, scale=0.8, color=LINING), torso.ring(0.760, color=look.coat_dark), torso.ring(0.78)]
    for z in (0.81, 0.85, 0.89, 0.93, 0.965, 1.03, 1.07, 1.12, 1.17, 1.22, 1.27):
        rings.append(torso.ring(z, ripple=quilt))
    for z in (1.31, 1.338, 1.365, 1.388, 1.407, 1.422):
        rings.append(torso.ring(z))
    faces = c.cloth.tube(rings, look.coat, segments=24, weights=weights, cap_start=0.0, cap_end=0.01)
    c.ragged_hem(faces, 0.76, 0.014)
    # Tapeta de los botones; falta uno, y de su sitio cuelga el hilo.
    grid, normals = torso.patch(spread(101.0, 85.0, 3), spread(1.375, 0.775, 9), 0.006)
    c.cloth.panel(grid, 0.011, look.coat_dark, weights, normals=normals)
    for z in (0.84, 1.075, 1.16, 1.245):
        point, _ = torso.on(92.0, z, 0.014)
        c.cloth.blob(point, (0.013, 0.0065, 0.013), LINING, weights, segments=8, rings=3)
    thread, _ = torso.on(92.0, 1.325, 0.012)
    c.cloth.tube(
        [Ring(thread, 0.0025, 0.0025), Ring(thread - UP * 0.028 + LEFT * 0.006, 0.002, 0.002)],
        THREAD, segments=6, weights=weights,
    )
    # Bolsillos de parche: el derecho tiene la tapa descosida.
    for sign in (1.0, -1.0):
        degrees = [90.0 - sign * a for a in spread(22.0, 58.0, 4)]
        grid, normals = torso.patch(degrees, spread(0.935, 0.805, 4), 0.007)
        c.cloth.panel(grid, 0.012, look.coat, weights, normals=normals, jitter=0.05)
        flap, flap_normals = torso.patch(degrees, spread(0.95, 0.905, 2), 0.014)
        if sign < 0:
            flap[1][0] = flap[1][0] - UP * 0.03 + flap_normals[1][0] * 0.014
            flap[1][1] = flap[1][1] - UP * 0.012 + flap_normals[1][1] * 0.006
        c.cloth.panel(flap, 0.01, look.coat_dark, weights, normals=flap_normals)
    # Remiendos.
    c.patch([90.0 - a for a in spread(-48.0, -20.0, 4)], spread(1.21, 1.13, 4), "#6B6350")
    c.patch(spread(250.0, 282.0, 4), spread(0.90, 0.80, 4), "#4E4A41")
    # Cuello de tira.
    collar = []
    for i in range(14):
        theta = 2.0 * math.pi * i / 14
        radial = LEFT * math.cos(theta) + FRONT * math.sin(theta)
        point = Vector((0.0, 0.012, c.j.neck.z + 0.008)) + LEFT * 0.076 * math.cos(theta) + FRONT * 0.072 * math.sin(theta)
        point.z -= 0.016 * math.sin(theta)
        collar.append(Ring(point, 0.014, 0.026, None, radial, UP.copy(), 2.6, {"Chest": 1.0}))
    c.cloth.tube(collar, look.coat_dark, segments=8, closed=True)
    # Cinturón militar, con una bolsa y la funda de la navaja.
    belt = [torso.ring(0.978, -0.004), torso.ring(0.978, 0.009), torso.ring(1.02, 0.009), torso.ring(1.02, -0.004)]
    c.cloth.tube(belt, LEATHER, segments=24, weights=weights, closed=True)
    buckle, _ = torso.on(90.0, 0.999, 0.016)
    c.cloth.box((0.058, 0.012, 0.052), buckle, DULL_METAL, weights, bevel=0.004)
    pouch, _ = torso.on(128.0, 0.985, 0.04)
    c.cloth.box(
        (0.085, 0.05, 0.1), pouch, CANVAS_BAG, weights,
        rotation=Quaternion(UP, math.radians(-38.0)), bevel=0.014, cuts=1,
    )
    lid = [torso.on(a, zz, off) for a, zz, off in ((128.0, 1.04, 0.045), (128.0, 1.036, 0.072), (128.0, 1.0, 0.076))]
    c.cloth.strap(lid, 0.09, 0.008, CANVAS_BAG_DARK, weights)
    sheath, _ = torso.on(38.0, 0.95, 0.022)
    c.cloth.tube(
        [Ring(sheath + UP * 0.05, 0.015, 0.008), Ring(sheath, 0.014, 0.008), Ring(sheath - UP * 0.075, 0.008, 0.006)],
        LEATHER_WORN, segments=8, weights=weights, cap_start=0.002, cap_end=0.004,
    )
    c.cloth.tube(
        [Ring(sheath + UP * 0.052, 0.01, 0.007), Ring(sheath + UP * 0.105, 0.011, 0.008)],
        "#2B211B", segments=8, weights=weights, cap_end=0.004,
    )

    c.build_legs(kneepads=True)
    c.build_boots(felt=False, taped=1.0)
    c.build_sleeves(quilted=True, taped=-1.0, elbow_patch=1.0)
    c.build_hands(taped=("Left", "Index"))
    c.build_head()
    c.build_scarf(1.0, 0.17)
    c.build_respirator()
    _ushanka(c)
    _rucksack(c)
    c.build_gas_mask_bag(-1.0)
    return c.finish("cara_chico")


def _ushanka(c: Character) -> None:
    """Gorro de orejeras del padre, con las orejeras atadas arriba y gafas de soldador."""
    head = {"Head": 1.0}
    cloth_color, fur = "#3B3A35", "#5B5247"
    hp, z, hair = c.head, c.head_z, c.look.hair
    rng = c.rng
    # Pelo sin cortar: mechones en las sienes, la nuca y la frente.
    for sign in (1.0, -1.0):
        lock = []
        for t in (0.68, 0.58, 0.48, 0.40):
            drop = rng.uniform(0.0, 0.012) if t < 0.45 else 0.0
            lock.append([hp.surface(90.0 - sign * a, z(t) - drop, 0.005) for a in spread(64.0, 108.0, 4)])
        c.cloth.panel(lock, 0.01, hair, head, jitter=0.05)
    nape = []
    for t in (0.68, 0.54, 0.40, 0.29):
        nape.append([hp.surface(d, z(t) - (rng.uniform(0.0, 0.016) if t < 0.3 else 0.0), 0.005) for d in spread(196.0, 344.0, 9)])
    c.cloth.panel(nape, 0.011, hair, head, jitter=0.05)
    fringe = []
    for k, t in enumerate((0.72, 0.66, 0.62)):
        fringe.append([hp.surface(d, z(t) - (rng.uniform(0.0, 0.02) if k == 2 else 0.0), 0.006) for d in spread(128.0, 52.0, 7)])
    c.cloth.panel(fringe, 0.009, hair, head)
    # Copa.
    crown = [hp.ring(z(0.66), 0.01), hp.ring(z(0.80), 0.02), hp.ring(z(0.93), 0.024)]
    top = hp.ring(z(0.93), 0.024, scale=0.8)
    top.center.z = z(1.03)
    crown.append(top)
    c.cloth.tube(crown, cloth_color, segments=16, weights=head, cap_start=None, cap_end=0.006)

    # Vuelta de piel apelmazada: las orejeras y la visera, subidas y atadas arriba.
    def matted(index: int) -> float:
        return 1.0 + 0.03 * math.sin(index * 2.7) + 0.018 * math.sin(index * 5.3)

    fur_band = [
        hp.ring(z(0.64), 0.01), hp.ring(z(0.625), 0.026, ripple=matted), hp.ring(z(0.78), 0.031, ripple=matted),
        hp.ring(z(0.93), 0.029, ripple=matted), hp.ring(z(0.96), 0.016),
    ]
    faces = c.cloth.tube(fur_band, fur, segments=24, weights=head, closed=True, jitter=0.03)
    # La visera es más alta por delante.
    c.cloth.move(
        faces,
        lambda co: UP * 0.016 * bump(math.degrees(math.atan2(co.x, -co.y)), 0.0, 40.0) * ramp(co.z, z(0.82), z(0.92)),
    )
    c.cloth.blob((0.0, -0.004, z(1.065)), (0.02, 0.012, 0.009), LINING, head, segments=6, rings=3)
    # Gafas de soldador sobre la visera.
    goggles_z = z(0.80)
    for sign in (1.0, -1.0):
        center, normal = hp.on(90.0 - sign * 21.0, goggles_z, 0.042)
        rings = pb.path_rings(
            [center - normal * 0.016, center + normal * 0.012, center + normal * 0.013, center + normal * 0.006],
            [(0.03, 0.03), (0.03, 0.03), (0.023, 0.023), (0.021, 0.021)],
            forward=UP, colors=[IRON, GLASS, GLASS, GLASS],
        )
        c.cloth.tube(rings, IRON, segments=12, weights=head, cap_start=0.0, cap_end=0.0)
    bridge, _ = hp.on(90.0, goggles_z, 0.044)
    c.cloth.box((0.02, 0.012, 0.016), bridge, LEATHER, head, bevel=0.003)
    strap = [
        hp.ring(goggles_z - 0.011, 0.03), hp.ring(goggles_z - 0.011, 0.037),
        hp.ring(goggles_z + 0.011, 0.037), hp.ring(goggles_z + 0.011, 0.03),
    ]
    c.cloth.tube(strap, LINING, segments=24, weights=head, closed=True)


def _rucksack(c: Character) -> None:
    """Macuto de lona con la lona enrollada, la cuerda y la palanca."""
    canvas, canvas_dark, tarp = "#6B634C", "#565040", "#4F5348"
    weights = blend({"Chest": 1.0}, {"Spine": 1.0}, 0.3)
    z = c.j.chest.z - 0.005
    back = c.torso.at(z)[2] + c.torso.at(z)[3]
    center = Vector((0.0, back + 0.085, z))
    half = Vector((0.15, 0.08, 0.185))
    faces = c.pack.box(half * 2.0, center, canvas, weights, bevel=0.035, cuts=3)
    c.pack.move(
        faces,
        lambda co: tb.box_bulge_offset(co, center, half, 0.016)
        + UP * (-0.02 * max(0.0, co.z - center.z) * abs(co.x) / half.x),
    )
    # Tapa que cae sobre la cara de atrás, con dos correas.
    outer_y = center.y + half.y
    flap = []
    for y, zz in ((center.y - 0.07, 0.196), (center.y, 0.206), (outer_y + 0.01, 0.196), (outer_y + 0.024, 0.12), (outer_y + 0.026, 0.02)):
        flap.append([Vector((x, y, center.z + zz)) for x in spread(-0.14, 0.14, 5)])
    c.pack.panel(flap, 0.014, canvas_dark, weights)
    for x in (-0.075, 0.075):
        strap = [(Vector((x, outer_y + 0.034, center.z + zz)), -FRONT) for zz in (0.13, 0.03, -0.07, -0.14)]
        c.pack.strap(strap, 0.028, 0.008, LEATHER, weights)
        c.pack.box((0.038, 0.012, 0.03), (x, outer_y + 0.042, center.z - 0.02), DULL_METAL, weights, bevel=0.003)
    # Un remiendo grande en la lona.
    patch = [[Vector((x, outer_y + 0.02, center.z + zz)) for x in spread(-0.035, 0.05, 3)] for zz in (-0.06, -0.15)]
    c.pack.panel(patch, 0.008, "#7C7560", weights, normals=[[-FRONT] * 3] * 2)
    # Bolsillos laterales.
    for sign in (1.0, -1.0):
        pocket = Vector((sign * (half.x + 0.022), center.y + 0.005, center.z - 0.07))
        faces = c.pack.box((0.06, 0.12, 0.17), pocket, canvas, weights, bevel=0.02, cuts=1, jitter=0.04)
        c.pack.move(faces, lambda co, p=pocket: tb.box_bulge_offset(co, p, Vector((0.03, 0.06, 0.085)), 0.008))
    # Lona enrollada, atada con cuerda.
    roll_z = center.z + half.z + 0.062
    roll = [
        Ring(Vector((x, center.y + 0.005, roll_z + 0.005 * math.sin(k * 1.7))), r, r * 0.92, None, FRONT.copy(), UP.copy())
        for k, (x, r) in enumerate(((-0.205, 0.045), (-0.19, 0.064), (-0.1, 0.069), (0.0, 0.065), (0.1, 0.07), (0.19, 0.064), (0.205, 0.045)))
    ]
    c.pack.tube(roll, tarp, segments=12, weights=weights, cap_start=-0.014, cap_end=-0.014)
    for x in (-0.11, 0.1):
        band(c.pack, Vector((x, center.y + 0.005, roll_z)), LEFT, 0.071, 0.012, HEMP, weights, thick=0.005)
    # Cuerda enrollada, colgada del lado derecho.
    coil = Vector((-(half.x + 0.058), center.y + 0.012, center.z + 0.02))
    for loop, (radius, dx) in enumerate(((0.07, 0.0), (0.078, 0.011), (0.066, -0.01))):
        rings = []
        for i in range(12):
            phi = 2.0 * math.pi * i / 12 + loop
            radial = -FRONT * math.cos(phi) + UP * math.sin(phi)
            stretch = 1.0 if radial.z > -0.3 else 1.18
            rings.append(Ring(coil + LEFT * dx + radial * radius * stretch, 0.0105, 0.0105, None, radial, LEFT.copy()))
        c.pack.tube(rings, HEMP, segments=6, weights=weights, closed=True, jitter=0.05)
    # La palanca, sujeta al otro lado.
    bar_x, bar_y = half.x + 0.06, center.y + 0.02
    bar = [
        Vector((bar_x, bar_y, center.z - 0.2)), Vector((bar_x, bar_y, center.z + 0.2)), Vector((bar_x, bar_y, center.z + 0.36)),
        Vector((bar_x, bar_y + 0.012, center.z + 0.395)), Vector((bar_x, bar_y + 0.04, center.z + 0.4)),
        Vector((bar_x, bar_y + 0.058, center.z + 0.375)),
    ]
    c.pack.tube(
        pb.path_rings(bar, [(0.011, 0.011)] * 5 + [(0.007, 0.015)], forward=LEFT),
        IRON, segments=6, weights=weights, cap_start=0.004, cap_end=0.004,
    )
    for zz in (-0.12, 0.02):
        c.pack.box((0.03, 0.036, 0.022), (bar_x - 0.006, bar_y, center.z + zz), LEATHER, weights, bevel=0.004)
    for sign in (1.0, -1.0):
        c.pack_strap(sign, 304.0, 0.105, c.j.spine.z, LEATHER)


# --------------------------------------------------------------------------
# La chica
# --------------------------------------------------------------------------


def build_chica() -> bpy.types.Object:
    look = CHICA
    torso = pb.Profile(
        [
            (0.500, 0.208, 0.160, 0.164, 0.006),
            (0.600, 0.200, 0.153, 0.155, 0.005),
            (0.740, 0.184, 0.138, 0.138, 0.004),
            (0.860, 0.168, 0.124, 0.124, 0.004),
            (0.955, 0.152, 0.113, 0.111, 0.004),
            (1.040, 0.162, 0.121, 0.117, 0.005),
            (1.140, 0.176, 0.127, 0.121, 0.007),
            (1.230, 0.182, 0.125, 0.119, 0.010),
            (1.292, 0.174, 0.113, 0.112, 0.012),
            (1.340, 0.125, 0.093, 0.095, 0.012),
            (1.372, 0.074, 0.065, 0.069, 0.010),
        ],
        power=2.4,
    )
    c = Character(look, torso, hem_follow=0.55)
    j = c.j
    braid_points = _braid_path(c)
    c.add_bones(
        c.scarf_bones(-1.0, 0.15)
        + [
            pb.BoneSpec("Trenza1", "Head", braid_points[0], braid_points[9]),
            pb.BoneSpec("Trenza2", "Trenza1", braid_points[9], braid_points[17]),
            pb.BoneSpec("Trenza3", "Trenza2", braid_points[17], braid_points[-1]),
        ]
    )
    weights = c.torso_weights

    # Capote militar, demasiado grande: le llega a las rodillas.
    rings = [torso.ring(0.52, scale=0.86, color=LINING), torso.ring(0.500, color=look.coat_dark), torso.ring(0.522)]
    for z in (0.56, 0.61, 0.67, 0.74, 0.80, 0.86, 0.91, 0.955, 1.0, 1.04, 1.09, 1.14, 1.19, 1.23, 1.265, 1.292, 1.318, 1.34, 1.358, 1.372):
        rings.append(torso.ring(z))
    faces = c.cloth.tube(rings, look.coat, segments=20, weights=weights, cap_start=0.0, cap_end=0.01)
    # Pliegues del vuelo, más marcados cuanto más abajo, y el bajo roto.
    c.cloth.move(
        faces,
        lambda co: Vector((co.x, co.y - 0.004, 0.0)).normalized()
        * 0.015 * ramp(0.94 - co.z, 0.0, 0.4) * math.sin(math.atan2(co.y, co.x) * 7.0),
    )
    c.ragged_hem(faces, 0.5, 0.024)
    # Cruzado, con dos filas de botones de latón sin brillo; faltan dos.
    grid, normals = torso.patch(spread(113.0, 69.0, 5), spread(1.31, 0.505, 10), 0.006)
    c.cloth.panel(grid, 0.012, look.coat, weights, normals=normals, jitter=0.02)
    for z, columns in ((1.04, (100.0, 77.0)), (1.13, (100.0,)), (1.22, (100.0, 77.0)), (0.86, (77.0,))):
        for degrees in columns:
            point, _ = torso.on(degrees, z, 0.016)
            c.cloth.blob(point, (0.014, 0.007, 0.014), DULL_METAL, weights, segments=8, rings=3)
    # Atado con una cuerda en vez de cinturón.
    for offset in (-0.012, 0.012):
        low, high = 0.955 + offset - 0.009, 0.955 + offset + 0.009
        rope = [torso.ring(low, 0.0), torso.ring(low, 0.013), torso.ring(high, 0.013), torso.ring(high, 0.0)]
        c.cloth.tube(rope, HEMP, segments=20, weights=weights, closed=True, jitter=0.04)
    knot, _ = torso.on(108.0, 0.955, 0.024)
    c.cloth.blob(knot, (0.024, 0.016, 0.026), HEMP, weights, segments=8, rings=3)
    for swing in (-9.0, 13.0):
        tail = [torso.on(108.0 + swing * f, 0.95 - 0.15 * f, 0.022) for f in spread(0.0, 1.0, 4)]
        c.cloth.tube(
            [Ring(point, 0.0085, 0.0085, None, UP.cross(normal).normalized(), normal) for point, normal in tail],
            HEMP, segments=6, weights=weights, cap_end=0.006,
        )
    # Remiendos y un bolsillo descosido.
    c.patch([90.0 - a for a in spread(30.0, 62.0, 4)], spread(0.72, 0.60, 4), "#4A4640")
    c.patch(spread(236.0, 262.0, 4), spread(1.14, 1.05, 4), "#6C675B")
    pocket = [torso.on(90.0 + a, zz, 0.008) for a, zz in ((36.0, 0.86), (46.0, 0.815), (56.0, 0.77))]
    c.cloth.strap(pocket, 0.03, 0.01, look.coat_dark, weights)
    # Cuello subido: le tapa la nuca y las mejillas.
    collar, collar_normals = [], []
    levels = ((j.arm.z + 0.015, 0.1), (j.neck.z - 0.005, 0.088), (j.neck.z + 0.045, 0.094), (j.neck.z + 0.085, 0.108))
    for k, (zz, radius) in enumerate(levels):
        row, row_normals = [], []
        for degrees in spread(128.0, 412.0, 15):
            theta = math.radians(degrees)
            radial = LEFT * math.cos(theta) * 1.06 + FRONT * math.sin(theta) * 0.94
            droop = 0.03 * max(0.0, math.sin(theta)) ** 2 * (k / 3.0)
            row.append(Vector((0.0, 0.016, zz - droop)) + radial * radius)
            row_normals.append((LEFT * math.cos(theta) + FRONT * math.sin(theta)).normalized())
        collar.append(row)
        collar_normals.append(row_normals)
    c.cloth.panel(
        collar, 0.013, look.coat_dark, blend({"Chest": 1.0}, {"Neck": 1.0}, 0.25),
        normals=collar_normals, inner_color=look.coat,
    )

    c.build_legs(kneepads=False)
    c.build_boots(felt=True, taped=-1.0)
    c.build_sleeves(quilted=False, taped=1.0)
    c.build_hands(taped=("Right", "Middle"))
    c.build_head()
    c.build_scarf(-1.0, 0.15)
    c.build_respirator()
    _knit_cap(c, braid_points)
    _kit_bag(c)
    c.build_gas_mask_bag(1.0)
    return c.finish("cara_chica")


def _braid_path(c: Character) -> list[Vector]:
    """La trenza sale de la nuca, pasa sobre el hombro izquierdo y cae por delante."""
    j = c.j
    z = c.head_z
    control = [
        c.head.surface(292.0, z(0.34), 0.01),
        c.head.surface(316.0, z(0.14), 0.03),
        Vector((0.10, 0.05, j.neck.z + 0.05)),
        Vector((0.13, -0.02, j.neck.z + 0.03)),
        c.torso.surface(50.0, j.arm.z - 0.05, 0.036),
        c.torso.surface(56.0, j.arm.z - 0.14, 0.03),
        c.torso.surface(58.0, j.arm.z - 0.22, 0.028),
    ]
    points = []
    for a, b in zip(control, control[1:]):
        points += [a.lerp(b, f) for f in (0.0, 0.25, 0.5, 0.75)]
    return points + [control[-1]]


def _knit_cap(c: Character, braid_points: list[Vector]) -> None:
    """Gorro de punto oscuro, calado hasta las cejas, y la trenza."""
    head = {"Head": 1.0}
    knit, hair = "#33363A", c.look.hair
    hp, z, rng = c.head, c.head_z, c.rng

    def rib(index: int) -> float:
        return 0.965 if index % 2 == 0 else 1.0

    # Mechones sueltos sobre la frente y a los lados de la cara.
    fringe = []
    for k, t in enumerate((0.70, 0.64, 0.585)):
        fringe.append([hp.surface(d, z(t) - (rng.uniform(0.0, 0.026) if k == 2 else 0.0), 0.006) for d in spread(134.0, 46.0, 8)])
    c.cloth.panel(fringe, 0.009, hair, head, jitter=0.04)
    for sign in (1.0, -1.0):
        lock = []
        for t, wide in ((0.62, 0.0), (0.48, 3.0), (0.33, 5.0), (0.19, 3.0), (0.07, -4.0)):
            lock.append([hp.surface(90.0 - sign * a, z(t), 0.006) for a in spread(66.0 - wide, 96.0 + wide, 3)])
        c.cloth.panel(lock, 0.011, hair, head, jitter=0.04)
    nape = [[hp.surface(d, z(t), 0.006) for d in spread(190.0, 350.0, 9)] for t in (0.6, 0.44, 0.3, 0.18)]
    c.cloth.panel(nape, 0.011, hair, head, jitter=0.04)
    # Gorro acanalado, con la vuelta estrecha.
    crown = [
        hp.ring(z(0.60), 0.01), hp.ring(z(0.70), 0.014, ripple=rib), hp.ring(z(0.82), 0.017, ripple=rib),
        hp.ring(z(0.92), 0.019, ripple=rib), hp.ring(z(0.97), 0.02, ripple=rib),
    ]
    tip = hp.ring(z(0.97), 0.02, scale=0.45, ripple=rib)
    tip.center.z = z(1.045)
    crown.append(tip)
    c.cloth.tube(crown, knit, segments=24, weights=head, cap_start=None, cap_end=0.006)
    brim = [
        hp.ring(z(0.60), 0.008), hp.ring(z(0.595), 0.022, ripple=rib),
        hp.ring(z(0.675), 0.024, ripple=rib), hp.ring(z(0.69), 0.012),
    ]
    c.cloth.tube(brim, "#2B2E31", segments=24, weights=head, closed=True)
    # Trenza: cabos alternados y apretados.
    bones = ("Trenza1", "Trenza2", "Trenza3")
    count = len(braid_points)
    for index, point in enumerate(braid_points):
        f = index / (count - 1)
        before, after = braid_points[max(0, index - 1)], braid_points[min(count - 1, index + 1)]
        axis = (after - before).normalized()
        across = axis.cross(FRONT).normalized()
        w = head if index < 2 else {bones[0 if index < 9 else 1 if index < 17 else 2]: 1.0}
        radius = lerp(0.021, 0.015, f)
        tilt = Quaternion(axis.cross(across), math.radians(30.0 if index % 2 else -30.0))
        c.cloth.blob(
            point + across * (0.008 if index % 2 else -0.008), (radius * 0.8, radius, radius * 1.55), hair, w,
            rotation=tilt @ UP.rotation_difference(axis), segments=8, rings=4, jitter=0.06,
        )
    tip_point, axis = braid_points[-1], (braid_points[-1] - braid_points[-2]).normalized()
    tail = {"Trenza3": 1.0}
    side = LEFT.copy()
    forward = axis.cross(side).normalized()
    # La ata un trapo del color del jugador.
    c.scarf.tube(
        [
            Ring(tip_point - axis * 0.006, 0.017, 0.017, None, side, forward),
            Ring(tip_point + axis * 0.012, 0.018, 0.018, None, side, forward),
        ],
        PLAYER_CLOTH, segments=8, weights=tail, cap_start=0.003, cap_end=0.003,
    )
    for sign, length in ((1.0, 0.05), (-1.0, 0.034)):
        start = tip_point + axis * 0.004 + side * sign * 0.016
        c.scarf.tube(
            [
                Ring(start, 0.008, 0.004, None, side, forward),
                Ring(start + axis * length + side * sign * 0.014, 0.007, 0.003, None, side, forward),
            ],
            PLAYER_CLOTH, segments=6, weights=tail, cap_end=0.002,
        )
    c.cloth.tube(
        [
            Ring(tip_point + axis * 0.01, 0.013, 0.013, None, side, forward),
            Ring(tip_point + axis * 0.04, 0.016, 0.016, None, side, forward),
            Ring(tip_point + axis * 0.075, 0.006, 0.006, None, side, forward),
        ],
        hair, segments=8, weights=tail, cap_start=0.0, cap_end=0.008,
    )


def _kit_bag(c: Character) -> None:
    """Petate de lona atado con su propia cuerda, con la tetera colgando."""
    canvas, soot = "#615C4B", "#232221"
    weights = blend({"Chest": 1.0}, {"Spine": 1.0}, 0.35)
    j = c.j
    back = c.torso.at(j.chest.z)[2] + c.torso.at(j.chest.z)[3]
    y = back + 0.082

    def section(zz: float, rx: float, depth: float, lean: float = 0.0) -> Ring:
        return Ring(Vector((0.0, y + lean, j.chest.z + zz)), rx, depth, depth * 0.95, LEFT.copy(), FRONT.copy(), 2.6)

    sack = [
        section(-0.21, 0.105, 0.062), section(-0.17, 0.142, 0.082), section(-0.08, 0.152, 0.09), section(0.02, 0.146, 0.086),
        section(0.10, 0.118, 0.074, -0.006), section(0.15, 0.07, 0.05, -0.012), section(0.172, 0.04, 0.034, -0.014),
        section(0.195, 0.056, 0.044, -0.012), section(0.21, 0.05, 0.04, -0.01),
    ]
    faces = c.pack.tube(sack, canvas, segments=14, weights=weights, cap_start=0.02, cap_end=-0.012)
    # Bultos: lo que lleva dentro se marca en la lona.
    c.pack.move(
        faces,
        lambda co: Vector((co.x, co.y - y, 0.0)).normalized()
        * 0.012 * math.sin(co.z * 31.0 + co.x * 17.0) * ramp(j.chest.z + 0.1 - co.z, 0.0, 0.1),
    )
    band(c.pack, Vector((0.0, y - 0.014, j.chest.z + 0.172)), UP, 0.04, 0.02, HEMP, weights, thick=0.006, segments=10)
    patch = [[Vector((x, y + 0.092, j.chest.z + zz)) for x in spread(-0.07, 0.01, 3)] for zz in (-0.03, -0.12)]
    c.pack.panel(patch, 0.008, "#77715D", weights, normals=[[-FRONT] * 3] * 2)
    # Tetera tiznada, colgada de un costado.
    kettle = Vector((-0.178, y + 0.02, j.chest.z - 0.13))
    c.pack.blob(kettle, (0.058, 0.058, 0.05), soot, weights, segments=10, rings=5)
    spout = [kettle + Vector((-0.04, 0.0, 0.0)), kettle + Vector((-0.075, 0.0, 0.02)), kettle + Vector((-0.09, 0.0, 0.05))]
    c.pack.tube(
        pb.path_rings(spout, [(0.012, 0.012), (0.009, 0.009), (0.007, 0.007)], forward=FRONT),
        soot, segments=6, weights=weights, cap_end=0.0,
    )
    handle = [kettle + Vector((0.0, dy, dz)) for dy, dz in ((-0.05, 0.02), (-0.04, 0.07), (0.0, 0.092), (0.04, 0.07), (0.05, 0.02))]
    c.pack.tube(pb.path_rings(handle, [(0.0045, 0.0045)] * 5, forward=LEFT), DULL_METAL, segments=6, weights=weights)
    c.pack.blob(kettle + UP * 0.05, (0.03, 0.03, 0.012), soot, weights, segments=8, rings=3)
    # Las hombreras son la misma cuerda que cierra el saco.
    for sign in (1.0, -1.0):
        c.pack_strap(sign, 292.0, 0.09, j.spine.z - 0.02, HEMP, width=0.02, thickness=0.014)


# --------------------------------------------------------------------------
# Manos de primera persona
# --------------------------------------------------------------------------

FP_CURL = (16.0, 20.0, 12.0)
FP_ARM_X = 0.16
FP_FOREARM = 0.3


def build_first_person_hands(look: Look) -> bpy.types.Object:
    """Antebrazos y manos tal como se ven desde los ojos, con dedos articulados.

    En reposo apuntan al frente (+Y) con las palmas enfrentadas y los pulgares
    arriba. La derecha es +X, como la ve la cámara.
    """
    root = tb.empty(f"manos_{look.name}")
    frames: dict[str, HandFrame] = {}
    specs: list[pb.BoneSpec] = []
    sides = ((-1.0, "Left"), (1.0, "Right"))
    for sign, side in sides:
        wrist = Vector((sign * FP_ARM_X, 0.0, 0.0))
        elbow = wrist - Vector((0.0, FP_FOREARM, 0.0))
        frame = HandFrame(wrist + Vector((0.0, 0.012, 0.0)), UP.copy(), -FRONT, LEFT * sign)
        frames[side] = frame
        specs += [
            pb.BoneSpec(f"{side}LowerArm", None, elbow, wrist),
            pb.BoneSpec(f"{side}Hand", f"{side}LowerArm", wrist, wrist + Vector((0.0, 0.085, 0.0))),
        ]
        specs += hand_bones(side, frame, FP_CURL)
    names = [spec.name for spec in specs]
    cloth, skin = pb.Sculpt(names, look.seed + 50), pb.Sculpt(names, look.seed + 51)
    quilted = look.name == "chico"
    taped = ("Left", "Index") if quilted else ("Right", "Middle")
    for sign, side in sides:
        wrist = Vector((sign * FP_ARM_X, 0.0, 0.0))
        lower = {f"{side}LowerArm": 1.0}
        rings = []
        stations = spread(-FP_FOREARM - 0.06, -0.082, 9)
        for index, y in enumerate(stations):
            radius = lerp(0.061, 0.054, index / (len(stations) - 1))
            if index > 0:
                radius += (0.0035 if index % 2 == 0 else -0.003) if quilted else 0.003 * math.sin(index * 2.4)
            rings.append(Ring(wrist + Vector((0.0, y, 0.0)), radius, radius, None, LEFT.copy(), UP.copy(), 2.0, lower))
        for y, radius, color in ((-0.078, 0.066, look.cuff), (-0.016, 0.067, look.cuff), (-0.008, 0.046, LINING)):
            rings.append(Ring(wrist + Vector((0.0, y, 0.0)), radius, radius, None, LEFT.copy(), UP.copy(), 2.0, lower, color))
        cloth.tube(rings, look.coat, segments=12, cap_start=0.0, cap_end=0.0)
        finger = taped[1] if taped[0] == side else None
        build_hand(cloth, skin, side, frames[side], FP_CURL, articulated=True, taped=finger)
    armature = pb.build_armature("esqueleto", specs, root)
    sleeves = cloth.finish("mangas", tb.material("ropa", look.coat), root)
    fingers = skin.finish("piel", tb.material("piel", SKIN), root)
    tb.stain(sleeves, GRIME, amount=0.6, scale=6.0, coverage=0.36, seed=look.seed + 3)
    tb.stain(sleeves, DUST, amount=0.3, scale=11.0, coverage=0.28, seed=look.seed + 5)
    tb.stain(fingers, SKIN_DIRT, amount=0.55, scale=30.0, coverage=0.35, seed=look.seed)
    tb.wobble(sleeves, amount=0.002, scale=7.0, seed=31)
    tb.paint(
        {sleeves: None, fingers: None},
        samples=16, ao=0.6, ao_distance=0.1, cavity_dark=0.38, edge_light=0.08, mottling=0.05, ground_z=None, seed=9,
    )
    pb.bind([sleeves, fingers], armature)
    anim.hand_animations(pb.Rig(armature))
    return root


# --------------------------------------------------------------------------
# La gente de la estación (clientes y la vendedora del puesto)
# --------------------------------------------------------------------------
# Más años que los protagonistas y otra ropa: abrigo largo o chaqueta acolchada,
# gorra de visera, pañuelo o el pelo al aire, a veces un delantal. Sin mochila
# ni máscara: viven abajo. La bufanda la tiñe el juego, como la de los jugadores.

RELOJERO = Look(
    name="relojero", scale=0.97, shoulder=0.15,
    coat="#3B3842", coat_dark="#2C2A31", cuff="#46434D",
    trousers="#35322E", hair="#8E8A84",
    boot="#2A2622", boot_cuff="#36302B", seed=300,
)
VENDEDORA = Look(
    name="vendedora", scale=0.93, shoulder=0.148,
    coat="#5E4E40", coat_dark="#4A3D32", cuff="#6E5E4E",
    trousers="#3A322C", hair="#77706A",
    boot="#4E4842", boot_cuff="#5A544C", seed=400,
)
VECINA = Look(
    name="vecina", scale=0.95, shoulder=0.146,
    coat="#4C5A5E", coat_dark="#3C474A", cuff="#5A686C",
    trousers="#3A3530", hair="#4A3628",
    boot="#3A3430", boot_cuff="#48413B", seed=500,
)
CHATARRERO = Look(
    name="chatarrero", scale=1.02, shoulder=0.165,
    coat="#4E4A36", coat_dark="#3E3B2B", cuff="#5E5A44",
    trousers="#3E3A32", hair="#2A2420",
    boot="#2C2824", boot_cuff="#3A3530", seed=600,
)


def _man_torso(belly: float) -> pb.Profile:
    """El tronco de un hombre (el del chico, con algo de tripa si los años la dan)."""
    rows = [
        (0.500, 0.196, 0.146, 0.142, 0.004),
        (0.640, 0.188, 0.140, 0.136, 0.004),
        (0.760, 0.180 + belly * 0.5, 0.131 + belly, 0.129, 0.004),
        (0.840, 0.185 + belly * 0.7, 0.136 + belly * 1.4, 0.133, 0.004),
        (0.930, 0.176 + belly * 0.6, 0.128 + belly * 1.3, 0.126, 0.004),
        (0.998, 0.165 + belly * 0.3, 0.12 + belly * 0.7, 0.116, 0.004),
        (1.070, 0.171, 0.126, 0.122, 0.005),
        (1.170, 0.187, 0.134, 0.128, 0.007),
        (1.270, 0.195, 0.132, 0.126, 0.010),
        (1.338, 0.187, 0.120, 0.118, 0.012),
        (1.388, 0.134, 0.098, 0.100, 0.012),
        (1.422, 0.078, 0.068, 0.072, 0.010),
    ]
    return pb.Profile(rows, power=2.5)


def _woman_torso() -> pb.Profile:
    """El tronco de una mujer de la estación, más ancho de caderas que la chica."""
    rows = [
        (0.480, 0.222, 0.168, 0.172, 0.006),
        (0.600, 0.214, 0.160, 0.164, 0.005),
        (0.740, 0.198, 0.148, 0.150, 0.004),
        (0.860, 0.180, 0.136, 0.134, 0.004),
        (0.955, 0.166, 0.126, 0.120, 0.004),
        (1.040, 0.172, 0.132, 0.122, 0.005),
        (1.140, 0.182, 0.136, 0.124, 0.007),
        (1.230, 0.184, 0.128, 0.120, 0.010),
        (1.292, 0.174, 0.114, 0.112, 0.012),
        (1.340, 0.125, 0.093, 0.095, 0.012),
        (1.372, 0.074, 0.065, 0.069, 0.010),
    ]
    return pb.Profile(rows, power=2.4)


def _long_coat(c: Character, hem: float, belt: str | None) -> None:
    """Abrigo largo cruzado, con botones (falta alguno) y, si lo hay, cinturón."""
    torso, look, weights = c.torso, c.look, c.torso_weights
    top = torso.rows[-1][0]
    heights = [hem + 0.02 + k * 0.06 for k in range(int((1.3 - hem) / 0.06))]
    rings = [torso.ring(hem + 0.02, scale=0.86, color=LINING), torso.ring(hem, color=look.coat_dark), torso.ring(hem + 0.022)]
    rings += [torso.ring(z) for z in heights[1:]]
    rings += [torso.ring(z) for z in (1.31, 1.338, 1.36, 1.39, 1.41) if z < top]
    faces = c.cloth.tube(rings, look.coat, segments=22, weights=weights, cap_start=0.0, cap_end=0.01)
    c.cloth.move(
        faces,
        lambda co: Vector((co.x, co.y - 0.004, 0.0)).normalized()
        * 0.012 * ramp(0.9 - co.z, 0.0, 0.4) * math.sin(math.atan2(co.y, co.x) * 6.0),
    )
    c.ragged_hem(faces, hem, 0.012)
    grid, normals = torso.patch(spread(112.0, 70.0, 5), spread(1.3, hem + 0.01, 10), 0.006)
    c.cloth.panel(grid, 0.012, look.coat, weights, normals=normals, jitter=0.02)
    for z in (1.18, 1.05, 0.92, 0.79):
        for degrees in (100.0, 78.0):
            if c.rng.random() < 0.15:
                continue
            point, _ = torso.on(degrees, z, 0.016)
            c.cloth.blob(point, (0.013, 0.007, 0.013), DULL_METAL, weights, segments=8, rings=3)
    if belt is not None:
        z0 = 0.975
        strap = [torso.ring(z0 - 0.02, 0.0), torso.ring(z0 - 0.02, 0.012), torso.ring(z0 + 0.02, 0.012), torso.ring(z0 + 0.02, 0.0)]
        c.cloth.tube(strap, belt, segments=22, weights=weights, closed=True)
    c.patch(spread(240.0, 266.0, 4), spread(1.12, 1.04, 4), look.cuff)


def _quilted_jacket(c: Character, hem: float) -> None:
    """Chaqueta acolchada (la de todo el mundo bajo tierra), hasta la cadera."""
    torso, look, weights = c.torso, c.look, c.torso_weights

    def quilt(index: int) -> float:
        return 0.972 if index % 2 == 0 else 1.0

    rings = [torso.ring(hem + 0.018, scale=0.8, color=LINING), torso.ring(hem, color=look.coat_dark), torso.ring(hem + 0.02)]
    z = hem + 0.06
    while z < 1.3:
        rings.append(torso.ring(z, ripple=quilt))
        z += 0.045
    for z in (1.31, 1.338, 1.365, 1.388, 1.407):
        rings.append(torso.ring(z))
    faces = c.cloth.tube(rings, look.coat, segments=24, weights=weights, cap_start=0.0, cap_end=0.01)
    c.ragged_hem(faces, hem, 0.01)
    grid, normals = torso.patch(spread(98.0, 84.0, 3), spread(1.36, hem + 0.01, 9), 0.006)
    c.cloth.panel(grid, 0.011, look.coat_dark, weights, normals=normals)
    c.patch([90.0 - a for a in spread(-50.0, -22.0, 4)], spread(1.2, 1.12, 4), look.cuff)


def _skirt(c: Character, top: float, hem: float, color: str) -> None:
    """Falda de lana larga, que se abre hacia abajo."""
    torso, weights = c.torso, c.torso_weights
    rings = [torso.ring(hem + 0.015, scale=0.92, color=LINING), torso.ring(hem, inflate=0.03, color=color)]
    z = hem + 0.05
    while z < top:
        rings.append(torso.ring(z, inflate=0.03 * (top - z) / (top - hem) + 0.006))
        z += 0.06
    faces = c.cloth.tube(rings, color, segments=22, weights=weights, cap_start=0.0, cap_end=None)
    c.ragged_hem(faces, hem, 0.01)


def _apron(c: Character, color: str) -> None:
    """Delantal de faena atado a la cintura, con el peto y la tira al cuello."""
    torso, weights = c.torso, c.torso_weights
    grid, normals = torso.patch(spread(122.0, 58.0, 6), spread(0.97, 0.55, 7), 0.038)
    c.cloth.panel(grid, 0.006, color, weights, normals=normals, jitter=0.03)
    bib, bib_normals = torso.patch(spread(108.0, 72.0, 4), spread(1.22, 0.98, 4), 0.026)
    c.cloth.panel(bib, 0.006, color, weights, normals=bib_normals)
    tie = [torso.ring(0.965, 0.024), torso.ring(0.965, 0.03), torso.ring(0.985, 0.03), torso.ring(0.985, 0.024)]
    c.cloth.tube(tie, color, segments=22, weights=weights, closed=True)
    pocket, pocket_normals = torso.patch(spread(104.0, 82.0, 3), spread(0.84, 0.74, 3), 0.036)
    c.cloth.panel(pocket, 0.005, "#A89A80", weights, normals=pocket_normals)


def _hair(c: Character, color: str, crown: bool, bun: bool = False) -> None:
    """El pelo: mechones en las sienes y la nuca; con ``crown``, también arriba
    (sin gorra); con ``bun``, recogido en un moño."""
    head = {"Head": 1.0}
    hp, z = c.head, c.head_z
    for sign in (1.0, -1.0):
        lock = [[hp.surface(90.0 - sign * a, z(t), 0.004) for a in spread(66.0, 110.0, 4)] for t in (0.7, 0.6, 0.5, 0.42)]
        c.cloth.panel(lock, 0.008, color, head, jitter=0.05)
    nape = [[hp.surface(d, z(t), 0.004) for d in spread(196.0, 344.0, 9)] for t in (0.7, 0.56, 0.42, 0.32)]
    c.cloth.panel(nape, 0.009, color, head, jitter=0.05)
    if crown:
        rings = [hp.ring(z(0.66), 0.006), hp.ring(z(0.8), 0.012), hp.ring(z(0.92), 0.012)]
        top = hp.ring(z(0.92), 0.012, scale=0.7)
        top.center.z = z(1.0)
        rings.append(top)
        c.cloth.tube(rings, color, segments=16, weights=head, cap_start=None, cap_end=0.004, jitter=0.04)
    if bun:
        back = hp.surface(270.0, z(0.72), 0.03)
        c.cloth.blob(back, (0.045, 0.04, 0.04), color, head, segments=10, rings=5)


def _flat_cap(c: Character, color: str) -> None:
    """Gorra de visera de paño, calada hasta las cejas."""
    head = {"Head": 1.0}
    hp, z = c.head, c.head_z
    rings = [hp.ring(z(0.64), 0.008), hp.ring(z(0.72), 0.02), hp.ring(z(0.84), 0.034, scale=1.04)]
    top = hp.ring(z(0.88), 0.03, scale=0.95)
    top.center.z = z(0.95)
    top.center.y -= 0.012
    rings.append(top)
    c.cloth.tube(rings, color, segments=18, weights=head, cap_start=None, cap_end=0.004)
    brim, _ = hp.on(90.0, z(0.665), 0.03)
    c.cloth.box(
        (0.13, 0.065, 0.012), brim + FRONT * 0.025 + UP * 0.004, LINING, head,
        rotation=Quaternion(LEFT, math.radians(-12.0)), bevel=0.004,
    )


def _headscarf(c: Character, color: str) -> None:
    """Pañuelo de lana atado a la nuca: tapa el pelo y las orejas, la cara al aire."""
    head = {"Head": 1.0}
    hp, z = c.head, c.head_z
    back = [[hp.surface(d, z(t), 0.012 + 0.004 * (1.0 - t)) for d in spread(140.0, 400.0, 14)] for t in (0.97, 0.86, 0.72, 0.58, 0.44, 0.32)]
    c.cloth.panel(back, 0.008, color, head, jitter=0.03)
    brow = [[hp.surface(d, z(t), 0.012) for d in spread(48.0, 132.0, 6)] for t in (0.98, 0.9, 0.78)]
    c.cloth.panel(brow, 0.008, color, head, jitter=0.03)
    knot = hp.surface(270.0, z(0.3), 0.03)
    c.cloth.blob(knot, (0.03, 0.024, 0.026), color, head, segments=8, rings=4)
    for swing in (-1.0, 1.0):
        tail = knot + Vector((swing * 0.025, 0.02, -0.06))
        c.cloth.box((0.035, 0.008, 0.07), (knot + tail) / 2.0, color, head, rotation=Quaternion(FRONT, swing * 0.3), bevel=0.003)


def _station_person(
    look: Look,
    torso: pb.Profile,
    *,
    coat: str,
    hem: float,
    headwear: str,
    headwear_color: str = "",
    apron: str | None = None,
    skirt: str | None = None,
    belt: str | None = None,
    felt: bool = False,
    scarf_side: float = 1.0,
) -> bpy.types.Object:
    c = Character(look, torso, hem_follow=0.4, prefix="persona")
    c.add_bones(c.scarf_bones(scarf_side, 0.14))
    if skirt is not None:
        _skirt(c, 0.98, 0.42, skirt)
    if coat == "largo":
        _long_coat(c, hem, belt)
    else:
        _quilted_jacket(c, hem)
    if apron is not None:
        _apron(c, apron)
    c.build_legs(kneepads=False)
    c.build_boots(felt=felt)
    c.build_sleeves(quilted=coat != "largo")
    c.build_hands()
    c.build_head()
    c.build_scarf(scarf_side, 0.14)
    if headwear == "gorra":
        _hair(c, look.hair, crown=False)
        _flat_cap(c, headwear_color)
    elif headwear == "panuelo":
        _headscarf(c, headwear_color)
    else:
        _hair(c, look.hair, crown=True, bun=headwear == "mono")
    return c.finish(f"cara_{look.name}")


def build_relojero() -> bpy.types.Object:
    """Lev Abrámovich, el relojero: abrigo largo gris con cinturón, gorra de paño
    y gafas redondas (dibujadas en la cara), bigote cano."""
    return _station_person(
        RELOJERO, _man_torso(0.006), coat="largo", hem=0.56, headwear="gorra",
        headwear_color="#34322E", belt=LEATHER, scarf_side=-1.0,
    )


def build_vendedora() -> bpy.types.Object:
    """Zina, la de la sopa: chaqueta acolchada, falda, delantal y pañuelo, y botas
    de fieltro de estar de pie todo el día."""
    return _station_person(
        VENDEDORA, _woman_torso(), coat="acolchada", hem=0.9, headwear="panuelo",
        headwear_color="#7A5A6E", apron="#C8B89A", skirt="#3E3530", felt=True,
    )


def build_vecina() -> bpy.types.Object:
    """Nadia, la de la lavandería: abrigo largo de paño y el pelo recogido."""
    return _station_person(
        VECINA, _woman_torso(), coat="largo", hem=0.5, headwear="mono", felt=True, scarf_side=-1.0,
    )


def build_chatarrero() -> bpy.types.Object:
    """Gleb, el chatarrero: chaqueta acolchada sucia y gorra; barba de días."""
    return _station_person(
        CHATARRERO, _man_torso(0.012), coat="acolchada", hem=0.74, headwear="gorra",
        headwear_color="#4A4232", belt=None,
    )


def models() -> dict:
    return {
        "jugador_chico": build_chico,
        "jugador_chica": build_chica,
        "manos_chico": lambda: build_first_person_hands(CHICO),
        "manos_chica": lambda: build_first_person_hands(CHICA),
        "persona_relojero": build_relojero,
        "persona_vendedora": build_vendedora,
        "persona_vecina": build_vecina,
        "persona_chatarrero": build_chatarrero,
    }
