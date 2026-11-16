"""El deterioro de la superficie de Tumansk: lo que la bomba y dos años de abandono en
invierno han hecho con las calles (README, «La ambientación de la superficie: nada está
intacto»).

Socavones, como en *Metro 2033*: donde reventó lo que va bajo la calle (un colector, la
galería de la calefacción, una tubería del agua que se heló, la bóveda del túnel del
metro), el agua se llevó la tierra de debajo y la calle cayó al hueco. Cada uno
(datos.HUNDIMIENTOS) tiene un contorno irregular, alargado a lo largo de lo que reventó:

- El tránsito se corta por el contorno (transito.py) y una malla propia baja de la calle
  rota al fondo: la clase "socavon", con la regla "malla" (la altura de cada vértice). En
  el borde, la arista "derrumbe" pinta el corte de la calle (la costra de asfalto o de
  losas, la base de grava y la tierra); debajo, la pared de tierra casi a pico y el talud
  de cascotes hasta el fondo.
- Alrededor, la calle se hunde unos palmos antes de romperse (la cubeta): la rasante, el
  relieve y el terreno bajan juntos.
- Lo que cae dentro va como piezas (modelos de tools/blender/recipes/deterioro.py): losas
  y trozos de asfalto caídos por el talud, la tubería o la galería rota en el fondo, el
  charco helado. Los coches que estaban encima, al fondo, de morro.
- Las vías del tranvía que cruzan un socavón se cortan en el borde y asoman un poco sobre
  el hueco, dobladas (ferrocarril.tranvias).

Y por todas partes, lo que hacen la helada y el abandono: grietas (alrededor de los
socavones y las de la helada, a lo largo y de través de la calle), baches a grupos, tapas
de registro abiertas o robadas, piezas de bordillo que faltan (algunas, tiradas en la
calzada) y matojos secos por donde el pavimento se abre y en el balasto de las vías. La
pintura que falta, el óxido y las traviesas que faltan los pone la propia red de tránsito
(transito.py y la maqueta).

Todo es determinista: el azar sale de la clave de cada cosa.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

import datos as D
from geo import banda

# ---------------------------------------------------------------------------
# Medidas
# ---------------------------------------------------------------------------
# Lo que baja el corte de la calle en el borde (la costra y su base): la malla del socavón
# empieza ahí, bajo lo que se pisa.
CAPA = 0.42
# La pared de tierra casi a pico bajo el corte: lo que baja como mucho y lo que entra.
PARED_MAX = 1.6
PARED_ENTRA = (0.12, 0.3)
# El fondo: la parte del radio que ocupa (casi llano, con los cascotes).
FONDO = 0.32
# Separación de los vértices del borde y número de anillos del talud.
PASO_BORDE = 0.7
ANILLOS = (5, 12)
# La cubeta: lo que se hunde la calle en el borde y hasta dónde llega.
CUBETA_HONDO = (0.08, 0.025, 0.32)
CUBETA_ALCANCE = (2.5, 0.35)
# Lo que asoman sobre el hueco las vías del tranvía (la maqueta las dobla hacia abajo:
# TransitRails.HANG_DROP).
VOLADIZO_CARRIL = 1.2
# Margen que exigen las comprobaciones: del borde del pavimento y de lo que no puede caer.
MARGEN_PAVIMENTO = 1.0
MARGEN_EDIFICIO = 1.5
# Modelos del fondo según lo que reventó (None: solo cascotes).
TUBERIA = {"metro": None, "galeria": "canal_calefaccion", "colector": "colector_roto", "arroyo": "colector_roto",
           "agua": "tuberia_rota"}
# Los trozos de la calle caídos dentro: de asfalto (con su base de grava) o losas de hormigón.
PLACAS_ASFALTO = ("placa_asfalto_a", "placa_asfalto_b", "placa_asfalto_c")
LOSAS_ROTAS = ("losa_rota_a", "losa_rota_b")


def _semilla(clave: str) -> int:
    return int(hashlib.md5(clave.encode()).hexdigest()[:8], 16)


def _azar(clave: str) -> float:
    return _semilla(clave) / 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Contornos
# ---------------------------------------------------------------------------
def _ruido_periodico(rng: random.Random, n: int, armonicos: int = 7, desde: int = 2) -> np.ndarray:
    """Un ruido suave y cerrado alrededor del contorno (de -1 a 1), con los armónicos de
    `desde` en adelante (cuanto más altos, más menudo)."""
    theta = np.arange(n) * 2.0 * math.pi / n
    total = np.zeros(n)
    suma = 0.0
    for k in range(desde, desde + armonicos):
        amplitud = rng.uniform(0.3, 1.0) / k**0.85
        total += amplitud * np.cos(k * theta + rng.uniform(0.0, 2.0 * math.pi))
        suma += amplitud
    return total / suma


@dataclass
class Socavon:
    """Un socavón de datos.HUNDIMIENTOS con su geometría: el contorno (en sentido
    antihorario), sus vértices (el borde) y el centro."""

    datos: dict
    contorno: Polygon
    borde: np.ndarray  # (n, 2)
    centro: tuple[float, float]

    @property
    def ident(self) -> str:
        return self.datos["id"]


def contorno(h: dict) -> Socavon:
    """El contorno de un socavón: una elipse (`radio` a lo largo de `rumbo`, `ancho` de
    través) mordida por un ruido suave (el hueco no es redondo) y con los dientes de la
    costra rota en el borde. Al milímetro, como el resto del tránsito."""
    cx, cy = h["pos"]
    a, b = float(h["radio"]), float(h["ancho"])
    rumbo = math.radians(h["rumbo"])
    perimetro = math.pi * (3.0 * (a + b) - math.sqrt((3.0 * a + b) * (a + 3.0 * b)))
    n = int(min(170, max(32, round(perimetro / PASO_BORDE))))
    rng = random.Random(_semilla(h["id"] + "/contorno"))
    ruido = _ruido_periodico(rng, n)
    irregular = h.get("irregular", 0.14)
    theta = np.arange(n) * 2.0 * math.pi / n
    elipse = a * b / np.hypot(b * np.cos(theta), a * np.sin(theta))
    dientes = np.array([rng.uniform(-1.0, 1.0) for _ in range(n)]) * np.minimum(0.14, 0.03 * elipse)
    r = elipse * (1.0 + irregular * ruido) + dientes
    c, s = math.cos(rumbo), math.sin(rumbo)
    lx, ly = r * np.cos(theta), r * np.sin(theta)
    xs = np.round(cx + lx * c - ly * s, 3)
    ys = np.round(cy + lx * s + ly * c, 3)
    borde = np.stack([xs, ys], axis=1)
    return Socavon(h, Polygon(borde), borde, (float(cx), float(cy)))


_SOCAVONES: list[Socavon] | None = None


def socavones() -> list[Socavon]:
    """Los socavones de datos.HUNDIMIENTOS (se calculan una vez)."""
    global _SOCAVONES
    if _SOCAVONES is None:
        _SOCAVONES = [contorno(h) for h in D.HUNDIMIENTOS]
    return _SOCAVONES


def huecos():
    """Todos los contornos juntos."""
    return unary_union([s.contorno for s in socavones()])


# ---------------------------------------------------------------------------
# La cubeta: la calle se hunde alrededor antes de romperse
# ---------------------------------------------------------------------------
def _cubeta(s: Socavon) -> tuple[float, float]:
    radio = float(s.datos["radio"])
    base, por_metro, maximo = CUBETA_HONDO
    alcance = CUBETA_ALCANCE[0] + CUBETA_ALCANCE[1] * radio
    return min(maximo, base + por_metro * radio), alcance


def hundir(capas: list[np.ndarray], res: float) -> list[np.ndarray]:
    """Baja la cubeta de cada socavón en las capas de altura (la rasante, el relieve y el
    terreno, en la rejilla de `res` metros): todo lo que cae dentro del contorno, lo más
    hondo; fuera, menos cuanto más lejos, hasta su alcance."""
    ny, nx = capas[0].shape
    resultado = [c.copy() for c in capas]
    for s in socavones():
        hondo, alcance = _cubeta(s)
        x0, y0, x1, y1 = s.contorno.bounds
        i0, i1 = max(0, int((x0 - alcance) / res) - 1), min(nx, int((x1 + alcance) / res) + 2)
        j0, j1 = max(0, int((y0 - alcance) / res) - 1), min(ny, int((y1 + alcance) / res) + 2)
        if i0 >= i1 or j0 >= j1:
            continue
        gx, gy = np.meshgrid((np.arange(i0, i1) + 0.5) * res, (np.arange(j0, j1) + 0.5) * res)
        puntos = shapely.points(gx.ravel(), gy.ravel())
        d = shapely.distance(s.contorno, puntos).reshape(gx.shape)
        t = np.clip(d / alcance, 0.0, 1.0)
        baja = hondo * (1.0 - t * t * (3.0 - 2.0 * t))
        for capa in resultado:
            capa[j0:j1, i0:i1] -= baja
    return resultado


# ---------------------------------------------------------------------------
# La malla del socavón
# ---------------------------------------------------------------------------
@dataclass
class Malla:
    """Vértices (x, y), su altura, triángulos (índices, en sentido antihorario) y las
    coordenadas de la textura (en metros, desenrolladas desde el borde hacia el fondo)."""

    puntos: np.ndarray
    z: np.ndarray
    triangulos: np.ndarray
    uv: np.ndarray
    # El fondo: su altura y lo que mide de media el radio de su anillo de dentro.
    fondo_z: float = 0.0
    fondo_r: float = 0.0

    def __post_init__(self) -> None:
        a = self.puntos[self.triangulos[:, 0]]
        b = self.puntos[self.triangulos[:, 1]]
        c = self.puntos[self.triangulos[:, 2]]
        self._a = a
        self._e1 = b - a
        self._e2 = c - a
        self._det = self._e1[:, 0] * self._e2[:, 1] - self._e1[:, 1] * self._e2[:, 0]

    def z_en(self, xs, ys) -> np.ndarray:
        """La altura en puntos sueltos (lineal en su triángulo; fuera, la del vértice más
        cercano)."""
        xs = np.atleast_1d(np.asarray(xs, float))
        ys = np.atleast_1d(np.asarray(ys, float))
        resultado = np.empty(len(xs))
        for k, (x, y) in enumerate(zip(xs, ys)):
            px, py = x - self._a[:, 0], y - self._a[:, 1]
            u = (px * self._e2[:, 1] - py * self._e2[:, 0]) / self._det
            v = (self._e1[:, 0] * py - self._e1[:, 1] * px) / self._det
            peor = np.minimum(np.minimum(u, v), 1.0 - u - v)
            m = int(np.argmax(peor))
            if peor[m] < -1e-4:
                cerca = int(np.argmin(np.hypot(self.puntos[:, 0] - x, self.puntos[:, 1] - y)))
                resultado[k] = self.z[cerca]
                continue
            i0, i1, i2 = self.triangulos[m]
            resultado[k] = self.z[i0] * (1.0 - u[m] - v[m]) + self.z[i1] * u[m] + self.z[i2] * v[m]
        return resultado

    def pendiente_en(self, x: float, y: float) -> tuple[float, float]:
        """La caída en un punto: (rumbo cuesta abajo en grados, pendiente en grados)."""
        paso = 0.4
        zx = (self.z_en([x + paso], [y])[0] - self.z_en([x - paso], [y])[0]) / (2 * paso)
        zy = (self.z_en([x], [y + paso])[0] - self.z_en([x], [y - paso])[0]) / (2 * paso)
        return math.degrees(math.atan2(-zy, -zx)), math.degrees(math.atan(math.hypot(zx, zy)))


def malla(s: Socavon, z_borde: np.ndarray) -> Malla:
    """La malla de un socavón: del borde (a `z_borde`, bajo el corte de la calle) baja la
    pared de tierra casi a pico, luego el talud de cascotes (más empinado arriba) hasta el
    fondo, a `hondo` bajo la calle, y en el centro la boca de lo que reventó."""
    h = s.datos
    rng = random.Random(_semilla(h["id"] + "/malla"))
    borde = s.borde
    n = len(borde)
    cx, cy = s.centro
    radial = borde - np.array([cx, cy])
    radio = np.hypot(radial[:, 0], radial[:, 1])
    direccion = radial / radio[:, None]
    hondo = float(h["hondo"])
    calle = float(np.mean(z_borde)) + CAPA
    z_fondo = calle - hondo
    anillos = int(min(ANILLOS[1], max(ANILLOS[0], round(hondo / 0.6) + 3)))
    # La pared bajo el corte: cuánto entra y cuánto baja (con ruido a lo largo del borde).
    entra = PARED_ENTRA[0] + (PARED_ENTRA[1] - PARED_ENTRA[0]) * (0.5 + 0.5 * _ruido_periodico(rng, n))
    pared = min(PARED_MAX, 0.22 * hondo + 0.35) * (0.75 + 0.25 * (1.0 + _ruido_periodico(rng, n)))
    pared = np.minimum(pared, np.maximum(0.2, z_borde - z_fondo - 0.4))
    fondo = radio * FONDO * (1.0 + 0.25 * _ruido_periodico(rng, n))
    r1 = radio - entra
    z1 = z_borde - pared
    # Los radios y las alturas de cada anillo (0: el borde; 1: el pie de la pared; el
    # último: el borde del fondo).
    rs = [radio, r1]
    zs = [z_borde, z1]
    cascotes = 0.12 * math.sqrt(hondo)
    # Desprendimientos: donde el talud se comió más la pared (bahías) y donde queda un
    # espolón; y las cárcavas que abrió el agua al bajar.
    bahia = _ruido_periodico(rng, n, 5)
    carcava = _ruido_periodico(rng, n, 8, desde=7)
    for k in range(2, anillos + 1):
        t = (k - 1) / (anillos - 1)
        joroba = math.sin(math.pi * t)
        rs.append(r1 + (fondo - r1) * t + 0.18 * (r1 - fondo) * joroba * bahia)
        bulto = cascotes * joroba * np.array([rng.uniform(-1.0, 1.0) for _ in range(n)])
        surco = 0.22 * math.sqrt(hondo) * joroba * carcava
        zs.append(z1 + (z_fondo - z1) * (1.0 - (1.0 - t) ** 2) + bulto + surco)
    # El fondo: un anillo a media distancia y el centro: la boca de lo reventado (más honda
    # en el metro: se baja por ahí al túnel). Donde corría agua, el fondo es llano y el
    # centro, una cubeta poco honda donde se heló el charco.
    rs.append(fondo * 0.5)
    agua = h["causa"] != "metro"
    llano = 0.0 if agua else cascotes * 0.6
    zs.append(z_fondo + np.array([rng.uniform(-1.0, 1.0) for _ in range(n)]) * llano)
    boca = 0.12 if agua else 2.2
    puntos = []
    alturas = []
    for r, z in zip(rs, zs):
        puntos.append(np.array([cx, cy]) + direccion * r[:, None])
        alturas.append(np.asarray(z, float))
    puntos.append(np.array([[cx, cy]]))
    alturas.append(np.array([z_fondo - boca]))
    xy = np.concatenate(puntos)
    z = np.concatenate(alturas)
    # Triángulos: tiras entre anillos seguidos (la diagonal más corta) y un abanico al centro.
    tris = []
    filas = len(rs)
    for k in range(filas - 1):
        for i in range(n):
            j = (i + 1) % n
            a, b = k * n + i, k * n + j
            c, d = (k + 1) * n + j, (k + 1) * n + i
            if np.hypot(*(xy[a] - xy[c])) <= np.hypot(*(xy[b] - xy[d])):
                tris += [(a, b, c), (a, c, d)]
            else:
                tris += [(a, b, d), (b, c, d)]
    centro = filas * n
    for i in range(n):
        j = (i + 1) % n
        tris.append(((filas - 1) * n + i, (filas - 1) * n + j, centro))
    tris = np.array(tris, dtype=int)
    # Todos en sentido antihorario (el borde ya lo es).
    p0, p1, p2 = xy[tris[:, 0]], xy[tris[:, 1]], xy[tris[:, 2]]
    area = (p1[:, 0] - p0[:, 0]) * (p2[:, 1] - p0[:, 1]) - (p1[:, 1] - p0[:, 1]) * (p2[:, 0] - p0[:, 0])
    tris[area < 0] = tris[area < 0][:, [0, 2, 1]]
    # La textura, desenrollada: cada vértice a lo largo de su radio según lo que mide el
    # camino desde el borde (las paredes no la estiran).
    largo = np.zeros((filas, n))
    for k in range(1, filas):
        dr = rs[k - 1] - rs[k]
        dz = np.asarray(zs[k - 1], float) - np.asarray(zs[k], float)
        largo[k] = largo[k - 1] + np.hypot(dr, dz)
    total = largo[-1] + fondo * 0.5
    escala = radio * (1.0 - largo / total)
    uv = np.concatenate([np.array([cx, cy]) + direccion * escala[k][:, None] for k in range(filas)]
                        + [np.array([[cx, cy]])])
    return Malla(np.round(xy, 3), np.round(z, 3), tris, np.round(uv, 2), round(z_fondo, 3),
                 float(np.mean(fondo * 0.5)))


# ---------------------------------------------------------------------------
# Lo que cae dentro
# ---------------------------------------------------------------------------
def piezas(s: Socavon, m: Malla, en_calzada: float) -> list[dict]:
    """Las piezas de un socavón: losas y trozos de costra caídos por el talud (de asfalto
    o de hormigón según lo que había encima: `en_calzada` es la parte del borde que era
    calzada), la tubería o la galería rota en el fondo y el charco helado."""
    h = s.datos
    rng = random.Random(_semilla(h["id"] + "/piezas"))
    cx, cy = s.centro
    radio, ancho, hondo = float(h["radio"]), float(h["ancho"]), float(h["hondo"])
    resultado = []

    def poner(modelo: str, x: float, y: float, rumbo: float, cabeceo: float, alabeo: float, escala: float,
              hundido: float, estira: float = 1.0, z: float | None = None) -> None:
        if z is None:
            z = float(m.z_en([x], [y])[0]) - hundido
        resultado.append({"modelo": modelo, "pos": (round(x, 3), round(y, 3)), "z": round(z, 3),
                          "rumbo": round(rumbo % 360.0, 1), "cabeceo": round(cabeceo, 1),
                          "alabeo": round(alabeo, 1), "escala": round(escala, 2), "estira": round(estira, 2)})

    perimetro = s.contorno.length
    cuantas = int(min(16, max(3, perimetro / 5.0)))
    borde = s.borde
    for k in range(cuantas):
        i = int((k + rng.uniform(0.1, 0.9)) / cuantas * len(borde)) % len(borde)
        bx, by = borde[i]
        t = rng.uniform(0.25, 0.85)
        x, y = bx + (cx - bx) * t, by + (cy - by) * t
        abajo, cuesta = m.pendiente_en(x, y)
        modelo = PLACAS_ASFALTO[k % 3] if rng.random() < en_calzada else LOSAS_ROTAS[k % 2]
        poner(modelo, x, y, abajo + rng.uniform(-35.0, 35.0), -min(55.0, cuesta) * rng.uniform(0.6, 1.0),
              rng.uniform(-18.0, 18.0), rng.uniform(0.75, 1.25) * min(1.0, 0.45 + 0.1 * ancho), 0.08)
    # Y algunas colgando del borde, de morro hacia el hueco: lo alto, a ras de la calle.
    for k in range(max(2, cuantas // 3)):
        i = int((k + rng.uniform(0.2, 0.8)) / max(2, cuantas // 3) * len(borde)) % len(borde)
        bx, by = borde[i]
        hacia = math.atan2(cy - by, cx - bx)
        escala = rng.uniform(0.8, 1.15) * min(1.0, 0.45 + 0.1 * ancho)
        mitad = 0.6 * escala
        cabeceo = rng.uniform(28.0, 50.0)
        dentro = mitad * math.cos(math.radians(cabeceo))
        calle = float(m.z_en([bx], [by])[0]) + CAPA
        modelo = PLACAS_ASFALTO[(k + 1) % 3] if rng.random() < en_calzada else LOSAS_ROTAS[k % 2]
        poner(modelo, bx + math.cos(hacia) * dentro, by + math.sin(hacia) * dentro,
              math.degrees(hacia) + rng.uniform(-15.0, 15.0), cabeceo, rng.uniform(-10.0, 10.0), escala, 0.0,
              z=calle - mitad * math.sin(math.radians(cabeceo)) - 0.3)
    tubo = TUBERIA[h["causa"]]
    if tubo is not None:
        # A su tamaño, pero tan largo como el fondo y algo más: sigue bajo los taludes.
        largo = 2.0 * radio * FONDO * 1.4
        poner(tubo, cx, cy, h["rumbo"] + rng.uniform(-6.0, 6.0), rng.uniform(-4.0, 4.0), rng.uniform(-6.0, 6.0),
              1.0, 0.18, max(0.6, min(1.8, largo / 3.6)))
    if h["causa"] != "metro":
        # El charco helado llena la cubeta del centro (el modelo mide un metro de radio).
        resultado.append({"modelo": "charco_helado", "pos": (round(cx, 3), round(cy, 3)),
                          "z": round(m.fondo_z - 0.02, 3), "rumbo": round(rng.uniform(0.0, 360.0), 1),
                          "cabeceo": 0.0, "alabeo": 0.0, "escala": round(0.8 * m.fondo_r, 2), "estira": 1.0})
    return resultado


# ---------------------------------------------------------------------------
# Los vehículos que estaban encima
# ---------------------------------------------------------------------------
def hundir_vehiculos() -> list[dict]:
    """Los vehículos que caen en un socavón: el más cercano al centro (y en los grandes,
    alguno más) queda en el fondo de morro, inclinado; los demás se los tragó el hueco
    (no se ven). Cambia datos.VEHICULOS; devuelve los que caen."""
    caidos = []
    quitar = set()
    for s in socavones():
        h = s.datos
        dentro = s.contorno.buffer(1.0)
        cerca = [(Point(v["pos"]).distance(Point(s.centro)), n) for n, v in enumerate(D.VEHICULOS)
                 if v["tipo"] not in ("tranvia", "vagon", "coche_tren", "locomotora") and dentro.contains(Point(v["pos"]))]
        cerca.sort()
        caben = 1 + int(float(h["radio"]) // 8.0)
        rng = random.Random(_semilla(h["id"] + "/vehiculos"))
        cx, cy = s.centro
        fondo = min(float(h["radio"]), float(h["ancho"])) * FONDO
        for orden, (_, n) in enumerate(cerca):
            quitar.add(n)
            if orden >= caben:
                continue
            v = dict(D.VEHICULOS[n])
            angulo = (2.0 * math.pi * orden / caben) + rng.uniform(-0.4, 0.4)
            lejos = 0.0 if caben == 1 else fondo * 0.8
            v["pos"] = (round(cx + math.cos(angulo) * lejos, 1), round(cy + math.sin(angulo) * lejos, 1))
            v["angulo"] = round(v["angulo"] + rng.uniform(-25.0, 25.0), 1)
            v["cabeceo"] = round(rng.uniform(24.0, 40.0), 1)
            v["alabeo"] = round(rng.uniform(-12.0, 12.0), 1)
            v["socavon"] = h["id"]
            caidos.append(v)
    D.VEHICULOS[:] = [v for n, v in enumerate(D.VEHICULOS) if n not in quitar] + caidos
    return caidos


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------
def comprobar(pavimento) -> list[str]:
    """Lo que tiene que cumplir cada socavón: dentro de lo pavimentado (con margen), lejos
    de los edificios, las vías del tren, los árboles, las tuberías en alto, las vallas, la
    Escalinata, el río y los demás socavones."""
    problemas = []
    edificios = unary_union([e["huella"] for e in D.EDIFICIOS])
    vias = unary_union([banda(v["puntos"], 6.0) for v in D.VIAS])
    en_alto = unary_union([LineString(t["puntos"]).buffer(1.5) for t in D.TUBERIAS]
                          + [LineString(v["puntos"]).buffer(1.0) for v in D.VALLAS]
                          + [LineString(l["puntos"]).buffer(3.0) for l in D.LINEAS_ELECTRICAS])
    arboles = unary_union([Point(a["pos"]).buffer(1.0) for a in D.ARBOLES])
    # Las rendijas de milímetros entre grupos no son bordes del pavimento.
    dentro = pavimento.buffer(0.05, join_style=2).buffer(-0.05 - MARGEN_PAVIMENTO, join_style=2)
    lista = socavones()
    for n, s in enumerate(lista):
        c = s.contorno
        nombre = s.ident
        if not c.is_valid:
            problemas.append(f"Socavón {nombre}: el contorno no es válido")
            continue
        if not c.within(dentro):
            fuera = c.difference(dentro).area
            problemas.append(f"Socavón {nombre}: {fuera:.1f} m² a menos de {MARGEN_PAVIMENTO} m del borde del pavimento")
        for cosa, forma, margen in (("un edificio", edificios, MARGEN_EDIFICIO), ("la vía del tren", vias, 0.0),
                                    ("una tubería, una valla o una línea", en_alto, 0.0), ("un árbol", arboles, 0.0),
                                    ("el río", D.RIO, 2.0)):
            if c.buffer(margen).intersects(forma):
                problemas.append(f"Socavón {nombre}: toca {cosa}")
        for otro in lista[n + 1:]:
            if c.distance(otro.contorno) < 3.0:
                problemas.append(f"Socavones {nombre} y {otro.ident}: a menos de 3 m")
    return problemas


# ---------------------------------------------------------------------------
# Grietas
# ---------------------------------------------------------------------------
# Las clases en las que se pintan grietas (lo pavimentado que sigue la rasante).
CLASES_CON_GRIETAS = ("calzada", "adoquin", "acera", "losas", "plaza", "paseo", "isleta", "paso_nivel", "via_tranvia")
# Grietas de la helada: una cada tantos metros cuadrados de cada clase.
GRIETAS_POR_M2 = {"calzada": 1 / 140.0, "acera": 1 / 220.0, "losas": 1 / 260.0, "plaza": 1 / 260.0,
                  "paseo": 1 / 300.0, "isleta": 1 / 260.0, "adoquin": 1 / 400.0, "paso_nivel": 1 / 60.0,
                  "via_tranvia": 1 / 120.0}


def _quebrada(rng: random.Random, x: float, y: float, rumbo: float, largo: float, paso: float,
              tuerce: float) -> list[tuple[float, float]]:
    """Una grieta: un camino quebrado que se tuerce poco a poco."""
    puntos = [(x, y)]
    andado = 0.0
    while andado < largo:
        rumbo += rng.uniform(-tuerce, tuerce)
        tramo = min(paso * rng.uniform(0.6, 1.4), largo - andado)
        x += math.cos(rumbo) * tramo
        y += math.sin(rumbo) * tramo
        puntos.append((x, y))
        andado += tramo
    return puntos


def grietas(t) -> list[dict]:
    """Las grietas de la calle (transito.Trazado ya con sus grupos): alrededor de cada
    socavón, radiales desde el borde y en arco algo más allá (la calle se abrió al ceder);
    y por todas partes, las de la helada: a lo largo de la calle (las rodadas, la junta
    del centro), de través y alguna sin orden. Cada una va dentro de una sola clase (con
    su ancho en metros); la maqueta las pinta a ras de lo que se pisa."""
    import transito as T

    clases = {c: t.superficies[c] for c in CLASES_CON_GRIETAS if c in t.superficies}
    dentro = {c: f.buffer(-0.12) for c, f in clases.items()}
    for f in dentro.values():
        shapely.prepare(f)
    crudas = []  # (puntos, ancho)
    for s in socavones():
        h = s.datos
        rng = random.Random(_semilla(h["id"] + "/grietas"))
        cx, cy = s.centro
        radio = float(h["radio"])
        cuantas = int(min(26, max(8, s.contorno.length / 2.2)))
        for k in range(cuantas):
            i = int((k + rng.uniform(0.0, 1.0)) / cuantas * len(s.borde)) % len(s.borde)
            bx, by = s.borde[i]
            fuera = math.atan2(by - cy, bx - cx) + rng.uniform(-0.35, 0.35)
            largo = rng.uniform(0.25, 0.7) * min(9.0, 1.5 + radio * 0.45)
            crudas.append((_quebrada(rng, bx, by, fuera, largo, 0.45, 0.35), rng.uniform(0.02, 0.05)))
        largo_eje, ancho_eje, giro = radio, float(h["ancho"]), math.radians(h["rumbo"])
        for k in range(2):
            lejos = rng.uniform(0.8, 2.6) + 0.1 * radio
            arco = rng.uniform(0.6, 1.6)
            empieza = rng.uniform(0.0, 2.0 * math.pi)
            pasos = max(4, int(arco * (radio + lejos) / 0.5))
            puntos = []
            for j in range(pasos + 1):
                a = empieza + arco * j / pasos
                elipse = largo_eje * ancho_eje / math.hypot(ancho_eje * math.cos(a - giro),
                                                            largo_eje * math.sin(a - giro))
                r = elipse * 1.15 + lejos + rng.uniform(-0.1, 0.1)
                puntos.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            crudas.append((puntos, rng.uniform(0.015, 0.035)))
    # Las de la helada, por clase y a lo largo de cada grupo (su ángulo es el de la calle).
    for n, g in enumerate(t.grupos):
        if g.clase not in GRIETAS_POR_M2 or g.elevado or g.regla.get("tipo") != "terreno":
            continue
        rng = random.Random(_semilla(f"grietas/{g.clase}/{n}"))
        cuantas = int(g.forma.area * GRIETAS_POR_M2[g.clase] + rng.random())
        if cuantas == 0:
            continue
        x0, y0, x1, y1 = g.forma.bounds
        shapely.prepare(g.forma)
        hechas = 0
        intentos = 0
        while hechas < cuantas and intentos < cuantas * 6:
            intentos += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if not shapely.contains_xy(g.forma, x, y):
                continue
            calle = math.radians(g.angulo)
            tipo = rng.random()
            if tipo < 0.5:
                # A lo largo de la calle (en un sentido o en el otro).
                rumbo = calle + rng.uniform(-0.15, 0.15) + (math.pi if rng.random() < 0.5 else 0.0)
                largo, tuerce = rng.uniform(2.0, 9.0), 0.18
            elif tipo < 0.8:
                rumbo = calle + math.pi / 2 + rng.uniform(-0.25, 0.25)
                largo, tuerce = rng.uniform(1.0, 4.5), 0.25
            else:
                rumbo = rng.uniform(0.0, 2.0 * math.pi)
                largo, tuerce = rng.uniform(0.8, 3.5), 0.5
            crudas.append((_quebrada(rng, x, y, rumbo, largo, 0.6, tuerce), rng.uniform(0.012, 0.04)))
            hechas += 1
    # Cada una, partida por las clases: los trozos de más de 30 cm, dentro de la suya.
    resultado = []
    for puntos, ancho in crudas:
        linea = LineString(puntos)
        for clase, forma in dentro.items():
            if not forma.intersects(linea):
                continue
            for trozo in T.lineas(linea.intersection(forma)):
                if trozo.length > 0.3:
                    resultado.append({"puntos": [(round(x, 3), round(y, 3)) for x, y in trozo.coords],
                                      "ancho": round(ancho, 3), "clase": clase})
    return resultado


# ---------------------------------------------------------------------------
# Baches, tapas, bordillos y matojos
# ---------------------------------------------------------------------------
BACHES = ("bache_a", "bache_b", "bache_c")
# Baches: grupos (donde el agua se encharca) por metro cuadrado de cada clase.
BACHES_POR_M2 = {"calzada": 1 / 650.0, "adoquin": 1 / 500.0, "paso_nivel": 1 / 300.0, "acera": 1 / 2600.0,
                 "losas": 1 / 3000.0, "plaza": 1 / 3200.0}
# Tapas de registro abiertas (la tapa, tirada al lado) y que faltan (para chatarra).
TAPAS_ABIERTAS = 0.14
TAPAS_ROBADAS = 0.08
# Piezas de bordillo (de un metro) que faltan y, de esas, las que siguen tiradas al lado.
LARGO_BORDILLO = 1.0
BORDILLO_FALTA = 0.04
BORDILLO_TIRADO = 0.5
# Matojos secos: cada cuánto se prueba a poner uno y cuántas veces sale, según dónde.
MATOJOS = {"bordillo": (2.5, 0.16), "fachada": (2.5, 0.22), "via": (3.0, 0.45), "balasto": (3.0, 0.22)}


def _cerca_de_las_vias() -> object:
    """Lo que no se puede tocar junto a las vías del tren y del tranvía."""
    import ferrocarril as F

    return unary_union([banda(v["puntos"], 5.0) for v in D.VIAS]
                       + [via.buffer(1.4) for _, via in F.ejes_tranvia()])


def baches(t, alturas) -> list[dict]:
    """Los baches: a grupos (donde el agua se encharca y la helada levanta el asfalto),
    sobre todo en la calzada; lejos de las tapas, los sumideros, las vías y los socavones.
    Cada uno con la pendiente de la calle donde cae (la maqueta lo inclina con ella)."""
    import transito as T

    evitar = ([Point(d["pos"]).buffer(1.3) for d in t.detalles["tapas"]]
              + [Point(d["pos"]).buffer(1.1) for d in t.detalles["sumideros"]]
              + [_cerca_de_las_vias(), huecos().buffer(1.5)])
    prohibido = unary_union(evitar)
    resultado = []
    for clase, densidad in BACHES_POR_M2.items():
        forma = t.superficies.get(clase)
        if forma is None or forma.is_empty:
            continue
        dentro = forma.buffer(-0.7).difference(prohibido)
        if dentro.is_empty:
            continue
        shapely.prepare(dentro)
        rng = random.Random(_semilla("baches/" + clase))
        grupos = int(forma.area * densidad)
        x0, y0, x1, y1 = dentro.bounds
        hechos = intentos = 0
        while hechos < grupos and intentos < grupos * 30:
            intentos += 1
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if not shapely.contains_xy(dentro, x, y):
                continue
            hechos += 1
            for k in range(rng.choice((1, 1, 2, 2, 3, 4))):
                px = x + (rng.uniform(-2.2, 2.2) if k else 0.0)
                py = y + (rng.uniform(-2.2, 2.2) if k else 0.0)
                if not shapely.contains_xy(dentro, px, py):
                    continue
                z = T._z_en(t, alturas, px, py)
                gx = (T._z_en(t, alturas, px + 0.5, py) - T._z_en(t, alturas, px - 0.5, py))
                gy = (T._z_en(t, alturas, px, py + 0.5) - T._z_en(t, alturas, px, py - 0.5))
                resultado.append({"modelo": BACHES[rng.randrange(3)], "pos": (round(px, 3), round(py, 3)),
                                  "z": round(z, 3), "angulo": round(rng.uniform(0.0, 360.0), 1),
                                  "escala": round(rng.uniform(0.7, 1.6) if k == 0 else rng.uniform(0.4, 1.0), 2),
                                  "pendiente": [round(gx, 4), round(gy, 4)]})
    return resultado


def estropear_tapas(t, alturas) -> None:
    """Unas tapas de registro, abiertas (la tapa, tirada al lado) y otras que ya no están
    (se las llevaron para chatarra): queda el pozo abierto. Cambia t.detalles["tapas"]:
    `estado` (cerrada, abierta o sin_tapa) y, si está abierta, dónde quedó la tapa."""
    import transito as T

    for tapa in t.detalles["tapas"]:
        x, y = tapa["pos"]
        clave = f"tapa/{x}/{y}"
        r = _azar(clave)
        tapa["estado"] = "cerrada"
        if r < TAPAS_ROBADAS:
            tapa["estado"] = "sin_tapa"
            continue
        if r >= TAPAS_ROBADAS + TAPAS_ABIERTAS:
            continue
        tapa["estado"] = "sin_tapa"
        rng = random.Random(_semilla(clave + "/suelta"))
        donde = T._grupo_en(t, x, y)
        for _ in range(10):
            a = rng.uniform(0.0, 2.0 * math.pi)
            d = rng.uniform(0.8, 1.2)
            sx, sy = x + math.cos(a) * d, y + math.sin(a) * d
            if donde is not None and T._grupo_en(t, sx, sy) == donde:
                tapa["estado"] = "abierta"
                tapa["suelta"] = {"pos": (round(sx, 3), round(sy, 3)), "z": round(T._z_en(t, alturas, sx, sy), 3),
                                  "angulo": round(rng.uniform(0.0, 360.0), 1)}
                break


def romper_bordillos(t, alturas) -> list[dict]:
    """Las piezas de bordillo que faltan (de metro en metro: la helada las levantó y se
    cayeron o se las llevaron): sus tramos van a `huecos` de cada arista "bordillo"; la
    mitad sigue tirada en la calzada, al lado (lo que devuelve)."""
    import transito as T

    sueltos = []
    for a in t.aristas:
        if a.tipo != "bordillo":
            continue
        linea = LineString(a.puntos)
        largo = linea.length
        a.huecos = []
        base = f"bordillo/{round(a.puntos[0][0], 1)}/{round(a.puntos[0][1], 1)}"
        for k in range(int(largo // LARGO_BORDILLO)):
            clave = f"{base}/{k}"
            if _azar(clave) >= BORDILLO_FALTA:
                continue
            s0, s1 = k * LARGO_BORDILLO, (k + 1) * LARGO_BORDILLO
            if a.huecos and abs(a.huecos[-1][1] - s0) < 1e-6:
                a.huecos[-1][1] = s1
            else:
                a.huecos.append([s0, s1])
            if _azar(clave + "/tirado") >= BORDILLO_TIRADO:
                continue
            medio = linea.interpolate((s0 + s1) / 2.0)
            delante = linea.interpolate(min(largo, (s0 + s1) / 2.0 + 0.5))
            detras = linea.interpolate(max(0.0, (s0 + s1) / 2.0 - 0.5))
            dx, dy = delante.x - detras.x, delante.y - detras.y
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            # La calzada queda a la izquierda del bordillo.
            lejos = 0.35 + 0.9 * _azar(clave + "/lejos")
            x, y = medio.x - dy * lejos, medio.y + dx * lejos
            if T._grupo_en(t, x, y) != a.izq:
                continue
            sueltos.append({"pos": (round(x, 3), round(y, 3)), "z": round(T._z_en(t, alturas, x, y), 3),
                            "rumbo": round(math.degrees(math.atan2(dy, dx)) + (_azar(clave + "/giro") - 0.5) * 70.0, 1),
                            "alabeo": round((_azar(clave + "/alabeo") - 0.5) * 16.0, 1)})
    return sueltos


def matojos(t, alturas) -> list[dict]:
    """Los matojos secos que salen por donde el pavimento se abre: junto a los bordillos
    y al pie de las fachadas, en las grietas, en los alcorques, alrededor de los socavones
    y por todo el balasto de las vías que ya no se usan."""
    import ferrocarril as F
    import transito as T

    rng = random.Random(_semilla("matojos"))
    puntos = []  # (x, y, z o None)

    def junto_a(linea: LineString, paso: float, sale: float, lado: float) -> None:
        andado = rng.uniform(0.0, paso)
        while andado < linea.length:
            if rng.random() < sale:
                p = linea.interpolate(andado)
                q = linea.interpolate(min(linea.length, andado + 0.3))
                r = linea.interpolate(max(0.0, andado - 0.3))
                dx, dy = q.x - r.x, q.y - r.y
                n = math.hypot(dx, dy) or 1.0
                lejos = lado * rng.uniform(0.06, 0.22)
                puntos.append((p.x - dy / n * lejos, p.y + dx / n * lejos, None))
            andado += paso * rng.uniform(0.6, 1.4)

    for a in t.aristas:
        if a.tipo == "bordillo":
            paso, sale = MATOJOS["bordillo"]
            junto_a(LineString(a.puntos), paso, sale, 1.0 if rng.random() < 0.6 else -1.0)
        elif a.tipo == "fachada":
            paso, sale = MATOJOS["fachada"]
            junto_a(LineString(a.puntos), paso, sale, 1.0)
    for g in t.grietas:
        if rng.random() < 0.12:
            linea = LineString(g["puntos"])
            p = linea.interpolate(rng.uniform(0.0, linea.length))
            puntos.append((p.x, p.y, None))
    for a in t.alcorques:
        for _ in range(rng.choice((0, 1, 1, 2, 3))):
            puntos.append((a["pos"][0] + rng.uniform(-0.4, 0.4), a["pos"][1] + rng.uniform(-0.4, 0.4), None))
    for s in socavones():
        cx, cy = s.centro
        for _ in range(int(min(14, 4 + s.contorno.length / 6.0))):
            bx, by = s.borde[rng.randrange(len(s.borde))]
            lejos = rng.uniform(-0.25, 0.2) if rng.random() < 0.5 else rng.uniform(0.3, 1.6)
            d = math.hypot(bx - cx, by - cy) or 1.0
            puntos.append((bx + (bx - cx) / d * lejos, by + (by - cy) / d * lejos, None))
    # Las vías: al pie del balasto, a los lados, y entre las traviesas.
    for v in D.VIAS:
        perfil = alturas.ferrocarril.get(v["id"])
        if perfil is None:
            continue
        linea = LineString(v["puntos"])
        andado = 0.0
        paso = MATOJOS["via"][0]
        while andado < linea.length:
            p = linea.interpolate(andado)
            q = linea.interpolate(min(linea.length, andado + 0.5))
            dx, dy = q.x - p.x, q.y - p.y
            n = math.hypot(dx, dy) or 1.0
            if T._grupo_en(t, p.x, p.y) is None:
                formacion = float(F.z_en(perfil, [(p.x, p.y)])[0])
                if rng.random() < MATOJOS["via"][1]:
                    lado = rng.choice((-1.0, 1.0)) * rng.uniform(2.3, 2.9)
                    puntos.append((p.x - dy / n * lado, p.y + dx / n * lado, None))
                if rng.random() < MATOJOS["balasto"][1]:
                    lado = rng.uniform(-1.5, 1.5)
                    puntos.append((p.x - dy / n * lado, p.y + dx / n * lado, formacion + 0.3))
            andado += paso * rng.uniform(0.6, 1.4)
    resultado = []
    for x, y, z in puntos:
        if z is None:
            z = T._z_en(t, alturas, x, y)
        resultado.append({"pos": (round(x, 3), round(y, 3)), "z": round(float(z), 3),
                          "angulo": round(rng.uniform(0.0, 360.0), 1), "escala": round(rng.uniform(0.6, 1.3), 2),
                          "alto": round(rng.uniform(0.7, 1.4), 2)})
    return resultado
