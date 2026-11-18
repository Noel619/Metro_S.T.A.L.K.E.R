"""Lo que deja el abandono por la calle: escombros, basura y farolas rotas.

Nadie limpia la ciudad desde hace dos años (README, «La ambientación de la superficie»):

- Cascotes y ladrillos al pie de las fachadas dañadas (más cuanto peor está el edificio),
  y montones de escombros junto a los que la bomba destripó o arrasó.
- Basura en las cunetas: cartones, ramas, neumáticos, cascotes; contenedores en las
  aceras, muchos volcados, con la basura alrededor.
- Más cascotes por todas partes cuanto más cerca de la Zona Cero (los trajo la onda).
- Las farolas de las calles con calzada: en pie, torcidas, caídas o arrancadas (solo queda
  el muñón), según la onda: las caídas, lejos de la bomba.

Cada cosa sale como una pieza (modelo, posición, altura de lo que pisa, rumbo, cabeceo,
alabeo y escala) para las instancias de la maqueta (CityTransit). Todo determinista.
"""

from __future__ import annotations

import math
import random

import shapely
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

import datos as D
import deterioro as DT
import firmes as FR

CASCOTES = ("cascotes_a", "cascotes_b", "cascotes_c")
# Al pie de las fachadas, según el daño del edificio: cada cuántos metros de fachada hay
# un corro de cascotes y la parte de ellos que son montones de escombros.
FACHADAS = {2: (7.0, 0.0), 3: (3.5, 0.08), 4: (2.2, 0.18)}
# Lo lejos que llegan de la fachada (metros).
ALCANCE_FACHADA = 4.5
# Basura en las cunetas: cada cuántos metros de bordillo se prueba y qué sale.
CUNETA = 5.0
BASURA = (("carton", 0.44), ("rama", 0.16), ("neumatico", 0.08), ("cascotes_a", 0.2), ("ladrillos", 0.12))
# Contenedores: cada cuántos metros de acera y cuántos están volcados.
CONTENEDORES = 110.0
VOLCADOS = 0.4
# Cascotes que trajo la onda: metros cuadrados de calle por pieza, según la Zona Cero.
ONDA = ((500.0, 35.0), (800.0, 70.0), (1100.0, 180.0))
# Sobre los montones de escombros que tapan la calle: hasta dónde (de la Zona Cero) y
# metros cuadrados por pieza.
MONTONES_RADIO = 950.0
MONTONES_CADA = 75.0
# Y lo suelto por todas partes: metros cuadrados de calle por pieza, y qué es.
SUELTO = 110.0
SUELTOS = (("cascotes_a", 0.36), ("ladrillos", 0.18), ("carton", 0.3), ("rama", 0.1), ("neumatico", 0.03),
           ("cascotes_b", 0.03))
# Farolas: separación a lo largo de la calle, distancia al bordillo y lo que pasa con
# ellas (en pie, torcidas, caídas, arrancadas) lejos y cerca de la Zona Cero.
FAROLA_PASO = 34.0
FAROLA_BORDILLO = 0.7
FAROLAS_LEJOS = (0.5, 0.2, 0.15, 0.15)
FAROLAS_CERCA = (0.1, 0.25, 0.4, 0.25)
LARGO_FAROLA = 7.5


def _pieza(modelo: str, x: float, y: float, z: float, rumbo: float, cabeceo: float = 0.0, alabeo: float = 0.0,
           escala: float = 1.0) -> dict:
    return {"modelo": modelo, "pos": (round(x, 3), round(y, 3)), "z": round(float(z), 3),
            "rumbo": round(rumbo % 360.0, 1), "cabeceo": round(cabeceo, 1), "alabeo": round(alabeo, 1),
            "escala": round(escala, 2)}


def _elige(rng: random.Random, tabla) -> str:
    r = rng.random() * sum(p for _, p in tabla)
    for nombre, p in tabla:
        r -= p
        if r <= 0.0:
            return nombre
    return tabla[-1][0]


def _lejos_de_la_bomba(x: float, y: float) -> float:
    """El rumbo (grados) que se aleja de la Zona Cero desde un punto."""
    return math.degrees(math.atan2(y - D.GZ[1], x - D.GZ[0]))


def restos(t, alturas) -> list[dict]:
    """Todo lo tirado por la calle (sin las farolas): cascotes al pie de las fachadas,
    basura en las cunetas, contenedores y los cascotes de la onda. Solo donde se pisa
    (el tránsito), lejos de los vehículos y de las vías del tren."""
    import transito as T

    pisable = unary_union([g.forma for g in t.grupos
                           if not g.elevado and g.clase not in ("socavon", "firme", "peldano", "anden")])
    libre = pisable.difference(unary_union([Point(v["pos"]).buffer(2.4) for v in D.VEHICULOS]
                                           + [DT._cerca_de_las_vias()]))
    shapely.prepare(libre)
    resultado = []

    def poner(modelo: str, x: float, y: float, rng: random.Random, escala: float = 1.0, inclina: float = 8.0) -> None:
        if not shapely.contains_xy(libre, x, y):
            return
        # Sobre lo que se pisa o, si un montón de escombros lo tapa, sobre el montón.
        z = max(T._z_en(t, alturas, x, y), float(alturas.terreno([x], [y])[0]))
        resultado.append(_pieza(modelo, x, y, z - 0.02, rng.uniform(0.0, 360.0), rng.uniform(-inclina, inclina),
                                rng.uniform(-inclina, inclina), escala))

    # Al pie de las fachadas dañadas.
    for e in D.EDIFICIOS:
        dano = e.get("dano") or 1
        if dano < 2 or e["tipo"] in ("chimenea", "torre", "muralla"):
            continue
        cada, montones = FACHADAS[min(4, dano)]
        rng = random.Random(DT._semilla("restos/" + e["id"]))
        anillo = e["huella"].exterior
        andado = rng.uniform(0.0, cada)
        while andado < anillo.length:
            p = anillo.interpolate(andado)
            q = anillo.interpolate((andado + 0.5) % anillo.length)
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            # La huella va en sentido antihorario o no: se prueba hacia los dos lados.
            for lado in (1.0, -1.0):
                lejos = ALCANCE_FACHADA * rng.random() ** 1.6 + 0.4
                x, y = p.x + dy / n * lejos * lado, p.y - dx / n * lejos * lado
                if e["huella"].contains(Point(x, y)):
                    continue
                if rng.random() < montones:
                    poner("escombros" if rng.random() < 0.7 else "escombros_grande", x, y, rng,
                          rng.uniform(0.35, 0.7), 4.0)
                else:
                    poner(CASCOTES[rng.randrange(3)] if rng.random() < 0.75 else "ladrillos", x, y, rng,
                          rng.uniform(0.7, 1.3))
                break
            andado += cada * rng.uniform(0.6, 1.4)
    # En las cunetas, junto a los bordillos (la calzada a la izquierda).
    rng = random.Random(DT._semilla("restos/cunetas"))
    for a in t.aristas:
        if a.tipo != "bordillo":
            continue
        linea = LineString(a.puntos)
        andado = rng.uniform(0.0, CUNETA)
        while andado < linea.length:
            if rng.random() < 0.55:
                p = linea.interpolate(andado)
                q = linea.interpolate(min(linea.length, andado + 0.5))
                dx, dy = q.x - p.x, q.y - p.y
                n = math.hypot(dx, dy) or 1.0
                lejos = rng.uniform(0.2, 0.9)
                modelo = _elige(rng, BASURA)
                poner(modelo, p.x - dy / n * lejos, p.y + dx / n * lejos, rng, rng.uniform(0.75, 1.25))
            andado += CUNETA * rng.uniform(0.5, 1.5)
    # Contenedores en las aceras (unos volcados, con la basura alrededor).
    rng = random.Random(DT._semilla("restos/contenedores"))
    for a in t.aristas:
        if a.tipo != "bordillo" or a.der < 0 or t.grupos[a.der].clase not in ("acera", "losas"):
            continue
        linea = LineString(a.puntos)
        andado = rng.uniform(0.0, CONTENEDORES)
        while andado < linea.length:
            p = linea.interpolate(andado)
            q = linea.interpolate(min(linea.length, andado + 0.5))
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            x, y = p.x + dy / n * 1.3, p.y - dx / n * 1.3
            rumbo = math.degrees(math.atan2(dy, dx))
            if shapely.contains_xy(libre, x, y):
                z = T._z_en(t, alturas, x, y)
                if rng.random() < VOLCADOS:
                    # Volcado de lado (gira sobre su largo: queda a medio metro de alto).
                    resultado.append(_pieza("contenedor", x, y, z + 0.5, rumbo + rng.uniform(-40, 40),
                                            rng.choice((-88.0, 88.0))))
                    for _ in range(rng.randint(2, 4)):
                        poner(rng.choice(("carton", "carton", "rama")), x + rng.uniform(-1.6, 1.6),
                              y + rng.uniform(-1.6, 1.6), rng)
                else:
                    resultado.append(_pieza("contenedor", x, y, z, rumbo + rng.uniform(-8, 8)))
            andado += CONTENEDORES * rng.uniform(0.6, 1.4)
    # Los cascotes de la onda, más cuanto más cerca de la Zona Cero.
    rng = random.Random(DT._semilla("restos/onda"))
    x0, y0, x1, y1 = libre.bounds
    for radio, cada in ONDA:
        cerca = Point(*D.GZ).buffer(radio).intersection(libre)
        cuantos = int(cerca.area / cada)
        hechos = 0
        for _ in range(cuantos * 4):
            if hechos >= cuantos:
                break
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if math.hypot(x - D.GZ[0], y - D.GZ[1]) >= radio:
                continue
            antes = len(resultado)
            poner(CASCOTES[rng.randrange(3)] if rng.random() < 0.8 else "ladrillos", x, y, rng, rng.uniform(0.6, 1.4))
            hechos += len(resultado) - antes
    # Sobre los montones de escombros cerca de la Zona Cero (en la calle y fuera de ella):
    # escombro de verdad, que el relieve solo da el bulto, liso.
    rng = random.Random(DT._semilla("restos/montones"))
    fuera = unary_union([e["huella"] for e in D.EDIFICIOS] + [D.RIO, DT._cerca_de_las_vias()]
                        + [Point(v["pos"]).buffer(2.4) for v in D.VEHICULOS])
    cerca = Point(*D.GZ).buffer(MONTONES_RADIO).difference(fuera)
    shapely.prepare(cerca)
    mx0, my0, mx1, my1 = cerca.bounds
    for _ in range(int(cerca.area / MONTONES_CADA)):
        x, y = rng.uniform(mx0, mx1), rng.uniform(my0, my1)
        if not shapely.contains_xy(cerca, x, y):
            continue
        bulto = float(alturas.terreno([x], [y])[0]) - float(alturas.terreno_desnudo([x], [y])[0])
        if bulto < 0.6:
            continue
        modelo = "escombros" if rng.random() < 0.4 else rng.choice(CASCOTES)
        z = float(alturas.terreno([x], [y])[0]) - 0.1
        escala = rng.uniform(0.5, 1.0) if modelo == "escombros" else rng.uniform(1.0, 1.6)
        resultado.append(_pieza(modelo, x, y, z, rng.uniform(0.0, 360.0), rng.uniform(-15.0, 15.0),
                                rng.uniform(-15.0, 15.0), escala))
    # Lo suelto por todas partes (también en las medianas y las plazas).
    rng = random.Random(DT._semilla("restos/suelto"))
    cuantos = int(libre.area / SUELTO)
    hechos = 0
    for _ in range(cuantos * 4):
        if hechos >= cuantos:
            break
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        antes = len(resultado)
        poner(_elige(rng, SUELTOS), x, y, rng, rng.uniform(0.6, 1.2))
        hechos += len(resultado) - antes
    return resultado


def farolas(t, alturas) -> list[dict]:
    """Las farolas de las calles con calzada, a los dos lados, alternas, a FAROLA_BORDILLO
    del bordillo y con el brazo sobre la calle. Lo que les pasó depende de la Zona Cero:
    en pie, torcidas (hacia fuera de la bomba), caídas (lejos de la bomba, sin caer sobre
    un edificio) o arrancadas (queda el muñón)."""
    import transito as T

    acera = unary_union([t.superficies[c] for c in ("acera", "losas", "plaza", "isleta") if c in t.superficies])
    dentro = acera.buffer(-0.35)
    shapely.prepare(dentro)
    edificios = unary_union([e["huella"] for e in D.EDIFICIOS]).buffer(0.3)
    shapely.prepare(edificios)
    coches = unary_union([Point(v["pos"]).buffer(1.6) for v in D.VEHICULOS])
    arboles = [Point(a["pos"]) for a in D.ARBOLES]
    puestas: list[Point] = []
    resultado = []
    for c in D.CALLES:
        if c["tipo"] not in ("avenida", "principal", "calle"):
            continue
        calzada, _ = T.anchos(c)
        linea = LineString(c["puntos"])
        rng = random.Random(DT._semilla("farolas/" + c["id"]))
        andado = rng.uniform(4.0, FAROLA_PASO)
        lado = 1.0 if rng.random() < 0.5 else -1.0
        while andado < linea.length - 4.0:
            p = linea.interpolate(andado)
            q = linea.interpolate(min(linea.length, andado + 0.5))
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            fuera = calzada / 2.0 + FAROLA_BORDILLO
            x, y = p.x - dy * fuera * lado, p.y + dx * fuera * lado
            punto = Point(x, y)
            if (shapely.contains_xy(dentro, x, y) and all(punto.distance(o) > 8.0 for o in puestas)
                    and all(punto.distance(a) > 1.5 for a in arboles)):
                puestas.append(punto)
                resultado += _farola(t, alturas, x, y, -dy * lado, dx * lado, edificios, coches, rng)
            andado += FAROLA_PASO * rng.uniform(0.85, 1.15)
            lado = -lado
    return resultado


def _farola(t, alturas, x: float, y: float, hacia_x: float, hacia_y: float, edificios, coches,
            rng: random.Random) -> list[dict]:
    """Una farola en (x, y) con el brazo hacia (hacia_x, hacia_y) (de la acera a la calle):
    sus piezas (el modelo "farola" tiene el poste en +Y y el brazo en +X; en la maqueta,
    el brazo queda 90° a la derecha del rumbo)."""
    import transito as T

    z = T._z_en(t, alturas, x, y)
    factor = FR._factor(x, y)
    cerca = min(1.0, (factor - 1.0) / 1.6)
    probabilidades = [a + (b - a) * cerca for a, b in zip(FAROLAS_LEJOS, FAROLAS_CERCA)]
    r = rng.random() * sum(probabilidades)
    estado = 0
    while estado < 3 and r > probabilidades[estado]:
        r -= probabilidades[estado]
        estado += 1
    brazo = math.degrees(math.atan2(hacia_y, hacia_x))
    lejos = _lejos_de_la_bomba(x, y)
    if estado == 0:
        return [_pieza("farola", x, y, z, brazo + 90.0, 0.0, rng.uniform(-1.5, 1.5))]
    if estado == 1:
        return [_pieza("farola_torcida", x, y, z, lejos + 90.0 + rng.uniform(-25.0, 25.0))]
    if estado == 2:
        for intento in range(6):
            cae = lejos + rng.uniform(-50.0, 50.0) if intento < 4 else brazo + rng.uniform(-30.0, 30.0)
            ux, uy = math.cos(math.radians(cae)), math.sin(math.radians(cae))
            poste = LineString([(x, y), (x + ux * LARGO_FAROLA, y + uy * LARGO_FAROLA)])
            if edificios.intersects(poste) or coches.intersects(poste):
                continue
            punta = T._z_en(t, alturas, x + ux * LARGO_FAROLA, y + uy * LARGO_FAROLA)
            baja = math.degrees(math.atan2(z - punta, LARGO_FAROLA))
            # Tumbada con su base (la arrancó de cuajo), la punta sobre lo que pisa.
            return [_pieza("farola", x, y, z + 0.14, cae, 90.0 + baja, rng.uniform(-6.0, 6.0))]
    return [_pieza("farola_mocha", x, y, z, rng.uniform(0.0, 360.0))]
