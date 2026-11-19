"""Animaciones de los protagonistas, generadas por código.

Cada animación es una función del tiempo (de 0 a 1) que devuelve una pose
(``personaje_bpy.Pose``). Las piernas se resuelven con cinemática inversa para
que los pies no patinen: el pie apoyado retrocede en línea recta y a velocidad
constante, así que basta con que el juego reproduzca el ciclo a la velocidad a
la que anda el personaje (``WALK_DISTANCE`` metros por ciclo).

El movimiento se guarda suave; el aspecto "a saltos" de dibujo animado lo pone
Godot al reproducirlo a pocos fotogramas por segundo (ver PlayerAvatar).
"""

from __future__ import annotations

import math

from mathutils import Quaternion, Vector

import personaje_bpy as pb
from personaje_bpy import FRONT, LEFT, UP, Pose, lerp, smooth

SIDES = ((1.0, "Left"), (-1.0, "Right"))

# Metros que avanza el personaje en un ciclo de caminar (dos pasos).
WALK_DISTANCE = 0.9
# Parte del ciclo que cada pie pasa apoyado.
STANCE = 0.6
# Agachado (F3-01): lo que bajan las caderas y los metros de cada ciclo.
CROUCH_DROP = 0.42
CROUCH_DISTANCE = 0.7
# Corriendo: los metros de cada ciclo y la parte que cada pie pasa en el suelo
# (el resto del ciclo, los dos pies van en el aire un momento).
RUN_DISTANCE = 2.4
RUN_STANCE = 0.3


def _wave(t: float, shift: float = 0.0) -> float:
    return math.sin(2.0 * math.pi * (t + shift))


# --------------------------------------------------------------------------
# Cuerpo
# --------------------------------------------------------------------------


def _arms_down(pose: Pose, swing: float, bend: float = 12.0) -> None:
    """Brazos caídos junto al cuerpo. ``swing`` > 0 adelanta el izquierdo."""
    for sign, side in SIDES:
        amount = swing * sign
        pose.turn(f"{side}UpperArm", FRONT, -24.0 * sign)
        pose.turn(f"{side}UpperArm", LEFT, -amount)
        pose.turn(f"{side}LowerArm", LEFT, -bend - max(0.0, amount) * 0.8)


def _arms_carrying(pose: Pose, character, lift: float, chest: Vector | None = None) -> None:
    """Brazos por delante, sujetando algo entre las manos a la altura del vientre.

    Las manos van respecto al pecho en reposo; con ``chest`` (el pecho ya
    colocado), respecto a él: agachado o corriendo, el pecho baja y se adelanta.
    """
    j = character.j
    base = Vector((0.0, 0.0, j.chest.z)) if chest is None else chest
    for sign, side in SIDES:
        target = Vector((sign * 0.15, base.y - 0.265, base.z - 0.045 + lift))
        pose.reach(f"{side}UpperArm", f"{side}LowerArm", target, Vector((sign * 0.55, 0.45, -1.0)))
        frame = character.hand_frames[side]
        pose.hold(f"{side}Hand", pb.aim(frame.y, frame.z, FRONT + LEFT * -0.2 * sign + UP * 0.25, LEFT * sign))


def _arms_ready(pose: Pose, forward: float, bend: float, swing: float = 0.0) -> None:
    """Los dos brazos a la vez: adelantados ``forward`` grados respecto al
    tronco, con los codos doblados ``bend`` y un vaivén ``swing`` (> 0 adelanta
    el izquierdo)."""
    for sign, side in SIDES:
        pose.turn(f"{side}UpperArm", FRONT, -20.0 * sign)
        pose.turn(f"{side}UpperArm", LEFT, -forward - swing * sign)
        pose.turn(f"{side}LowerArm", LEFT, -bend)


def _crouch_body(pose: Pose, bob: float = 0.0) -> None:
    """Agachado: las caderas abajo y algo atrás, el cuerpo echado hacia delante
    y la cabeza levantada para mirar al frente."""
    pose.move("Hips", Vector((0.0, 0.07, -CROUCH_DROP + bob)))
    pose.turn("Hips", LEFT, 20.0)
    pose.turn("Spine", LEFT, 9.0)
    pose.turn("Chest", LEFT, 4.0)
    pose.turn("Neck", LEFT, -12.0)
    pose.turn("Head", LEFT, -24.0)


def _spread(targets: dict[str, tuple[Vector, float]], amount: float) -> dict[str, tuple[Vector, float]]:
    """Separa los pies ``amount`` metros más hacia fuera."""
    sides = dict((side, sign) for sign, side in SIDES)
    return {side: (offset + Vector((amount * sides[side], 0.0, 0.0)), pitch) for side, (offset, pitch) in targets.items()}


def _slouch(pose: Pose, amount: float = 1.0) -> None:
    """Postura de base: flacos, cargados de hombros y con la cabeza adelantada."""
    pose.turn("Spine", LEFT, 4.0 * amount)
    pose.turn("Chest", LEFT, 7.0 * amount)
    pose.turn("Neck", LEFT, 9.0 * amount)
    pose.turn("Head", LEFT, -14.0 * amount)
    for sign, side in SIDES:
        pose.turn(f"{side}Shoulder", UP, -9.0 * sign * amount)
        pose.turn(f"{side}Shoulder", FRONT, -3.0 * sign * amount)


def _plant_feet(pose: Pose, character, targets: dict[str, tuple[Vector, float]] | None = None) -> None:
    """Lleva cada tobillo a su sitio (por defecto, el de reposo) y nivela el pie."""
    j = character.j
    for sign, side in SIDES:
        offset, pitch = targets[side] if targets else (Vector(), 0.0)
        ankle = Vector((j.ankle.x * sign, j.ankle.y, j.ankle.z)) + offset
        pose.reach(f"{side}UpperLeg", f"{side}LowerLeg", ankle, FRONT + LEFT * 0.12 * sign)
        pose.hold(f"{side}Foot", Quaternion(LEFT, math.radians(pitch)))


def _foot_path(phase: float, distance: float = WALK_DISTANCE, step: float = 1.0) -> tuple[Vector, float]:
    """Dónde está el tobillo en el ciclo de caminar y cuánto cabecea el pie.

    Devuelve el desplazamiento respecto al reposo y el cabeceo en grados
    (positivo: puntera hacia abajo). ``distance`` son los metros de cada ciclo
    y ``step``, lo que se levanta el pie (1, andando).
    """
    reach = distance * STANCE / 2.0
    if phase < STANCE:
        u = phase / STANCE
        y = -reach + 2.0 * reach * u
        heel_strike = -14.0 * (1.0 - smooth(u / 0.18))
        push_off = 26.0 * smooth((u - 0.7) / 0.3)
        pitch = heel_strike + push_off
        return Vector((0.0, y, 0.115 * math.sin(math.radians(push_off)))), pitch
    u = (phase - STANCE) / (1.0 - STANCE)
    y = reach - 2.0 * reach * smooth(u)
    lift = 0.05 * (1.0 - u) + 0.055 * math.sin(math.pi * u)
    if step != 1.0:
        lift *= step
    return Vector((0.0, y, lift)), lerp(26.0, -14.0, smooth(u * 1.15))


# Corriendo, el pie que vuela: [parte del vuelo, adelante (fracción de lo que
# recorre apoyado), altura, cabeceo]. Sale de atrás de puntillas, el talón sube
# hacia el culo, la rodilla tira hacia delante y cae casi plano.
_RUN_SWING = (
    (0.0, 1.0, 0.1, 32.0),
    (0.3, 1.15, 0.34, 70.0),
    (0.62, -0.3, 0.28, 8.0),
    (1.0, -1.0, 0.0, -6.0),
)


def _run_foot(phase: float) -> tuple[Vector, float]:
    """Como ``_foot_path``, corriendo."""
    reach = RUN_DISTANCE * RUN_STANCE / 2.0
    if phase < RUN_STANCE:
        u = phase / RUN_STANCE
        push = smooth((u - 0.5) / 0.5)
        return Vector((0.0, -reach + 2.0 * reach * u, 0.1 * push)), lerp(-6.0, 32.0, push)
    u = (phase - RUN_STANCE) / (1.0 - RUN_STANCE)
    for (u0, y0, z0, p0), (u1, y1, z1, p1) in zip(_RUN_SWING, _RUN_SWING[1:]):
        if u <= u1:
            k = smooth((u - u0) / (u1 - u0))
            return Vector((0.0, reach * lerp(y0, y1, k), lerp(z0, z1, k))), lerp(p0, p1, k)
    return Vector((0.0, -reach, 0.0)), -6.0


def _idle(character, t: float, carrying: bool) -> Pose:
    pose = Pose(character_rig(character))
    breath, sway = _wave(t * 2.0), _wave(t)
    _slouch(pose, 0.6 if carrying else 1.0)
    pose.move("Hips", Vector((0.012 + 0.006 * sway, 0.0, -0.014 - 0.002 * breath)))
    pose.turn("Hips", FRONT, 2.2 + 1.2 * sway)
    pose.turn("Spine", FRONT, -2.0 - 1.0 * sway)
    pose.turn("Chest", LEFT, -1.6 * breath - (6.0 if carrying else 0.0))
    pose.turn("Neck", LEFT, 0.8 * breath + (3.0 if carrying else 0.0))
    pose.turn("Head", UP, 2.0 * _wave(t, 0.2))
    for sign, side in SIDES:
        pose.turn(f"{side}Shoulder", FRONT, 1.6 * breath * sign)
    if carrying:
        _arms_carrying(pose, character, 0.004 * breath)
    else:
        _arms_down(pose, 2.0 * _wave(t, 0.1))
    _plant_feet(pose, character)
    return pose


def _walk(character, t: float, carrying: bool) -> Pose:
    pose = Pose(character_rig(character))
    stride = math.cos(2.0 * math.pi * t)
    lift = math.cos(4.0 * math.pi * (t - 0.3))
    side_shift = math.cos(2.0 * math.pi * (t - 0.3))
    _slouch(pose, 0.5 if carrying else 0.9)
    pose.move("Hips", Vector((0.013 * side_shift, 0.0, -0.05 + 0.012 * lift)))
    pose.turn("Hips", UP, -6.0 * stride)
    pose.turn("Hips", FRONT, 2.5 * side_shift)
    pose.turn("Spine", LEFT, 2.0 if not carrying else -3.0)
    pose.turn("Spine", UP, 3.5 * stride)
    pose.turn("Spine", FRONT, -2.0 * side_shift)
    pose.turn("Chest", UP, (5.0 if not carrying else 2.0) * stride)
    pose.turn("Neck", UP, -2.5 * stride)
    pose.turn("Head", LEFT, 1.2 * lift)
    if carrying:
        _arms_carrying(pose, character, 0.006 * lift)
    else:
        _arms_down(pose, -15.0 * stride, 14.0)
    _plant_feet(
        pose, character, {"Left": _foot_path(t % 1.0), "Right": _foot_path((t + 0.5) % 1.0)}
    )
    return pose


def _crouch(character, t: float, carrying: bool) -> Pose:
    """Agachado y quieto: un pie adelante y el otro atrás, de puntillas."""
    pose = Pose(character_rig(character))
    breath, sway = _wave(t * 2.0), _wave(t)
    _slouch(pose, 0.5)
    _crouch_body(pose, -0.004 * breath)
    pose.move("Hips", Vector((0.008 * sway, 0.0, 0.0)))
    pose.turn("Chest", LEFT, -1.4 * breath)
    pose.turn("Head", UP, 3.0 * _wave(t, 0.2))
    if carrying:
        _arms_carrying(pose, character, 0.004 * breath, pose.head("Chest"))
    else:
        _arms_ready(pose, -16.0, 42.0, 1.5 * sway)
    feet = {"Left": (Vector((0.0, -0.1, 0.0)), 0.0), "Right": (Vector((0.0, 0.16, 0.05)), 30.0)}
    _plant_feet(pose, character, _spread(feet, 0.03))
    return pose


def _crouch_walk(character, t: float, carrying: bool) -> Pose:
    """Andando agachado: pasos cortos, sin levantar los pies, y el cuerpo bajo."""
    pose = Pose(character_rig(character))
    stride = math.cos(2.0 * math.pi * t)
    lift = math.cos(4.0 * math.pi * (t - 0.3))
    side_shift = math.cos(2.0 * math.pi * (t - 0.3))
    _slouch(pose, 0.5)
    _crouch_body(pose, 0.012 * lift)
    pose.move("Hips", Vector((0.016 * side_shift, 0.0, 0.0)))
    pose.turn("Hips", UP, -5.0 * stride)
    pose.turn("Hips", FRONT, 2.0 * side_shift)
    pose.turn("Spine", UP, 3.0 * stride)
    pose.turn("Chest", UP, 3.0 * stride)
    if carrying:
        _arms_carrying(pose, character, 0.005 * lift, pose.head("Chest"))
    else:
        _arms_ready(pose, -12.0, 40.0, -10.0 * stride)
    feet = {
        "Left": _foot_path(t % 1.0, CROUCH_DISTANCE, 0.7),
        "Right": _foot_path((t + 0.5) % 1.0, CROUCH_DISTANCE, 0.7),
    }
    _plant_feet(pose, character, _spread(feet, 0.03))
    return pose


def _run(character, t: float, carrying: bool) -> Pose:
    """Corriendo: echado hacia delante, con los brazos doblados que acompañan y
    un momento en el aire entre paso y paso."""
    pose = Pose(character_rig(character))
    stride = math.cos(2.0 * math.pi * t)
    # Lo más bajo, con cada pie a mitad de su apoyo.
    bounce = math.cos(4.0 * math.pi * (t - RUN_STANCE / 2.0))
    _slouch(pose, 0.4)
    pose.move("Hips", Vector((0.0, 0.0, -0.075 - 0.03 * bounce)))
    pose.turn("Hips", LEFT, 13.0)
    pose.turn("Hips", UP, -9.0 * stride)
    pose.turn("Spine", LEFT, 6.0)
    pose.turn("Spine", UP, 5.0 * stride)
    pose.turn("Chest", UP, 7.0 * stride)
    pose.turn("Neck", LEFT, -7.0)
    pose.turn("Head", LEFT, -11.0)
    if carrying:
        _arms_carrying(pose, character, 0.012 * bounce, pose.head("Chest"))
    else:
        _arms_ready(pose, 8.0, 80.0, -38.0 * stride)
    _plant_feet(pose, character, {"Left": _run_foot(t % 1.0), "Right": _run_foot((t + 0.5) % 1.0)})
    return pose


_RIGS: dict[int, pb.Rig] = {}


def character_rig(character) -> pb.Rig:
    return _RIGS[id(character)]


def body_animations(rig: pb.Rig, character) -> None:
    _RIGS[id(character)] = rig
    moving = ["Hips"]
    pb.bake_action(rig, "reposo-loop", 4.0, lambda t: _idle(character, t, False), moving=moving)
    pb.bake_action(rig, "caminar-loop", 1.0, lambda t: _walk(character, t, False), moving=moving)
    pb.bake_action(rig, "reposo_cargando-loop", 4.0, lambda t: _idle(character, t, True), moving=moving)
    pb.bake_action(rig, "caminar_cargando-loop", 1.0, lambda t: _walk(character, t, True), moving=moving)
    pb.bake_action(rig, "agachado-loop", 4.0, lambda t: _crouch(character, t, False), moving=moving)
    pb.bake_action(rig, "caminar_agachado-loop", 1.0, lambda t: _crouch_walk(character, t, False), moving=moving)
    pb.bake_action(rig, "correr-loop", 1.0, lambda t: _run(character, t, False), moving=moving)
    pb.bake_action(rig, "agachado_cargando-loop", 4.0, lambda t: _crouch(character, t, True), moving=moving)
    pb.bake_action(rig, "caminar_agachado_cargando-loop", 1.0, lambda t: _crouch_walk(character, t, True), moving=moving)
    pb.bake_action(rig, "correr_cargando-loop", 1.0, lambda t: _run(character, t, True), moving=moving)
    del _RIGS[id(character)]


# --------------------------------------------------------------------------
# Manos de primera persona
# --------------------------------------------------------------------------

HAND_SIDES = ((-1.0, "Left"), (1.0, "Right"))
FINGERS = ("Index", "Middle", "Ring", "Little")


def _place_arm(pose: Pose, side: str, elbow: Vector, wrist: Vector, thumb: Vector) -> None:
    """Coloca un antebrazo: el codo, hacia dónde apunta y hacia dónde mira el pulgar."""
    bone = f"{side}LowerArm"
    pose.move(bone, Vector(elbow) - pose.rig.head[bone])
    pose.point_at(bone, Vector(wrist) - Vector(elbow), thumb, UP)


def _curl(pose: Pose, sign: float, side: str, amount: float, thumb: float | None = None) -> None:
    """Cierra los dedos ``amount`` grados por falange (negativo los abre)."""
    for finger in FINGERS:
        for part, share in (("Proximal", 1.0), ("Intermediate", 1.1), ("Distal", 0.7)):
            pose.turn(f"{side}{finger}{part}", UP, sign * amount * share)
    thumb = amount * 0.6 if thumb is None else thumb
    for part, share in (("Metacarpal", 0.5), ("Proximal", 0.6), ("Distal", 0.8)):
        pose.turn(f"{side}Thumb{part}", -FRONT, -sign * thumb * share)


def _hands_low(rig: pb.Rig, t: float) -> Pose:
    """Manos caídas, fuera de la vista."""
    pose = Pose(rig)
    sway = _wave(t)
    for sign, side in HAND_SIDES:
        elbow = Vector((sign * 0.27, -0.12, -0.50 + 0.004 * sway))
        wrist = elbow + Vector((-sign * 0.05, 0.2, -0.22))
        _place_arm(pose, side, elbow, wrist, UP + LEFT * -0.3 * sign)
        _curl(pose, sign, side, 22.0)
    return pose


def _hands_holding(rig: pb.Rig, t: float) -> Pose:
    """Sujetando algo entre las dos manos, delante del pecho."""
    pose = Pose(rig)
    sway = _wave(t)
    for sign, side in HAND_SIDES:
        elbow = Vector((sign * 0.335, 0.31, -0.63 + 0.003 * sway))
        wrist = Vector((sign * 0.225, 0.47, -0.33 + 0.004 * sway))
        _place_arm(pose, side, elbow, wrist, UP + LEFT * -0.2 * sign)
        pose.turn(f"{side}Hand", UP, -sign * 14.0)
        _curl(pose, sign, side, 10.0, thumb=-10.0)
    return pose


def _hands_reaching(rig: pb.Rig, t: float) -> Pose:
    """La mano derecha sale a tocar o coger algo y vuelve."""
    pose = _hands_low(rig, 0.0)
    out = math.sin(math.pi * smooth(t)) ** 0.8
    low_elbow = Vector((0.27, -0.12, -0.50))
    low_wrist = low_elbow + Vector((-0.05, 0.2, -0.22))
    elbow = low_elbow.lerp(Vector((0.24, 0.12, -0.36)), out)
    wrist = low_wrist.lerp(Vector((0.12, 0.42, -0.17)), out)
    pose.offset.pop("RightLowerArm", None)
    pose.rotation.pop("RightLowerArm", None)
    _place_arm(pose, "Right", elbow, wrist, (UP + LEFT * -0.3).lerp(UP * 0.4 + LEFT * -1.0, out))
    for name in list(pose.rotation):
        if name.startswith("Right") and name not in ("RightLowerArm",):
            del pose.rotation[name]
    _curl(pose, 1.0, "Right", lerp(22.0, 4.0, out), thumb=lerp(13.0, -10.0, out))
    return pose


def hand_animations(rig: pb.Rig) -> None:
    moving = ["LeftLowerArm", "RightLowerArm"]
    pb.bake_action(rig, "reposo-loop", 4.0, lambda t: _hands_low(rig, t), moving=moving)
    pb.bake_action(rig, "sostener-loop", 4.0, lambda t: _hands_holding(rig, t), moving=moving)
    pb.bake_action(rig, "alcanzar", 0.6, lambda t: _hands_reaching(rig, t), moving=moving)
