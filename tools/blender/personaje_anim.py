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


def _arms_carrying(pose: Pose, character, lift: float) -> None:
    """Brazos por delante, sujetando algo entre las manos a la altura del vientre."""
    j = character.j
    for sign, side in SIDES:
        target = Vector((sign * 0.15, -0.265, j.chest.z - 0.045 + lift))
        pose.reach(f"{side}UpperArm", f"{side}LowerArm", target, Vector((sign * 0.55, 0.45, -1.0)))
        frame = character.hand_frames[side]
        pose.hold(f"{side}Hand", pb.aim(frame.y, frame.z, FRONT + LEFT * -0.2 * sign + UP * 0.25, LEFT * sign))


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


def _foot_path(phase: float) -> tuple[Vector, float]:
    """Dónde está el tobillo en el ciclo de caminar y cuánto cabecea el pie.

    Devuelve el desplazamiento respecto al reposo y el cabeceo en grados
    (positivo: puntera hacia abajo).
    """
    reach = WALK_DISTANCE * STANCE / 2.0
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
    return Vector((0.0, y, lift)), lerp(26.0, -14.0, smooth(u * 1.15))


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


# Agachado (F3-01): las caderas bajan, el cuerpo se inclina y la cabeza sigue mirando al
# frente. Metros por ciclo al andar agachado y al correr (PlayerAvatar los usa igual).
CROUCH_DISTANCE = 0.75
CROUCH_DROP = 0.40
RUN_DISTANCE = 2.6
# Parte del ciclo que cada pie pasa apoyado al correr: menos de la mitad, así que hay vuelo.
RUN_STANCE = 0.34


def _stride_path(phase: float, distance: float, stance: float, lift: float, kick: float) -> tuple[Vector, float]:
    """Como ``_foot_path``, para cualquier paso: ``distance`` metros por ciclo, la parte
    apoyada ``stance``, lo que sube el pie al pasar ``lift`` y lo que se echa atrás el
    talón al despegar ``kick`` (correr)."""
    reach = distance * stance / 2.0
    if phase < stance:
        u = phase / stance
        y = -reach + 2.0 * reach * u
        pitch = -10.0 * (1.0 - smooth(u / 0.2)) + 24.0 * smooth((u - 0.7) / 0.3)
        return Vector((0.0, y, 0.0)), pitch
    u = (phase - stance) / (1.0 - stance)
    y = reach - 2.0 * reach * smooth(u)
    # Al correr, el talón sube hacia atrás al empezar el vuelo.
    back = kick * math.sin(math.pi * min(1.0, u * 1.6)) * (1.0 - u)
    up = lift * math.sin(math.pi * u) + back * 0.9
    return Vector((0.0, y + back, up)), lerp(30.0, -10.0, smooth(u))


def _crouch_body(pose: Pose, carrying: bool, breath: float, bob: float = 0.0) -> None:
    """El cuerpo agachado: caderas abajo y atrás, la espalda inclinada y la cabeza al frente."""
    pose.move("Hips", Vector((0.0, 0.07, -CROUCH_DROP + 0.01 * bob - 0.004 * breath)))
    pose.turn("Hips", LEFT, 24.0)
    pose.turn("Spine", LEFT, 11.0 + (0.0 if carrying else 2.0))
    pose.turn("Chest", LEFT, 7.0 - 1.2 * breath - (6.0 if carrying else 0.0))
    pose.turn("Neck", LEFT, -16.0 + (3.0 if carrying else 0.0))
    pose.turn("Head", LEFT, -24.0)
    for sign, side in SIDES:
        pose.turn(f"{side}Shoulder", UP, -6.0 * sign)


def _crouch_arms(pose: Pose, character, carrying: bool, swing: float) -> None:
    """Agachado, las manos van por delante, cerca de las rodillas (o sujetando lo que se lleva)."""
    if carrying:
        chest = pose.head("Chest")
        for sign, side in SIDES:
            target = chest + Vector((sign * 0.15, -0.3, -0.06))
            pose.reach(f"{side}UpperArm", f"{side}LowerArm", target, Vector((sign * 0.55, 0.45, -1.0)))
            frame = character.hand_frames[side]
            pose.hold(f"{side}Hand", pb.aim(frame.y, frame.z, FRONT + UP * 0.25, LEFT * sign))
        return
    for sign, side in SIDES:
        amount = swing * sign
        pose.turn(f"{side}UpperArm", FRONT, -20.0 * sign)
        pose.turn(f"{side}UpperArm", LEFT, 28.0 - amount)
        pose.turn(f"{side}LowerArm", LEFT, -38.0 - max(0.0, amount) * 0.6)


def _crouch(character, t: float, carrying: bool) -> Pose:
    pose = Pose(character_rig(character))
    breath = _wave(t * 2.0)
    _crouch_body(pose, carrying, breath)
    pose.turn("Head", UP, 3.0 * _wave(t, 0.2))
    _crouch_arms(pose, character, carrying, 2.0 * _wave(t, 0.1))
    # Un pie algo adelantado y separados: listo para moverse.
    _plant_feet(
        pose,
        character,
        {"Left": (Vector((0.03, -0.09, 0.0)), 0.0), "Right": (Vector((-0.03, 0.08, 0.0)), 6.0)},
    )
    return pose


def _crouch_walk(character, t: float, carrying: bool) -> Pose:
    pose = Pose(character_rig(character))
    stride = math.cos(2.0 * math.pi * t)
    bob = math.cos(4.0 * math.pi * (t - 0.3))
    _crouch_body(pose, carrying, 0.0, bob)
    pose.turn("Hips", UP, -5.0 * stride)
    pose.turn("Spine", UP, 3.0 * stride)
    pose.turn("Chest", UP, 3.0 * stride)
    pose.turn("Neck", UP, -2.0 * stride)
    _crouch_arms(pose, character, carrying, -10.0 * stride)
    left = _stride_path(t % 1.0, CROUCH_DISTANCE, 0.62, 0.06, 0.0)
    right = _stride_path((t + 0.5) % 1.0, CROUCH_DISTANCE, 0.62, 0.06, 0.0)
    _plant_feet(
        pose,
        character,
        {
            "Left": (left[0] + Vector((0.03, 0.0, 0.0)), left[1]),
            "Right": (right[0] + Vector((-0.03, 0.0, 0.0)), right[1]),
        },
    )
    return pose


def _run(character, t: float, carrying: bool) -> Pose:
    pose = Pose(character_rig(character))
    stride = math.cos(2.0 * math.pi * t)
    # Dos botes por ciclo: abajo al apoyar, arriba en el vuelo.
    bounce = math.cos(4.0 * math.pi * (t - RUN_STANCE / 2.0))
    side_shift = math.cos(2.0 * math.pi * (t - 0.2))
    _slouch(pose, 0.4)
    pose.move("Hips", Vector((0.01 * side_shift, 0.0, -0.075 - 0.03 * bounce)))
    pose.turn("Hips", LEFT, 8.0)
    pose.turn("Hips", UP, -9.0 * stride)
    pose.turn("Spine", LEFT, 6.0)
    pose.turn("Spine", UP, 5.0 * stride)
    pose.turn("Chest", UP, 7.0 * stride)
    pose.turn("Neck", LEFT, -5.0)
    pose.turn("Neck", UP, -4.0 * stride)
    pose.turn("Head", LEFT, -6.0 + 1.5 * bounce)
    if carrying:
        _arms_carrying(pose, character, 0.015 * bounce)
    else:
        # Los brazos doblados en ángulo recto, a contratiempo de las piernas.
        for sign, side in SIDES:
            amount = -38.0 * stride * sign
            pose.turn(f"{side}UpperArm", FRONT, -16.0 * sign)
            pose.turn(f"{side}UpperArm", LEFT, 8.0 - amount)
            pose.turn(f"{side}LowerArm", LEFT, -78.0 - max(0.0, amount) * 0.3)
    left = _stride_path(t % 1.0, RUN_DISTANCE, RUN_STANCE, 0.12, 0.28)
    right = _stride_path((t + 0.5) % 1.0, RUN_DISTANCE, RUN_STANCE, 0.12, 0.28)
    _plant_feet(pose, character, {"Left": left, "Right": right})
    return pose


# Trepar (F3-06): por una escalera de pates o una cuerda. Cada ciclo sube dos peldaños
# (CLIMB_DISTANCE metros); la mano agarrada y el pie apoyado bajan respecto al cuerpo
# mientras sube y luego se adelantan al siguiente peldaño, como los pies al andar.
CLIMB_DISTANCE = 0.56
CLIMB_GRIP = 0.72


def _climb_path(phase: float, top: float) -> float:
    """La altura de una mano o de un pie en el ciclo de trepar: agarrado, baja con el
    cuerpo que sube; suelto, sube al peldaño siguiente."""
    if phase < CLIMB_GRIP:
        return top - CLIMB_DISTANCE * phase
    u = (phase - CLIMB_GRIP) / (1.0 - CLIMB_GRIP)
    return top - CLIMB_DISTANCE * CLIMB_GRIP * (1.0 - smooth(u))


def _climb(character, t: float) -> Pose:
    pose = Pose(character_rig(character))
    j = character.j
    _slouch(pose, 0.3)
    # Pegado a la escalera, la cabeza un poco atrás para mirar arriba.
    pose.move("Hips", Vector((0.0, -0.06, -0.02)))
    pose.turn("Spine", LEFT, 6.0)
    pose.turn("Head", LEFT, 14.0)
    for sign, side in SIDES:
        # Mano izquierda con pie derecho, y al revés (medio ciclo después).
        phase = (t + (0.0 if side == "Left" else 0.5)) % 1.0
        top = j.head_top.z + 0.18
        hand = Vector((sign * 0.17, -0.3, _climb_path(phase, top)))
        pose.reach(f"{side}UpperArm", f"{side}LowerArm", hand, Vector((sign * 0.8, 0.4, -0.6)))
        frame = character.hand_frames[side]
        pose.hold(f"{side}Hand", pb.aim(frame.y, frame.z, UP + FRONT * 0.6, -FRONT))
    feet = {}
    for sign, side in SIDES:
        phase = (t + (0.5 if side == "Left" else 0.0)) % 1.0
        lift = _climb_path(phase, 0.42)
        feet[side] = (Vector((0.0, -0.12, lift)), -10.0)
    _plant_feet(pose, character, feet)
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
    pb.bake_action(rig, "agachado_cargando-loop", 4.0, lambda t: _crouch(character, t, True), moving=moving)
    pb.bake_action(rig, "agachado_andar-loop", 1.0, lambda t: _crouch_walk(character, t, False), moving=moving)
    pb.bake_action(
        rig, "agachado_andar_cargando-loop", 1.0, lambda t: _crouch_walk(character, t, True), moving=moving
    )
    pb.bake_action(rig, "correr-loop", 0.6, lambda t: _run(character, t, False), moving=moving)
    pb.bake_action(rig, "correr_cargando-loop", 0.6, lambda t: _run(character, t, True), moving=moving)
    pb.bake_action(rig, "trepar-loop", 1.0, lambda t: _climb(character, t), moving=moving)
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
