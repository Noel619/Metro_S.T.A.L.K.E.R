"""Animaciones de los perros de la Jauría (F3-10), generadas por código.

Como las de los protagonistas (``personaje_anim.py``): cada animación es una función del
tiempo (de 0 a 1) que devuelve una pose, y las patas se resuelven con cinemática inversa
para que no patinen. El aspecto "a saltos" lo pone Godot al reproducirlas a pocos
fotogramas por segundo; la cabeza que sigue lo que percibe y el hocico al suelo al
olfatear también son de Godot (``DogLook``), encima de la animación.

Los pasos: al andar, cada pata a su tiempo (atrás izquierda, delante izquierda, atrás
derecha, delante derecha); al trotar, en diagonal; al galopar, las de atrás casi juntas y
luego las de delante, con el lomo que se encoge y se estira. ``*_DISTANCE`` son los metros
que avanza cada ciclo (el juego los usa para no patinar).
"""

from __future__ import annotations

import math

from mathutils import Quaternion, Vector

import personaje_bpy as pb
from personaje_bpy import FRONT, LEFT, UP, Pose, lerp, smooth

SIDES = ((1.0, "Left"), (-1.0, "Right"))
WALK_DISTANCE = 1.1
STALK_DISTANCE = 0.8
TROT_DISTANCE = 1.6
GALLOP_DISTANCE = 2.9
BACK = Vector((0.0, 1.0, 0.0))


def _wave(t: float, shift: float = 0.0) -> float:
    return math.sin(2.0 * math.pi * (t + shift))


def _mx(v: Vector, sign: float) -> Vector:
    return Vector((v.x * sign, v.y, v.z))


def _foot_path(phase: float, distance: float, stance: float, lift: float) -> tuple[Vector, float]:
    """Dónde está la pata en el ciclo, respecto a su sitio de pie, y cuánto se dobla
    (grados). Apoyada, va de delante (-Y) a atrás a velocidad constante; en el aire, vuelve
    levantándose."""
    reach = distance * stance / 2.0
    if phase < stance:
        u = phase / stance
        return Vector((0.0, -reach + 2.0 * reach * u, 0.0)), 25.0 * smooth((u - 0.75) / 0.25)
    u = (phase - stance) / (1.0 - stance)
    y = reach - 2.0 * reach * smooth(u)
    return Vector((0.0, y, lift * math.sin(math.pi * u))), lerp(60.0, 0.0, smooth(u))


class DogPoser:
    """Las poses del perro sobre su esqueleto (``j``: las articulaciones de pie)."""

    def __init__(self, rig: pb.Rig, j) -> None:
        self.rig = rig
        self.j = j

    def pose(self) -> Pose:
        return Pose(self.rig)

    # -- el cuerpo ----------------------------------------------------------

    def body(self, pose: Pose, drop: float = 0.0, pitch: float = 0.0, bob: float = 0.0, sway: float = 0.0) -> None:
        """Caderas abajo ``drop`` (y un bote ``bob``), el lomo inclinado ``pitch`` grados
        (positivo: el pecho más bajo) y un vaivén de lado ``sway``."""
        pose.move("Hips", Vector((sway * 0.01, 0.0, -drop + bob)))
        pose.turn("Hips", LEFT, pitch * 0.5)
        pose.turn("Hips", FRONT, sway)
        pose.turn("Spine", FRONT, -sway * 0.6)

    def head(self, pose: Pose, lift: float = 0.0, turn: float = 0.0, jaw: float = 0.0, ears: float = 0.0) -> None:
        """La cabeza ``lift`` grados más alta, girada ``turn``; la boca abierta ``jaw``
        grados y las orejas ``ears`` (positivo: tiesas, negativo: gachas)."""
        pose.turn("Neck", LEFT, -lift * 0.6)
        pose.turn("Head", LEFT, -lift * 0.4)
        pose.turn("Neck", UP, turn * 0.6)
        pose.turn("Head", UP, turn * 0.4)
        pose.turn("Jaw", LEFT, jaw)
        for sign, side in SIDES:
            # Las orejas miran arriba: girar hacia delante (+X) las pone tiesas.
            pose.turn(f"{side}Ear", LEFT, ears)
            pose.turn(f"{side}Ear", FRONT, ears * 0.3 * sign)

    def tail(self, pose: Pose, lift: float, wag: float = 0.0) -> None:
        """La cola ``lift`` grados más alta y moviéndose ``wag`` grados de lado."""
        for index, bone in enumerate(("Tail1", "Tail2", "Tail3")):
            # La cola sale hacia atrás (+Y): girar sobre +X la sube.
            pose.turn(bone, LEFT, lift * (0.6 - index * 0.15))
            pose.turn(bone, UP, wag * (0.5 + index * 0.35))

    # -- las patas ----------------------------------------------------------

    def front_leg(self, pose: Pose, sign: float, side: str, offset: Vector, bend: float = 0.0) -> None:
        """La pata de delante con la muñeca en su sitio de pie más ``offset``; ``bend``
        dobla la muñeca (la pata en el aire)."""
        wrist = _mx(self.j.wrist, sign) + offset
        pose.reach(f"{side}UpperArm", f"{side}ForeArm", wrist, BACK + UP * 0.2)
        down = Quaternion(LEFT, math.radians(bend)) @ (-UP + FRONT * 0.18)
        pose.point_at(f"{side}Hand", down)

    def hind_leg(self, pose: Pose, sign: float, side: str, offset: Vector, bend: float = 0.0) -> None:
        """La pata de atrás con el corvejón en su sitio de pie más ``offset``."""
        hock = _mx(self.j.hock, sign) + offset
        pose.reach(f"{side}UpperLeg", f"{side}LowerLeg", hock, FRONT + UP * 0.1)
        down = Quaternion(LEFT, math.radians(bend)) @ (-UP + FRONT * 0.2)
        pose.point_at(f"{side}Foot", down)

    def stand_legs(self, pose: Pose, spread: float = 0.0) -> None:
        for sign, side in SIDES:
            self.front_leg(pose, sign, side, Vector((sign * spread, 0.0, 0.0)))
            self.hind_leg(pose, sign, side, Vector((sign * spread, 0.0, 0.0)))

    def gait_legs(self, pose: Pose, t: float, distance: float, stance: float, lift: float, phases: dict[str, float]) -> None:
        for sign, side in SIDES:
            front, bend_f = _foot_path((t + phases[f"{side}Front"]) % 1.0, distance, stance, lift)
            hind, bend_h = _foot_path((t + phases[f"{side}Hind"]) % 1.0, distance, stance, lift * 1.1)
            self.front_leg(pose, sign, side, front, bend_f)
            self.hind_leg(pose, sign, side, hind, bend_h)

    # -- las animaciones ------------------------------------------------------

    def idle(self, t: float) -> Pose:
        pose = self.pose()
        breath = _wave(t * 3.0)
        self.body(pose, drop=0.01, bob=0.004 * breath)
        pose.turn("Chest", LEFT, 1.0 * breath)
        self.head(pose, lift=2.0 * _wave(t, 0.3), turn=8.0 * _wave(t, 0.1))
        self.tail(pose, -10.0, 6.0 * _wave(t * 2.0))
        self.stand_legs(pose)
        return pose

    def alert(self, t: float) -> Pose:
        """Vigilar: la cabeza alta, las orejas tiesas y la cola rígida."""
        pose = self.pose()
        breath = _wave(t * 4.0)
        self.body(pose, drop=0.0, pitch=-3.0, bob=0.003 * breath)
        self.head(pose, lift=14.0, turn=12.0 * _wave(t, 0.25), ears=18.0)
        self.tail(pose, 10.0)
        self.stand_legs(pose, 0.01)
        return pose

    def growl(self, t: float) -> Pose:
        """Gruñir: la cabeza baja y adelantada, los dientes a la vista, las patas abiertas."""
        pose = self.pose()
        shake = _wave(t * 6.0)
        self.body(pose, drop=0.07, pitch=8.0, bob=0.004 * shake)
        self.head(pose, lift=-14.0, jaw=12.0 + 3.0 * shake, ears=-20.0)
        self.tail(pose, 5.0, 2.0 * shake)
        self.stand_legs(pose, 0.03)
        return pose

    def sniff(self, t: float) -> Pose:
        """Olfatear quieto: el hocico al suelo, a sacudidas."""
        pose = self.pose()
        twitch = _wave(t * 5.0)
        self.body(pose, drop=0.03, pitch=12.0)
        self.head(pose, lift=-45.0 + 3.0 * twitch, turn=10.0 * _wave(t), ears=-5.0)
        self.tail(pose, -5.0, 10.0 * _wave(t * 2.0))
        self.stand_legs(pose)
        return pose

    def eat(self, t: float) -> Pose:
        """Comer: la cabeza abajo, tirando y sacudiendo lo que tiene entre los dientes."""
        pose = self.pose()
        tug = _wave(t * 2.0)
        self.body(pose, drop=0.05, pitch=10.0, bob=0.01 * tug)
        self.head(pose, lift=-38.0 + 10.0 * max(0.0, tug), turn=14.0 * _wave(t * 2.0, 0.25), jaw=10.0 + 8.0 * abs(tug), ears=-10.0)
        self.tail(pose, -6.0)
        self.stand_legs(pose, 0.02)
        return pose

    def lie(self, t: float) -> Pose:
        """Echado, como una esfinge: las patas de delante estiradas y las de atrás dobladas."""
        pose = self.pose()
        breath = _wave(t * 2.0)
        self.body(pose, drop=0.46, pitch=-2.0, bob=0.006 * breath)
        pose.turn("Chest", LEFT, 1.5 * breath)
        self.head(pose, lift=-8.0 + 4.0 * _wave(t, 0.2), turn=6.0 * _wave(t, 0.1), ears=-8.0)
        self.tail(pose, -30.0)
        for sign, side in SIDES:
            self.front_leg(pose, sign, side, Vector((sign * 0.01, -0.24, -0.08)), -80.0)
            self.hind_leg(pose, sign, side, Vector((sign * 0.07, -0.12, -0.12)), 0.0)
        return pose

    def howl(self, t: float) -> Pose:
        """Aullar: sentado, la cabeza al cielo y la boca abierta."""
        pose = self.pose()
        rise = smooth(min(1.0, t / 0.25)) * (1.0 - smooth(max(0.0, (t - 0.8) / 0.2)))
        self.body(pose, drop=0.22, pitch=-28.0)
        self.head(pose, lift=10.0 + 45.0 * rise, jaw=4.0 + 22.0 * rise, ears=-12.0)
        self.tail(pose, -35.0)
        for sign, side in SIDES:
            self.front_leg(pose, sign, side, Vector((0.0, -0.05, 0.0)))
            self.hind_leg(pose, sign, side, Vector((sign * 0.05, -0.16, -0.12)))
        return pose

    def bite(self, t: float) -> Pose:
        """Morder: se encoge, salta hacia delante con la boca abierta, cierra y sacude."""
        pose = self.pose()
        crouch = smooth(min(1.0, t / 0.25))
        lunge = smooth((t - 0.25) / 0.2) * (1.0 - smooth((t - 0.7) / 0.3))
        shake = _wave(t * 4.0) * smooth((t - 0.45) / 0.1) * (1.0 - smooth((t - 0.8) / 0.2))
        self.body(pose, drop=0.08 * crouch * (1.0 - lunge), pitch=10.0 * crouch - 6.0 * lunge)
        pose.move("Hips", Vector((0.0, -0.25 * lunge, 0.06 * lunge)))
        jaw = 32.0 * smooth((t - 0.2) / 0.15) * (1.0 - smooth((t - 0.42) / 0.06))
        self.head(pose, lift=-10.0 + 8.0 * lunge, turn=25.0 * shake, jaw=jaw, ears=-25.0)
        self.tail(pose, 8.0)
        for sign, side in SIDES:
            self.front_leg(pose, sign, side, Vector((0.0, -0.18 * lunge, 0.12 * lunge)), 40.0 * lunge)
            self.hind_leg(pose, sign, side, Vector((0.0, 0.1 * lunge, 0.0)))
        return pose

    def walk(self, t: float, stalk: bool = False) -> Pose:
        pose = self.pose()
        distance = STALK_DISTANCE if stalk else WALK_DISTANCE
        bob = 0.01 * math.cos(4.0 * math.pi * t)
        sway = 2.0 * _wave(t)
        self.body(pose, drop=0.09 if stalk else 0.02, pitch=6.0 if stalk else 0.0, bob=bob, sway=sway)
        if stalk:
            self.head(pose, lift=-16.0, ears=10.0)
            self.tail(pose, -2.0)
        else:
            self.head(pose, lift=-4.0 + 2.0 * _wave(t * 2.0), turn=4.0 * _wave(t))
            self.tail(pose, -8.0, 8.0 * _wave(t))
        phases = {"LeftHind": 0.0, "LeftFront": 0.75, "RightHind": 0.5, "RightFront": 0.25}
        self.gait_legs(pose, t, distance, 0.68, 0.07 if stalk else 0.09, phases)
        return pose

    def trot(self, t: float) -> Pose:
        pose = self.pose()
        bob = 0.018 * math.cos(4.0 * math.pi * (t - 0.1))
        self.body(pose, drop=0.02, bob=bob)
        self.head(pose, lift=-6.0 + 2.0 * _wave(t * 2.0))
        self.tail(pose, -4.0, 5.0 * _wave(t))
        phases = {"LeftFront": 0.0, "RightHind": 0.0, "RightFront": 0.5, "LeftHind": 0.5}
        self.gait_legs(pose, t, TROT_DISTANCE, 0.45, 0.13, phases)
        return pose

    def gallop(self, t: float) -> Pose:
        pose = self.pose()
        # El lomo se encoge al recoger las patas de atrás y se estira al lanzarse.
        flex = math.cos(2.0 * math.pi * (t - 0.1))
        self.body(pose, drop=0.05, pitch=6.0 * flex, bob=0.04 * math.cos(2.0 * math.pi * (t + 0.15)))
        pose.turn("Spine", LEFT, -9.0 * flex)
        pose.turn("Chest", LEFT, 5.0 * flex)
        self.head(pose, lift=-10.0 - 6.0 * flex, ears=-25.0)
        self.tail(pose, 5.0 * flex)
        phases = {"RightHind": 0.0, "LeftHind": 0.1, "LeftFront": 0.45, "RightFront": 0.55}
        self.gait_legs(pose, t, GALLOP_DISTANCE, 0.3, 0.2, phases)
        return pose


def dog_animations(rig: pb.Rig, j) -> None:
    poser = DogPoser(rig, j)
    moving = ["Hips"]
    pb.bake_action(rig, "quieto-loop", 3.0, poser.idle, moving=moving)
    pb.bake_action(rig, "vigilar-loop", 3.0, poser.alert, moving=moving)
    pb.bake_action(rig, "grunir-loop", 1.0, poser.growl, moving=moving)
    pb.bake_action(rig, "olfatear-loop", 1.6, poser.sniff, moving=moving)
    pb.bake_action(rig, "comer-loop", 1.2, poser.eat, moving=moving)
    pb.bake_action(rig, "echado-loop", 4.0, poser.lie, moving=moving)
    pb.bake_action(rig, "aullar", 2.4, poser.howl, moving=moving)
    pb.bake_action(rig, "morder", 0.8, poser.bite, moving=moving)
    pb.bake_action(rig, "andar-loop", 1.0, poser.walk, moving=moving)
    pb.bake_action(rig, "acechar-loop", 1.2, lambda t: poser.walk(t, True), moving=moving)
    pb.bake_action(rig, "trote-loop", 0.55, poser.trot, moving=moving)
    pb.bake_action(rig, "galope-loop", 0.42, poser.gallop, moving=moving)
