"""El tendido aéreo del tranvía y del trolebús: los postes, los tirantes y los hilos, rotos
como lo demás de la calle (README, «La ambientación de la superficie»).

El tranvía lleva un hilo de contacto sobre cada vía y el trolebús, dos por sentido (el
positivo y el negativo, a 60 cm), a ALTO_HILO de la calle. Cuelgan, con una péndola, de
un tirante que cruza la calle de un poste a otro (en la acera, la mediana, la plaza o el
terreno de al lado) o, si a un lado no hay dónde ponerlo, de la ménsula de un poste solo.
Los apoyos van cada VANO metros; en las curvas, más juntos (el hilo va recto de un apoyo
a otro y no puede separarse de la vía más de DESVIO_MAX).

Después de la bomba y de dos inviernos, como las farolas y más cuanto más cerca de la
Zona Cero: postes torcidos hacia fuera de la bomba, caídos o partidos. Un apoyo que pierde
su poste ya no sostiene nada: el tirante cuelga hasta el suelo y los hilos de los vanos de
al lado se vienen abajo. En los demás vanos el hilo sigue tenso, se partió (cada mitad
cuelga de su apoyo y lo que sobra queda en la calle) o se soltó de las péndolas y está
en el suelo, todavía atado a sus dos apoyos. Sobre los socavones y el vano hundido del
puente, siempre roto.

Donde dos líneas van por la misma calle (el tranvía 3 y el trolebús 2 en la de los Mineros),
comparten los apoyos: los hilos de la segunda cuelgan de los tirantes de la primera.

Los postes son piezas como las farolas (modelos "poste_tendido", "poste_tendido_partido" y
"poste_tendido_punta" de tools/blender/recipes/transito.py; van con lo tirado por la calle)
y los cables, líneas con su grosor que la maqueta levanta como vigas finas (TransitSector).
"""

from __future__ import annotations

import math
import random

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import substring, unary_union

import datos as D

# Cada cuánto va un apoyo; en las curvas, lo que haga falta (sin bajar de VANO_MIN) para que
# el hilo no se separe de la vía más de DESVIO_MAX.
VANO = 30.0
VANO_MIN = 6.0
DESVIO_MAX = 0.35
# Alturas sobre la calle: el hilo de contacto y, encima, la péndola hasta el tirante o la
# ménsula. El poste y dónde se ata el tirante, sobre su base.
ALTO_HILO = 5.8
PENDOLA = 0.45
ALTO_POSTE = 8.5
ALTO_TIRANTE = 6.7
# Lo que queda en pie de un poste partido.
MUNON = 1.6
# Del eje de la línea a cada hilo (el tranvía, sobre sus dos vías; el trolebús, un par por
# sentido sobre el carril de la derecha) y lo más cerca que puede estar un poste.
HILOS_TRANVIA = (-1.6, 1.6)
HILOS_TROLEBUS = (-3.3, -2.7, 2.7, 3.3)
LIBRE_TRANVIA = 3.4
LIBRE_TROLEBUS = 4.4
# Lo más lejos que se busca sitio para un poste, cuánto se mete en la acera y lo más larga
# que puede ser una ménsula (del poste al último hilo).
POSTE_LEJOS = 22.0
RETRANQUEO = 0.6
MENSULA_MAX = 7.0
RADIO_TROLEBUS = 15.0
# Lo que les pasó (en pie, torcido, caído, partido), lejos y cerca de la Zona Cero, como las
# farolas pero más fuertes: son de tubo de acero y van atirantados.
POSTES_LEJOS = (0.86, 0.1, 0.02, 0.02)
POSTES_CERCA = (0.2, 0.33, 0.3, 0.17)
TORCIDO = (5.0, 16.0)
# Y a los hilos de cada vano (tenso, roto, caído). Los de una línea en un vano suelen correr
# la misma suerte; HILO_SUELTO de ellos, la suya.
VANOS_LEJOS = (0.85, 0.09, 0.06)
VANOS_CERCA = (0.25, 0.4, 0.35)
HILO_SUELTO = 0.2
# Un vano más largo que esto no se sostiene (le falta un apoyo): roto o caído.
VANO_SIN_APOYO = 65.0
# Lo más que cuelga o queda en el suelo de cada trozo de un hilo roto (el resto se lo
# llevaron para chatarra o lo tapa la nieve).
TROZO_MAX = 15.0
# Grosor de cada cable al dibujarlo (algo más que el de verdad, para que se vea).
GROSOR = {"hilo": 0.028, "tirante": 0.022, "pendola": 0.015, "mensula": 0.08, "tornapunta": 0.035}
# Por donde se sigue buscando sitio para un poste (la calle y la cama del tranvía) y donde no
# se pone nunca (los escalones y los andenes). Fuera de la calle, en cualquier otro sitio.
RODADO = ("calzada", "adoquin", "paso_nivel", "via_tranvia")
NO_PISABLE = ("peldano", "anden")


def lineas():
    """Las líneas con tendido: (id, eje, desplazamiento de cada hilo, lo libre junto al eje)."""
    import ferrocarril as F
    import vias as V

    resultado = []
    for linea in D.TRANVIAS:
        resultado.append((linea["id"], LineString(F.eje_tranvia(linea["puntos"])), HILOS_TRANVIA, LIBRE_TRANVIA))
    for linea in D.TROLEBUSES:
        eje = LineString(V.redondear(linea["puntos"], RADIO_TROLEBUS, 6.0))
        resultado.append((linea["id"], eje, HILOS_TROLEBUS, LIBRE_TROLEBUS))
    return resultado


def _apoyos(eje: LineString, fijos: list[float] = ()) -> list[float]:
    """Dónde va cada apoyo (lo andado por el eje): cada VANO metros o, en las curvas, donde la
    cuerda se separaría más de DESVIO_MAX. Si un tirante de otra línea cruza esta (`fijos`,
    lo andado hasta cada cruce), el apoyo va ahí: lo comparten."""
    largo = eje.length
    s = [0.0]
    while s[-1] < largo - 1e-6:
        a = s[-1]
        b = min(largo, a + VANO_MIN)
        t = b
        while t <= min(largo, a + VANO) + 1e-6:
            cuerda = LineString([eje.interpolate(a).coords[0], eje.interpolate(t).coords[0]])
            if substring(eje, a, t).hausdorff_distance(cuerda) > DESVIO_MAX:
                break
            b = t
            t += 1.0
        cerca = [f for f in fijos if a + VANO_MIN * 0.5 < f <= b + 1e-6]
        if cerca:
            b = max(cerca)
        elif largo - b < VANO_MIN * 0.5:
            b = largo
        s.append(b)
    return s


def _cruces(eje: LineString, tirantes: list[dict]) -> list[float]:
    """Lo andado por el eje hasta cada tirante de otra línea que lo cruza de través."""
    resultado = []
    for e in tirantes:
        a, b = (poste["base"][:2] for poste in e["postes"])
        cruce = LineString([a, b]).intersection(eje)
        if cruce.is_empty or cruce.geom_type != "Point":
            continue
        s = eje.project(cruce)
        _, d, _ = _marco(eje, s)
        u = (b - a) / (np.linalg.norm(b - a) or 1.0)
        if abs(float(u @ d)) < 0.4:
            resultado.append(s)
    return sorted(resultado)


def _compartido(ctx: "_Contexto", tirantes: list[dict], k: int, eje: LineString, s: float, hilos):
    """El apoyo de otra línea cuyo tirante cruza esta en `s`, con los puntos donde cuelgan
    los hilos de esta (bajo el tirante); None si no hay."""
    p, d, n = _marco(eje, s)
    for e in tirantes:
        a, b = (poste["base"][:2] for poste in e["postes"])
        largo = float(np.linalg.norm(b - a))
        u = (b - a) / (largo or 1.0)
        if abs(float(u @ d)) > 0.4 or LineString([a, b]).distance(Point(p)) > 1.0:
            continue
        puntos = []
        for off in hilos:
            q0 = p + n * off
            t, v = np.linalg.solve(np.array([[d[0], -u[0]], [d[1], -u[1]]]), a - q0)
            if not 0.8 < v < largo - 0.8:
                break
            x, y = q0 + d * t
            puntos.append(np.array([x, y, ctx.z(x, y) + ALTO_HILO]))
        else:
            e.setdefault("extra", []).extend(q + np.array([0.0, 0.0, PENDOLA]) for q in puntos)
            return {"k": k, "s": s, "hilos": puntos, "valido": e["valido"], "propio": False}
    return None


def _marco(eje: LineString, s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """El punto del eje a `s` metros, su dirección y su normal (a la izquierda)."""
    a = eje.interpolate(max(0.0, s - 0.5))
    b = eje.interpolate(min(eje.length, s + 0.5))
    d = np.array([b.x - a.x, b.y - a.y])
    d /= np.linalg.norm(d) or 1.0
    p = eje.interpolate(s)
    return np.array([p.x, p.y]), d, np.array([-d[1], d[0]])


def _elegir(rng: random.Random, probabilidades) -> int:
    r = rng.random() * sum(probabilidades)
    for k, p in enumerate(probabilidades):
        if r < p:
            return k
        r -= p
    return len(probabilidades) - 1


def _mezcla(lejos, cerca, x: float, y: float) -> list[float]:
    import firmes as FR

    cerca_gz = min(1.0, (FR._factor(x, y) - 1.0) / 1.6)
    return [a + (b - a) * cerca_gz for a, b in zip(lejos, cerca)]


def _inclinar(base: np.ndarray, punto: np.ndarray, rumbo: float, grados: float) -> np.ndarray:
    """Un punto que va con el poste (base en `base`) al inclinarse `grados` hacia `rumbo`."""
    u = np.array([math.cos(math.radians(rumbo)), math.sin(math.radians(rumbo)), 0.0])
    rel = punto - base
    a = math.radians(grados)
    lejos, alto = float(rel[:2] @ u[:2]), float(rel[2])
    lado = rel - u * lejos - np.array([0.0, 0.0, alto])
    lejos2 = lejos * math.cos(a) + alto * math.sin(a)
    alto2 = -lejos * math.sin(a) + alto * math.cos(a)
    return base + lado + u * lejos2 + np.array([0.0, 0.0, alto2])


class _Contexto:
    """Lo que se consulta una y otra vez: dónde se pisa, dónde puede ir un poste, qué está
    prohibido y la altura de cada punto."""

    def __init__(self, t, alturas) -> None:
        import deterioro as DT
        import ferrocarril as F
        import transito as T

        self.t, self.alturas = t, alturas
        # La calle (lo que rueda) por los grupos, también el tablero del puente y lo que era
        # calzada donde el firme está roto.
        self.rodado = unary_union([g.forma for g in t.grupos if g.clase in RODADO]
                                  + [z.contorno for z in t.firmes if z.clase in RODADO])
        tableros = unary_union([g.forma for g in t.grupos if g.elevado])
        vias = [LineString(p["puntos"]) for k, p in (alturas.ferrocarril or {}).items() if k != "plataforma"]
        self.prohibido = unary_union(
            [e["huella"].buffer(0.5) for e in D.EDIFICIOS] + [D.RIO.difference(tableros), DT.huecos(),
                                                              T._hueco_puente()]
            + [v.buffer(F.TRANVIA_ENTREVIA + 2.0) for v in vias]
            + [g.forma for g in t.grupos if g.clase in NO_PISABLE]
        )
        self.huecos = unary_union([DT.huecos(), T._hueco_puente()])
        for g in (self.rodado, self.prohibido, self.huecos):
            shapely.prepare(g)
        self.arboles = [Point(a["pos"]) for a in D.ARBOLES]
        self.vehiculos = unary_union([Point(v["pos"]).buffer(2.0) for v in D.VEHICULOS])
        self.farolas = [Point(f["pos"]) for f in t.detalles.get("restos", []) if f["modelo"].startswith("farola")]
        self.puestos: list[Point] = []

    def z(self, x: float, y: float) -> float:
        import transito as T

        return T._z_en(self.t, self.alturas, x, y)

    def libre(self, x: float, y: float) -> bool:
        p = Point(x, y)
        return (all(p.distance(a) > 1.0 for a in self.arboles if abs(a.x - x) < 2 and abs(a.y - y) < 2)
                and all(p.distance(f) > 1.5 for f in self.farolas if abs(f.x - x) < 2 and abs(f.y - y) < 2)
                and all(p.distance(o) > 3.0 for o in self.puestos if abs(o.x - x) < 4 and abs(o.y - y) < 4))

    def sitio(self, p: np.ndarray, n: np.ndarray, lado: float, desde: float):
        """Dónde va el poste a un lado de la línea (x, y y su distancia al eje): lo primero que
        no es calle (una acera, la mediana, una plaza, el tablero del puente o el terreno de al
        lado), un poco hacia dentro y donde no estorbe a un árbol, una farola u otro poste;
        None si antes hay algo donde no se puede (un edificio, el río, un hueco, el
        ferrocarril) o queda lejos."""
        d = desde
        while d <= POSTE_LEJOS:
            x, y = p + n * lado * d
            if shapely.contains_xy(self.prohibido, x, y):
                return None
            if not shapely.contains_xy(self.rodado, x, y):
                for dentro in (RETRANQUEO, RETRANQUEO + 0.75, RETRANQUEO + 1.5, 0.0):
                    x, y = p + n * lado * (d + dentro)
                    if (not shapely.contains_xy(self.prohibido, x, y) and not shapely.contains_xy(self.rodado, x, y)
                            and self.libre(x, y)):
                        return float(x), float(y), d + dentro
                return None
            d += 0.25
        return None


def tendido(t, alturas) -> tuple[list[dict], list[dict], dict]:
    """Los postes (piezas, como las farolas), los cables (líneas con su grosor y sus puntos
    [x, y, z]) y las cifras."""
    import restos as RS

    ctx = _Contexto(t, alturas)
    postes: list[dict] = []
    cables: list[dict] = []
    cifras = {"apoyos": 0, "compartidos": 0, "postes": [0, 0, 0, 0], "vanos": [0, 0, 0], "hilo_m": 0.0}
    tirantes: list[dict] = []
    por_linea = []
    for ident, eje, hilos, libre in lineas():
        apoyos = []
        for k, s in enumerate(_apoyos(eje, _cruces(eje, tirantes))):
            apoyo = _compartido(ctx, tirantes, k, eje, s, hilos)
            if apoyo is not None:
                cifras["compartidos"] += 1
                apoyos.append(apoyo)
                continue
            apoyo = _apoyo(ctx, ident, k, eje, s, hilos, libre)
            if apoyo is None:
                continue
            apoyos.append(apoyo)
            cifras["apoyos"] += 1
            for poste in apoyo["postes"]:
                postes += _piezas_poste(ctx, poste, RS)
                cifras["postes"][poste["estado"]] += 1
            if apoyo["tipo"] == "tirante":
                tirantes.append(apoyo)
        por_linea.append((ident, apoyos, hilos))
    # Los tirantes y las ménsulas, con las péndolas de todas las líneas que cuelgan de ellos.
    for _, apoyos, _ in por_linea:
        for apoyo in apoyos:
            if apoyo["propio"]:
                cables += _cables_apoyo(ctx, apoyo)
    for ident, apoyos, hilos in por_linea:
        for w in range(len(hilos)):
            pares = list(zip(apoyos, apoyos[1:]))
            # Los hilos de una línea en un vano suelen correr la misma suerte (la misma clave);
            # alguno, la suya.
            estados = []
            for a, b in pares:
                propia = random.Random(_semilla(f"{ident}/{a['k']}/{w}/propia")).random() < HILO_SUELTO
                estados.append(_estado_vano(ctx, f"{ident}/{a['k']}" + (f"/{w}" if propia else ""), a, b, w))
            for i, (a, b) in enumerate(pares):
                cifras["vanos"][estados[i]] += 1
                antes = estados[i - 1] if i > 0 else 0
                despues = estados[i + 1] if i + 1 < len(estados) else 0
                rng = random.Random(_semilla(f"{ident}/{a['k']}/{w}/hilo"))
                for puntos in _hilo(ctx, a, b, w, estados[i], antes == 0, despues == 0, rng):
                    cifras["hilo_m"] += _largo(puntos)
                    cables.append(_cable("hilo", puntos))
    cifras["hilo_m"] = round(cifras["hilo_m"])
    return postes, cables, cifras


def _apoyo(ctx: _Contexto, ident: str, k: int, eje: LineString, s: float, hilos, libre: float):
    """Un apoyo: sus postes (uno o dos) y dónde cuelga cada hilo, o None si no hay sitio."""
    p, d, n = _marco(eje, s)
    sitios = {lado: ctx.sitio(p, n, lado, libre) for lado in (1.0, -1.0)}
    if sitios[1.0] is None and sitios[-1.0] is None:
        return None
    rng = random.Random(_semilla(f"tendido/{ident}/{k}"))
    puntos_hilo = []
    for off in hilos:
        x, y = p + n * off
        puntos_hilo.append(np.array([x, y, ctx.z(x, y) + ALTO_HILO]))
    if sitios[1.0] is not None and sitios[-1.0] is not None:
        tipo = "tirante"
    else:
        tipo = "mensula"
        lado = 1.0 if sitios[1.0] is not None else -1.0
        alcance = max(abs(lado * sitios[lado][2] - off) for off in hilos) + 0.4
        if alcance > MENSULA_MAX:
            return None
    lista = []
    for lado, sitio in sitios.items():
        if sitio is None:
            continue
        x, y, _ = sitio
        z = ctx.z(x, y)
        ctx.puestos.append(Point(x, y))
        mezcla = _mezcla(POSTES_LEJOS, POSTES_CERCA, x, y)
        lista.append({"lado": lado, "base": np.array([x, y, z]), "estado": _elegir(rng, mezcla),
                      "rng": random.Random(_semilla(f"tendido/{ident}/{k}/{lado}"))})
    return {"k": k, "s": s, "p": p, "n": n, "d": d, "tipo": tipo, "postes": lista, "hilos": puntos_hilo,
            "valido": all(poste["estado"] <= 1 for poste in lista), "ident": ident, "propio": True}


def _semilla(clave: str) -> int:
    import deterioro as DT

    return DT._semilla(clave)


def _piezas_poste(ctx: _Contexto, poste: dict, RS) -> list[dict]:
    """El poste como pieza: en pie, torcido hacia fuera de la bomba, caído (lejos de la bomba,
    sin caer sobre un edificio ni un vehículo) o partido (el muñón y, si cabe, la punta
    tirada al lado). Apunta en el poste dónde queda atado el tirante ("atado")."""
    x, y, z = (float(v) for v in poste["base"])
    rng = poste["rng"]
    lejos = RS._lejos_de_la_bomba(x, y)
    estado = poste["estado"]
    if estado == 0:
        poste["atado"] = _arriba(poste, ALTO_TIRANTE)
        return [_pieza("poste_tendido", x, y, z, rng.uniform(0.0, 360.0))]
    if estado == 1:
        poste["rumbo"] = lejos + rng.uniform(-25.0, 25.0)
        poste["inclina"] = rng.uniform(*TORCIDO)
        poste["atado"] = _arriba(poste, ALTO_TIRANTE)
        return [_pieza("poste_tendido", x, y, z, poste["rumbo"], poste["inclina"])]
    largo = ALTO_POSTE if estado == 2 else ALTO_POSTE - MUNON
    desde = 0.0 if estado == 2 else 0.3
    for intento in range(8):
        cae = lejos + rng.uniform(-60.0, 60.0) if intento < 6 else rng.uniform(0.0, 360.0)
        ux, uy = math.cos(math.radians(cae)), math.sin(math.radians(cae))
        pie = (x + ux * desde, y + uy * desde)
        punta = (x + ux * (desde + largo), y + uy * (desde + largo))
        tumbado = LineString([pie, punta])
        if tumbado.intersects(ctx.vehiculos) or shapely.intersects(ctx.prohibido, tumbado):
            continue
        baja = math.degrees(math.atan2(ctx.z(*pie) - ctx.z(*punta), largo))
        # Atado donde estaba: a lo largo de lo que quedó tumbado, sobre el suelo.
        atado = desde + (ALTO_TIRANTE if estado == 2 else ALTO_TIRANTE - MUNON)
        ax, ay = x + ux * atado, y + uy * atado
        poste["atado"] = np.array([ax, ay, ctx.z(ax, ay) + 0.12])
        if estado == 2:
            return [_pieza("poste_tendido", x, y, z + 0.13, cae, 90.0 + baja)]
        return [_pieza("poste_tendido_partido", x, y, z, cae),
                _pieza("poste_tendido_punta", pie[0], pie[1], ctx.z(*pie) + 0.12, cae, 90.0 + baja)]
    # Sin sitio donde caer: queda el muñón (la punta se la llevaron para chatarra).
    poste["estado"] = 3
    poste["atado"] = np.array([x, y, z + MUNON - 0.2])
    return [_pieza("poste_tendido_partido", x, y, z, lejos)]


def _pieza(modelo: str, x: float, y: float, z: float, rumbo: float, cabeceo: float = 0.0,
           escala: float = 1.0) -> dict:
    return {"modelo": modelo, "pos": (round(x, 2), round(y, 2)), "z": round(z, 2),
            "rumbo": round(rumbo % 360.0), "cabeceo": round(cabeceo), "alabeo": 0, "escala": escala}


def _cable(tipo: str, puntos) -> dict:
    return {"tipo": tipo, "grosor": GROSOR[tipo],
            "puntos": [[round(float(x), 2), round(float(y), 2), round(float(z), 2)] for x, y, z in puntos]}


def _largo(puntos) -> float:
    a = np.asarray(puntos, float)
    return float(np.sum(np.linalg.norm(np.diff(a, axis=0), axis=1))) if len(a) > 1 else 0.0


def _arriba(poste: dict, alto: float) -> np.ndarray:
    """Un punto del poste a `alto` metros de su base (inclinado si está torcido)."""
    base = poste["base"]
    punto = base + np.array([0.0, 0.0, alto])
    if poste["estado"] == 1:
        return _inclinar(base, punto, poste["rumbo"], poste["inclina"])
    return punto


def _cables_apoyo(ctx: _Contexto, apoyo: dict) -> list[dict]:
    """El tirante (o la ménsula y su tornapunta) y las péndolas de un apoyo. Si perdió un
    poste, lo que queda del tirante cuelga hasta el suelo y los hilos no tienen de qué
    colgar (sus vanos se caen: _estado_vano)."""
    cables = []
    postes = apoyo["postes"]
    hilos = apoyo["hilos"]
    en_pie = [poste for poste in postes if poste["estado"] <= 1]
    if apoyo["tipo"] == "mensula":
        if not en_pie:
            return []
        poste = en_pie[0]
        z_brazo = max(float(h[2]) for h in hilos) + PENDOLA
        base = poste["base"]
        alto = min(z_brazo - float(base[2]), ALTO_POSTE - 0.3)
        lejano = max(hilos, key=lambda h: float(np.linalg.norm(h[:2] - base[:2])))
        hacia = (lejano[:2] - base[:2]) / (np.linalg.norm(lejano[:2] - base[:2]) or 1.0)
        punta_xy = lejano[:2] + hacia * 0.4
        brazo = [base + np.array([0.0, 0.0, alto]), np.array([*punta_xy, float(base[2]) + alto])]
        medio = brazo[0] + (brazo[1] - brazo[0]) * 0.6
        tornapunta = [base + np.array([0.0, 0.0, alto + 1.3]), medio]
        if poste["estado"] == 1:
            brazo = [_inclinar(base, q, poste["rumbo"], poste["inclina"]) for q in brazo]
            tornapunta = [_inclinar(base, q, poste["rumbo"], poste["inclina"]) for q in tornapunta]
        cables.append(_cable("mensula", brazo))
        cables.append(_cable("tornapunta", tornapunta))
        # Los hilos cuelgan de la ménsula: si el poste se torció, con ella.
        for i, h in enumerate(hilos):
            arriba = np.array([h[0], h[1], float(base[2]) + alto])
            if poste["estado"] == 1:
                arriba = _inclinar(base, arriba, poste["rumbo"], poste["inclina"])
                hilos[i] = arriba - np.array([0.0, 0.0, PENDOLA])
            cables.append(_cable("pendola", [arriba, hilos[i]]))
        return cables
    # Tirante entre dos postes: de uno al otro pasando por lo alto de cada péndola.
    a, b = sorted(postes, key=lambda poste: -poste["lado"])
    arribas = [h + np.array([0.0, 0.0, PENDOLA]) for h in hilos] + apoyo.get("extra", [])
    arribas.sort(key=lambda q: -float((q[:2] - apoyo["p"]) @ apoyo["n"]))
    # Caído o partido, el tirante sigue atado a lo que quedó en el suelo (o al muñón).
    extremos = [a["atado"], b["atado"]]
    if apoyo["valido"]:
        cables.append(_cable("tirante", [extremos[0], *arribas, extremos[1]]))
        for arriba in arribas:
            cables.append(_cable("pendola", [arriba, arriba - np.array([0.0, 0.0, PENDOLA])]))
        return cables
    if en_pie:
        # Solo queda un poste: el tirante cuelga de él hasta el suelo, hacia el otro.
        cables.append(_cable("tirante", _colgando(ctx, extremos[0] if a in en_pie else extremos[1],
                                                  extremos[1] if a in en_pie else extremos[0], 6.0)))
    return cables


def _colgando(ctx: _Contexto, desde: np.ndarray, hasta: np.ndarray, flecha: float, paso: float = 1.5):
    """Un cable flojo de `desde` a `hasta` con `flecha` metros de comba: donde llega al suelo,
    se apoya en él."""
    largo = float(np.linalg.norm(hasta[:2] - desde[:2]))
    n = max(2, int(math.ceil(largo / paso)))
    puntos = []
    for i in range(n + 1):
        u = i / n
        q = desde + (hasta - desde) * u
        z = float(q[2]) - flecha * 4.0 * u * (1.0 - u)
        puntos.append(np.array([q[0], q[1], max(z, ctx.z(float(q[0]), float(q[1])) + 0.03)]))
    return puntos


def _estado_vano(ctx: _Contexto, clave: str, a: dict, b: dict, w: int) -> int:
    """Cómo está el hilo `w` entre dos apoyos: 0 tenso, 1 roto, 2 caído. Sin uno de los dos
    apoyos, demasiado largo o sobre un hueco, no se sostiene."""
    rng = random.Random(_semilla(clave))
    pa, pb = a["hilos"][w], b["hilos"][w]
    largo = float(np.linalg.norm(pb[:2] - pa[:2]))
    tramo = LineString([pa[:2], pb[:2]])
    if tramo.intersects(ctx.huecos):
        return 1
    if not a["valido"] or not b["valido"] or largo > VANO_SIN_APOYO:
        return 1 if rng.random() < 0.6 else 2
    medio = (pa + pb) / 2.0
    return _elegir(rng, _mezcla(VANOS_LEJOS, VANOS_CERCA, float(medio[0]), float(medio[1])))


def _hilo(ctx: _Contexto, a: dict, b: dict, w: int, estado: int, tenso_antes: bool, tenso_despues: bool,
          rng: random.Random) -> list:
    """Los trozos del hilo `w` entre dos apoyos. Tenso: con su poca comba. Roto: cada mitad
    cuelga de su apoyo y lo que sobra queda en el suelo. Caído: se soltó de las péndolas y
    está en la calle; si el vano de al lado sigue tenso, todavía cuelga de ese apoyo."""
    pa, pb = a["hilos"][w], b["hilos"][w]
    largo = float(np.linalg.norm(pb[:2] - pa[:2]))
    if estado == 0:
        return [_colgando(ctx, pa, pb, 0.004 * largo + 0.05, 3.0)]
    if estado == 1:
        corte = rng.uniform(0.3, 0.7)
        trozos = []
        if a["valido"]:
            trozos.append(_roto(ctx, pa, pb, min(corte * largo, TROZO_MAX), rng))
        if b["valido"]:
            trozos.append(_roto(ctx, pb, pa, min((1.0 - corte) * largo, TROZO_MAX), rng))
        return trozos
    if a["valido"] and tenso_antes:
        return [_roto(ctx, pa, pb, largo, rng)]
    if b["valido"] and tenso_despues:
        return [_roto(ctx, pb, pa, largo, rng)]
    return [_tirado(ctx, pa[:2], pb[:2], rng)]


def _tirado(ctx: _Contexto, desde: np.ndarray, hasta: np.ndarray, rng: random.Random) -> list:
    """Un hilo en el suelo de `desde` a `hasta`, con alguna onda."""
    u = hasta - desde
    largo = float(np.linalg.norm(u))
    u /= largo or 1.0
    lado = np.array([-u[1], u[0]])
    n = max(2, int(math.ceil(largo / 1.5)))
    puntos = []
    for i in range(n + 1):
        q = desde + u * largo * i / n + lado * (rng.uniform(-0.25, 0.25) if 0 < i < n else 0.0)
        puntos.append(np.array([q[0], q[1], ctx.z(float(q[0]), float(q[1])) + 0.03]))
    return puntos


def _roto(ctx: _Contexto, desde: np.ndarray, hacia: np.ndarray, largo: float, rng: random.Random):
    """Un trozo de hilo roto que cuelga de `desde`: baja casi a plomo, se tumba al llegar al
    suelo (una J, hacia `hacia`) y sigue tirado lo que le quede de largo, con alguna onda.
    Si no llega al suelo (sobre un hueco, o es corto), cuelga en el aire."""
    u = hacia[:2] - desde[:2]
    u /= np.linalg.norm(u) or 1.0
    lado = np.array([-u[1], u[0]])
    suelo = ctx.z(float(desde[0]), float(desde[1]))
    caida = float(desde[2]) - suelo
    puntos = [desde]
    if largo <= caida:
        for i in range(1, 7):
            f = i / 6
            q = desde[:2] + u * min(0.6, largo * 0.15) * (1.0 - math.cos(f * math.pi / 2))
            puntos.append(np.array([q[0], q[1], float(desde[2]) - largo * math.sin(f * math.pi / 2)]))
        return puntos
    sale = min(1.2, (largo - caida) * 0.5)
    for i in range(1, 7):
        f = i / 6
        q = desde[:2] + u * sale * (1.0 - math.cos(f * math.pi / 2))
        z = float(desde[2]) - caida * math.sin(f * math.pi / 2)
        puntos.append(np.array([q[0], q[1], max(z, ctx.z(float(q[0]), float(q[1])) + 0.03)]))
    resto = largo - caida - sale
    andado = 0.0
    q = desde[:2] + u * sale
    while andado < resto:
        paso = min(1.5, resto - andado)
        andado += paso
        q = q + u * paso + lado * rng.uniform(-0.2, 0.2)
        puntos.append(np.array([q[0], q[1], ctx.z(float(q[0]), float(q[1])) + 0.03]))
    return puntos
