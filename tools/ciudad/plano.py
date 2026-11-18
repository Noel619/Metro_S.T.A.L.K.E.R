"""Genera el plano de Tumansk a partir de datos.py.

Uso: python3 tools/ciudad/plano.py [--solo-datos | --comprobar] [--plano=general|subsuelo|peligros|rutas]

--comprobar  valida y exporta los datos; termina con error si hay problemas (lo usa la CI).
--solo-datos valida y exporta los datos, sin dibujar.
--plano=...  dibuja solo ese plano (se puede repetir).

1. Valida los datos: edificios dentro del mapa, fuera del río y de las calles, sin
   solaparse y en la zona que dicen.
2. Calcula el daño de cada edificio (distancia a la Zona Cero, con variación fija
   por edificio), los incendios y los escombros que caen a la calle.
3. Calcula el relieve con los terraplenes, las calles de la loma niveladas, los
   escombros, la cubeta de los socavones (deterioro.py) y las explanadas de los edificios
   con modelo propio, y la cota de cada edificio.
4. Traza la red de tránsito (transito.py): calzadas, aceras, bordillos, escaleras, el
   tablero del puente, pasos de cebra… con sus alturas, y su deterioro (deterioro.py):
   socavones, grietas, baches, tapas abiertas, bordillos rotos y matojos.
5. Exporta data/ciudad/plano.json, data/ciudad/relieve.png (16 bits), la rasante del
   tránsito (data/ciudad/rasante.png), la red de tránsito (data/ciudad/transito.json) y el
   suelo de la maqueta, data/ciudad/suelo.png.
6. Dibuja los planos de desarrollo en docs/ciudad/.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))

import datos as D  # noqa: E402
import relieve as R  # noqa: E402
import ferrocarril as F  # noqa: E402
import vias as V  # noqa: E402
import deterioro as DT  # noqa: E402
import transito as T  # noqa: E402
from geo import ALTO, ANCHO, SECTOR, banda, coords, distancia, sector_de  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
SALIDA_DATOS = RAIZ / "data" / "ciudad"
SALIDA_DOCS = RAIZ / "docs" / "ciudad"

NIVELES_DANO = {
    1: ("Herido", "Sin cristales, hollín de incendios, balcones y paneles caídos, cubiertas cedidas por la nieve"),
    2: ("Roto", "Derrumbes parciales (una esquina, las últimas plantas), fachadas abiertas, montones de escombro"),
    3: ("Destripado", "Cascarón: la mayoría de los forjados caídos; quedan muros y estructura; calles cegadas"),
    4: ("Arrasado", "Muñones de una o dos plantas y campos de escombros"),
}
ANILLOS_DANO = [(400.0, 4), (800.0, 3), (1250.0, 2)]


def azar(clave: str) -> float:
    """Número fijo entre 0 y 1 para cada clave (no cambia entre ejecuciones)."""
    return int(hashlib.md5(clave.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Daños, incendios y escombros
# ---------------------------------------------------------------------------
def calcular_danos() -> None:
    for e in D.EDIFICIOS:
        c = e["huella"].centroid
        d = distancia((c.x, c.y), D.GZ)
        e["distancia_gz"] = round(d, 1)
        if e["dano"] is None:
            base = 1
            for radio, nivel in ANILLOS_DANO:
                if d < radio:
                    base = nivel
                    break
            r = azar(e["id"] + "/dano")
            if r < 0.15 and d > 450:
                base -= 1
            elif r > 0.82:
                base += 1
            if D.TIPOS[e["tipo"]]["grupo"] == "madera" and d < 1300:
                base += 1
            e["dano"] = int(min(4, max(1, base)))
        if e["incendio"] is None:
            r = azar(e["id"] + "/fuego")
            grupo = D.TIPOS[e["tipo"]]["grupo"]
            if grupo == "madera":
                e["incendio"] = "total" if r < 0.6 else "parcial"
            elif grupo in ("menor", "industria") and e["tipo"] != "nave":
                e["incendio"] = "no"
            else:
                umbral_total = {1: 0.04, 2: 0.10, 3: 0.20, 4: 0.5}[e["dano"]]
                umbral_parcial = {1: 0.35, 2: 0.55, 3: 0.75, 4: 1.0}[e["dano"]]
                e["incendio"] = "total" if r < umbral_total else ("parcial" if r < umbral_parcial else "no")


def calcular_escombros() -> list[dict]:
    """Los escombros caen hacia fuera de la Zona Cero: la onda empujó las fachadas, así que
    el montón queda del lado contrario a la bomba (y cubre la calle si la hay)."""
    from shapely import affinity

    escombros = []
    for e in D.EDIFICIOS:
        if e["dano"] < 2 or D.TIPOS[e["tipo"]]["grupo"] in ("menor",) or e["tipo"] in ("chimenea", "torre", "muralla"):
            continue
        if e["id"] in D.MODELO_PROPIO:
            continue  # su modelo trae su escombro
        huella = e["huella"]
        c = huella.centroid
        dx, dy = c.x - D.GZ[0], c.y - D.GZ[1]
        largo = math.hypot(dx, dy) or 1.0
        ux, uy = dx / largo, dy / largo
        h = e["altura"]
        r = azar(e["id"] + "/escombro")
        if e["dano"] == 2:
            if r > 0.45:
                continue
            alcance, alto = min(9.0, 0.16 * h), 0.12 * h
        elif e["dano"] == 3:
            alcance, alto = min(20.0, 0.3 * h), 0.2 * h
        else:
            alcance, alto = min(26.0, 0.45 * h + 5.0), 0.3 * h + 1.5
        barrido = unary_union([affinity.translate(huella, ux * alcance * f, uy * alcance * f) for f in (0.3, 0.6, 1.0)])
        forma = barrido.buffer(1.5).difference(huella.buffer(0.5))
        if e["dano"] == 4:
            forma = unary_union([forma, huella])
        forma = forma.difference(D.RIO).simplify(0.4)
        if forma.is_empty or forma.area < 8:
            continue
        alto = min(alto, {2: 3.0, 3: 6.0, 4: 9.0}[e["dano"]])
        escombros.append({"edificio": e["id"], "forma": forma, "alto": round(max(0.8, alto), 1), "dano": e["dano"]})
    return escombros


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------
TOLERANCIA_CALLE = {"quiosco", "tienda_campana", "torre", "pabellon"}
SIN_VALIDAR_CALLE = {"PLZ-06", "IND-G1", "IND-G2", "IND-G3", "IND-G4", "CEN-FLU", "CEN-FLUT", "BLQ-PLY", "AVM-18", "IND-35",
                     "IND-32B", "PLZ-24"}


def calles_poligono():
    return D.CALLES_UNION


def validar(calles) -> list[str]:
    problemas = []
    mapa = Point(ANCHO / 2, ALTO / 2).buffer(1).envelope.buffer(0)
    del mapa
    huellas = [e["huella"] for e in D.EDIFICIOS]
    arbol = STRtree(huellas)
    vistos = set()
    ids = set()
    for i, e in enumerate(D.EDIFICIOS):
        h = e["huella"]
        if e["id"] in ids:
            problemas.append(f"{e['id']}: identificador repetido")
        ids.add(e["id"])
        if not h.is_valid or h.area < 1.0:
            problemas.append(f"{e['id']}: huella no válida (área {h.area:.1f})")
            continue
        minx, miny, maxx, maxy = h.bounds
        if minx < -2 or miny < -2 or maxx > ANCHO + 2 or maxy > ALTO + 2:
            problemas.append(f"{e['id']}: se sale del mapa {h.bounds}")
        agua = h.intersection(D.RIO).area
        if agua > 0.05 * h.area and e["id"] not in SIN_VALIDAR_CALLE:
            problemas.append(f"{e['id']} ({e['nombre']}): {agua:.0f} m² dentro del río")
        if e["tipo"] not in TOLERANCIA_CALLE and e["id"] not in SIN_VALIDAR_CALLE:
            en_calle = h.intersection(calles).area
            if en_calle > max(4.0, 0.03 * h.area):
                problemas.append(f"{e['id']} ({e['nombre']}): {en_calle:.0f} m² sobre la calle")
        for j in arbol.query(h):
            j = int(j)
            if j == i or (min(i, j), max(i, j)) in vistos:
                continue
            vistos.add((min(i, j), max(i, j)))
            otro = D.EDIFICIOS[j]
            comun = h.intersection(otro["huella"]).area
            if comun > 2.0:
                problemas.append(f"{e['id']} y {otro['id']} se solapan {comun:.0f} m²")
        c = h.representative_point()
        zona = D.zona_de(c.x, c.y)
        if zona != e["zona"]:
            problemas.append(f"{e['id']} ({e['nombre']}): dice zona {e['zona']} pero está en la {zona}")
    return problemas


# ---------------------------------------------------------------------------
# Relieve
# ---------------------------------------------------------------------------
def rasterizar(formas_y_valores, res: float, nx: int, ny: int) -> np.ndarray:
    from PIL import Image, ImageDraw

    capa = Image.new("F", (nx, ny), 0.0)
    dibujo = ImageDraw.Draw(capa)
    for forma, valor in formas_y_valores:
        geoms = forma.geoms if forma.geom_type == "MultiPolygon" else [forma]
        for g in geoms:
            puntos = [(x / res, (ALTO - y) / res) for x, y in g.exterior.coords]
            dibujo.polygon(puntos, fill=float(valor))
    return np.flipud(np.array(capa))


def suavizar(a: np.ndarray, radio: int) -> np.ndarray:
    """Desenfoque de caja separable (dos pasadas) sin scipy."""
    for _ in range(2):
        for eje_ in (0, 1):
            c = np.cumsum(np.pad(a, [(radio + 1, radio) if k == eje_ else (0, 0) for k in range(2)], mode="edge"), axis=eje_)
            if eje_ == 0:
                a = (c[2 * radio + 1 :, :] - c[: -2 * radio - 1, :]) / (2 * radio + 1)
            else:
                a = (c[:, 2 * radio + 1 :] - c[:, : -2 * radio - 1]) / (2 * radio + 1)
    return a


def calcular_relieve(escombros: list[dict], res: float = 2.0) -> tuple[np.ndarray, np.ndarray, dict]:
    """El relieve (lo que se ve: con los escombros), el terreno (sin ellos) y las rasantes
    de las vías del tren. El relieve y el terreno llevan las vías niveladas (con sus
    terraplenes y trincheras) y las calles de la falda de la loma."""
    nx, ny = int(ANCHO / res), int(ALTO / res)
    xs = (np.arange(nx) + 0.5) * res
    ys = (np.arange(ny) + 0.5) * res
    gx, gy = np.meshgrid(xs, ys)
    h = R.altura_natural(gx, gy)
    ferro = F.perfiles(h, res)
    terreno = T.nivelar(h, res, ferro)
    montones = rasterizar([(e["forma"], e["alto"]) for e in escombros], res, nx, ny)
    return terreno + suavizar(montones, max(1, int(4 / res))), terreno, ferro


def muestrear(h: np.ndarray, res: float, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Altura bilineal en puntos del mapa. h[j, i] es la altura del centro de la celda
    ((i + 0,5)·res, (j + 0,5)·res): la fila 0 es el borde sur."""
    fx = np.clip(np.asarray(xs, float) / res - 0.5, 0.0, h.shape[1] - 1.0001)
    fy = np.clip(np.asarray(ys, float) / res - 0.5, 0.0, h.shape[0] - 1.0001)
    i0 = np.floor(fx).astype(int)
    j0 = np.floor(fy).astype(int)
    tx = fx - i0
    ty = fy - j0
    return (h[j0, i0] * (1 - tx) * (1 - ty) + h[j0, i0 + 1] * tx * (1 - ty)
            + h[j0 + 1, i0] * (1 - tx) * ty + h[j0 + 1, i0 + 1] * tx * ty)


def calcular_cotas(terreno: np.ndarray, res: float) -> None:
    """Cota de cada edificio: la altura del terreno sin escombros bajo su huella.

    `cota` (la mediana) es el nivel de la planta baja; `cota_min` (el punto más bajo de la
    huella), hasta dónde bajan los muros en las laderas. Se mide sin los montones de
    escombros porque el escombro cae encima: un muñón queda medio enterrado en el suyo."""
    for e in D.EDIFICIOS:
        h = e["huella"]
        minx, miny, maxx, maxy = h.bounds
        gx, gy = np.meshgrid(np.arange(minx + 1.0, maxx, 2.0), np.arange(miny + 1.0, maxy, 2.0))
        dentro = shapely.contains_xy(h, gx.ravel(), gy.ravel())
        borde = np.array(h.exterior.coords)
        xs = np.concatenate([gx.ravel()[dentro], borde[:, 0]])
        ys = np.concatenate([gy.ravel()[dentro], borde[:, 1]])
        alturas = muestrear(terreno, res, xs, ys)
        e["cota"] = round(float(np.median(alturas)), 2)
        e["cota_min"] = round(float(alturas.min()), 2)


def explanar(capas: list[np.ndarray], res: float) -> list[np.ndarray]:
    """Las explanadas de los edificios con modelo propio (D.EXPLANADAS): el terreno, a la cota
    del edificio bajo su huella y su margen, y de vuelta a su altura en la transición (con
    una curva suave). Las capas son rejillas como las de calcular_relieve (la fila 0 al sur)."""
    resultado = [c.copy() for c in capas]
    ny, nx = resultado[0].shape
    for e in D.EDIFICIOS:
        if e["id"] not in D.EXPLANADAS:
            continue
        margen, transicion = D.EXPLANADAS[e["id"]]
        alcance = margen + transicion
        # Con lo que haya en sus patios cerrados (la torre en medio de los Sóviets).
        llena = shapely.Polygon(e["huella"].exterior)
        minx, miny, maxx, maxy = llena.bounds
        i0, i1 = max(0, int((minx - alcance) / res)), min(nx, int((maxx + alcance) / res) + 1)
        j0, j1 = max(0, int((miny - alcance) / res)), min(ny, int((maxy + alcance) / res) + 1)
        gx, gy = np.meshgrid((np.arange(i0, i1) + 0.5) * res, (np.arange(j0, j1) + 0.5) * res)
        lejos = shapely.distance(llena, shapely.points(gx.ravel(), gy.ravel())).reshape(gx.shape)
        t = np.clip((lejos - margen) / transicion, 0.0, 1.0)
        llano = 1.0 - t * t * (3.0 - 2.0 * t)
        for capa in resultado:
            capa[j0:j1, i0:i1] += (e["cota"] - capa[j0:j1, i0:i1]) * llano
    return resultado


# ---------------------------------------------------------------------------
# Suelo de la maqueta
# ---------------------------------------------------------------------------
# Color del suelo bajo la nieve (RGB) y cuánta nieve lo cubre (A: 0 nada, 255 todo).
# La nieve es vieja y nunca blanca: la pone el shader del suelo encima de este color.
SUELO: dict[str, tuple[int, int, int, int]] = {
    "tierra": (98, 92, 82, 235),
    "parque": (100, 98, 80, 245),
    "ladera": (90, 86, 72, 225),
    "arena": (138, 126, 104, 215),
    "hielo": (118, 130, 134, 105),
    "acera": (116, 112, 104, 200),
    "calzada": (60, 58, 56, 150),
    "mediana": (96, 94, 84, 235),
    "plaza": (124, 118, 108, 185),
    "camino": (104, 92, 76, 205),
    "via": (52, 48, 46, 80),
    "tranvia": (46, 44, 42, 120),
    "escombros": (88, 80, 72, 115),
    "juegos": (140, 120, 90, 205),
    "pista": (96, 100, 90, 225),
    "hockey": (168, 178, 180, 60),
    "basuras": (58, 56, 52, 130),
    "aparcamiento": (90, 88, 84, 190),
    "carbon": (30, 28, 28, 0),
    "cementerio": (104, 100, 84, 240),
    "patio_transformadores": (110, 108, 102, 180),
    "acero": (92, 88, 84, 150),
    "huerto": (96, 84, 66, 230),
}
ANCHO_VIA = {"principal": 7.0, "secundaria": 3.6, "playa": 3.2}


def ancho_acera(c: dict) -> float:
    """Aceras de una calle: las da su calzada si la tiene; los pasos de servicio no tienen."""
    if c["tipo"] == "servicio":
        return 0.0
    if "calzada" in c:
        return (c["ancho"] - c["calzada"]) / 2.0
    return min(5.0, max(2.0, round(c["ancho"] * 0.2, 1)))


def exportar_suelo(escombros: list[dict], res: float = 1.0) -> dict:
    """Pinta el suelo de la maqueta (data/ciudad/suelo.png), capa a capa y sin suavizar."""
    from PIL import Image, ImageDraw

    from geo import banda, circulo

    nx, ny = int(ANCHO / res), int(ALTO / res)
    img = Image.new("RGBA", (nx, ny), SUELO["tierra"])

    def pts(anillo) -> list[tuple[float, float]]:
        return [(x / res, (ALTO - y) / res) for x, y in anillo]

    def pintar(formas, clase: str) -> None:
        mascara = Image.new("L", (nx, ny), 0)
        d = ImageDraw.Draw(mascara)
        for forma in formas:
            partes = forma.geoms if forma.geom_type in ("MultiPolygon", "GeometryCollection") else [forma]
            for g in partes:
                if g.geom_type != "Polygon" or g.is_empty:
                    continue
                d.polygon(pts(g.exterior.coords), fill=255)
                for hueco in g.interiors:
                    d.polygon(pts(hueco.coords), fill=0)
        img.paste(SUELO[clase], None, mascara)

    verdes = D.ZONAS_VERDES
    pintar([verdes["parque"], verdes["hospital"]], "parque")
    pintar([verdes["barranco"]], "ladera")
    pintar([verdes["playa"]], "arena")
    pintar([D.RIO, D.ESTANQUE], "hielo")
    for clase in SUELO:
        formas = [p["forma"] for p in D.PATIOS if p["tipo"] == clase]
        if formas:
            pintar(formas, clase)
    # Las calles, las plazas, las sendas y el camino no se pintan: la maqueta los levanta
    # con sus propios materiales (data/ciudad/transito.json) y el terreno de debajo no se ve.
    # Las vías y el tranvía cruzan el río por los puentes: sobre el hielo no se pintan.
    pintar([banda(v["puntos"], ANCHO_VIA[v["tipo"]]).difference(D.RIO) for v in D.VIAS], "via")
    pintar([e["forma"] for e in escombros], "escombros")
    img.save(SALIDA_DATOS / "suelo.png")
    return {"archivo": "suelo.png", "resolucion": res, "filas": "la primera fila es el borde norte",
            "canales": "RGB: color del suelo bajo la nieve; A: cuánta nieve lo cubre (0 nada, 255 todo)",
            "clases": {k: list(v) for k, v in SUELO.items()}}


def exportar_relieve(h: np.ndarray, res: float, archivo: str = "relieve.png") -> dict:
    from PIL import Image

    codigo = np.clip(np.round((h + 50.0) * 100.0), 0, 65535).astype(np.uint16)
    Image.fromarray(np.flipud(codigo)).save(SALIDA_DATOS / archivo)
    return {"archivo": archivo, "resolucion": res, "codificacion": "metros = valor / 100 - 50",
            "filas": "la primera fila es el borde norte", "min": round(float(h.min()), 2), "max": round(float(h.max()), 2)}


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def huella_exportable(huella) -> list:
    """Coordenadas de una huella para plano.json. Al redondearlas a 0,1 m, alguna huella
    recortada contra su manzana queda con astillas (tiras de centímetros) que se cruzan:
    esas se limpian quitando las tiras de menos de medio metro y se ajustan a la rejilla
    de 0,1 m sin perder la validez. Las demás se exportan tal cual."""
    from shapely.geometry import Polygon

    anillos = coords(huella)
    if Polygon(anillos[0], anillos[1:]).is_valid:
        return anillos
    limpia = huella.buffer(-0.25, join_style=2).buffer(0.25, join_style=2)
    if limpia.geom_type == "MultiPolygon":
        limpia = max(limpia.geoms, key=lambda g: g.area)
    limpia = shapely.set_precision(limpia, 0.1)
    if limpia.geom_type == "MultiPolygon":
        limpia = max(limpia.geoms, key=lambda g: g.area)
    return coords(limpia)


def exportar_arbol(a: dict) -> dict:
    registro = {"pos": (round(a["pos"][0], 1), round(a["pos"][1], 1)), "estado": a["estado"]}
    if a.get("z") is not None:
        registro["z"] = a["z"]
    if a["estado"] == "tumbado":
        registro["rumbo"] = round(a["rumbo"], 1)
    else:
        registro["copa"] = round(a["copa"], 2)
    return registro


# Vehículos que van sobre los carriles del tren (si no están volcados, en lo alto del carril).
SOBRE_CARRILES = ("vagon", "coche_tren", "locomotora")


def alturas_en_el_transito(trazado, alturas) -> None:
    """La altura de lo que pisan los árboles y los vehículos que están en el tránsito (una
    acera, un alcorque, el tablero del puente, el fondo de un socavón…) o sobre una vía del
    tren (lo alto del carril); los demás, la sacan del relieve."""
    for lista in (D.ARBOLES, D.VEHICULOS):
        for cosa in lista:
            x, y = cosa["pos"]
            if cosa.get("tipo") in SOBRE_CARRILES and cosa.get("estado") != "volcado":
                carril = F.carril_en(alturas.ferrocarril, x, y)
                if carril is not None:
                    cosa["z"] = round(carril, 3)
                    continue
            grupo = T._grupo_en(trazado, x, y)
            if grupo is None:
                cosa.pop("z", None)
                continue
            z = float(alturas.z(trazado.grupos[grupo], [x], [y])[0])
            if trazado.grupos[grupo].clase == "socavon":
                # En el fondo de un socavón (el terreno de encima ya no está).
                cosa["z"] = round(z, 3)
                continue
            cosa["z"] = round(max(z, float(alturas.terreno([x], [y])[0])), 3)


def exportar_json(escombros: list[dict], meta_relieve: dict, meta_suelo: dict, calles, meta_transito: dict) -> dict:
    def pts(lista):
        return [(round(x, 1), round(y, 1)) for x, y in lista]

    edificios = []
    for e in D.EDIFICIOS:
        c = e["huella"].centroid
        registro = {k: v for k, v in e.items() if k not in ("huella",)}
        registro["sector"] = sector_de(c.x, c.y)
        registro["centro"] = (round(c.x, 1), round(c.y, 1))
        registro["superficie"] = round(e["huella"].area, 1)
        registro["huella"] = huella_exportable(e["huella"])
        edificios.append(registro)
    estadisticas = {
        "edificios": len(D.EDIFICIOS),
        "edificios_por_zona": {str(z): sum(1 for e in D.EDIFICIOS if e["zona"] == z) for z in D.ZONAS},
        "edificios_por_dano": {str(n): sum(1 for e in D.EDIFICIOS if e["dano"] == n) for n in NIVELES_DANO},
        "viviendas_que_se_recorren": sum(1 for e in D.EDIFICIOS if D.TIPOS[e["tipo"]]["grupo"] == "vivienda"),
        "edificios_con_interior": sum(1 for e in D.EDIFICIOS if e["interior"] != "ninguno"),
        "interiores_a_mano": sum(1 for e in D.EDIFICIOS if e["interior"] == "a_mano"),
        "vehiculos": len(D.VEHICULOS),
        "patios": len(D.PATIOS),
        "superficie_construida_m2": round(sum(e["huella"].area for e in D.EDIFICIOS)),
        "superficie_util_m2": round(sum(e["huella"].area * e["pisos"] for e in D.EDIFICIOS if e["interior"] != "ninguno")),
        "km_de_calles": round(sum(banda(c["puntos"], 1).length / 2 / 1000 for c in D.CALLES if c["tipo"] not in ("puente",)), 1),
        "superficie_calles_m2": round(calles.area),
    }
    plano = {
        "version": 1,
        "unidades": "metros; x hacia el este, y hacia el norte; origen en la esquina suroeste",
        "tamano": [ANCHO, ALTO],
        "sector": SECTOR,
        "eje_monumental": {"origen": (430.0, 330.0), "angulo": 48.0},
        "zona_cero": D.GZ,
        "niveles_dano": {str(k): {"nombre": v[0], "descripcion": v[1]} for k, v in NIVELES_DANO.items()},
        "tipos": D.TIPOS,
        "zonas": {str(k): {**v, "poligono": coords(D.ZONA_POLIGONOS[k]) if k in D.ZONA_POLIGONOS else None} for k, v in D.ZONAS.items()},
        "rio": {"nombre": "Tumán", "eje": D.R.RIO_EJE, "poligono": coords(D.RIO), "hielo": D.R.NIVEL_HIELO},
        "relieve": meta_relieve,
        "suelo": meta_suelo,
        "transito": meta_transito,
        "calles": [{**c, "puntos": pts(c["puntos"])} for c in D.CALLES],
        "plazas": [{**{k: v for k, v in p.items() if k != "forma"}, "forma": coords(p["forma"])} for p in D.PLAZAS],
        "vias": [{"id": v["id"], "nombre": v["nombre"], "tipo": v["tipo"], "puntos": pts(v["puntos"])}
                 for v in D.VIAS],
        "puente_ferrocarril": D.PUENTE_FERROCARRIL,
        "terraplenes": D.TERRAPLENES,
        "tranvias": [{**t, "puntos": pts(t["puntos"])} for t in D.TRANVIAS],
        "trolebuses": [{**t, "puntos": pts(t["puntos"])} for t in D.TROLEBUSES],
        "tuberias": D.TUBERIAS,
        "edificios": edificios,
        "escombros": [{**{k: v for k, v in e.items() if k != "forma"}, "forma": coords(e["forma"])} for e in escombros],
        "hitos": {str(k): {**v, "pos": pts([v["pos"]])[0]} for k, v in D.HITOS.items()},
        "puntos": D.PUNTOS,
        "metro": {
            "lineas": [{**l, "puntos": pts(l["puntos"])} for l in D.METRO_LINEAS],
            "estaciones": [{**{k: v for k, v in s.items() if k != "forma"}, "pos": pts([s["pos"]])[0], "forma": coords(s["forma"])} for s in D.METRO_ESTACIONES],
            "rejas": [{**r, "pos": pts([r["pos"]])[0]} for r in D.METRO_REJAS],
            "pozos": [{**p, "pos": pts([p["pos"]])[0]} for p in D.POZOS],
            "inundado": [{**t, "puntos": pts(t["puntos"])} for t in D.TRAMOS_INUNDADOS],
            "hundido": [{**t, "puntos": pts(t["puntos"])} for t in D.TRAMOS_HUNDIDOS],
        },
        "subsuelo": [{**s, "puntos": pts(s["puntos"])} for s in D.SUBSUELO],
        "amenazas": [{**{k: v for k, v in a.items() if k != "territorio"}, "guarida": pts([a["guarida"]])[0], "territorio": coords(a["territorio"])} for a in D.AMENAZAS],
        "patrullas": [{**p, "puntos": pts(p["puntos"])} for p in D.PATRULLAS],
        "vigias": [{**v, "pos": pts([v["pos"]])[0]} for v in D.VIGIAS],
        "peligros": {
            "rastro_radiactivo": [{"nivel": r["nivel"], "forma": coords(r["forma"])} for r in D.RASTRO_RADIACTIVO],
            "focos": [{**f, "pos": pts([f["pos"]])[0]} for f in D.FOCOS_RADIACION],
            "mascara": [{"nombre": m["nombre"], "forma": coords(m["forma"])} for m in D.ZONAS_MASCARA],
            "hielo_fino": [{"nombre": m["nombre"], "forma": coords(m["forma"])} for m in D.HIELO_FINO],
            "anillos_dano": [{"radio": r, "nivel": n} for r, n in ANILLOS_DANO],
        },
        "cruces_rio": [{**c, "pos": pts([c["pos"]])[0]} for c in D.CRUCES_RIO],
        "limites": D.LIMITES,
        "rutas": [{**r, "puntos": pts(r["puntos"]), "metros": round(banda(r["puntos"], 1).length / 2)} for r in D.RUTAS],
        "patios": [{**{k: v for k, v in p.items() if k != "forma"}, "forma": coords(p["forma"])} for p in D.PATIOS],
        "vallas": [{**v, "puntos": pts(v["puntos"])} for v in D.VALLAS],
        "sendas": [{**s, "puntos": pts(s["puntos"])} for s in D.SENDAS],
        "arboles": [exportar_arbol(a) for a in D.ARBOLES],
        "vehiculos": D.VEHICULOS,
        "medidas_vehiculos": D.MEDIDAS,
        "lineas_electricas": D.LINEAS_ELECTRICAS,
        "estadisticas": estadisticas,
    }
    texto = json.dumps(plano, ensure_ascii=False, separators=(",", ":"))
    (SALIDA_DATOS / "plano.json").write_text(texto, encoding="utf-8")
    return estadisticas


def main() -> int:
    SALIDA_DATOS.mkdir(parents=True, exist_ok=True)
    SALIDA_DOCS.mkdir(parents=True, exist_ok=True)
    # El trazado final de las vías (desvíos y curvas) antes que nada: lo usan el relieve,
    # el tránsito, el suelo y los planos. Pone también los vagones de la playa.
    V.red()
    calles = calles_poligono()
    problemas = validar(calles)
    calcular_danos()
    escombros = calcular_escombros()
    relieve, terreno, ferro = calcular_relieve(escombros, 2.0)
    # La calle se hunde alrededor de cada socavón (la cubeta): el terreno, el relieve y, con
    # el terreno, la rasante del tránsito.
    relieve, terreno = DT.hundir([relieve, terreno], 2.0)
    calcular_cotas(terreno, 2.0)
    # Los edificios con modelo propio, en su explanada a su cota (y otra vez las cotas: las
    # de sus vecinos pueden cambiar).
    relieve, terreno = explanar([relieve, terreno], 2.0)
    calcular_cotas(terreno, 2.0)
    planta = T.trazar()
    rasante_calles = T.rasante_transito(terreno, 2.0)
    # Lo pavimentado, también donde la calle está rota o hundida (el relieve no depende de ello).
    pavimento = unary_union(list(planta.superficies.values()) + [z.contorno for z in planta.firmes] + [DT.huecos()])
    pasos = F.cruces(ferro, pavimento)
    rasante = F.subir_pasos(rasante_calles, 2.0, pasos, T.NIVEL_CALZADA)
    # El terreno sube con la calle junto a los pasos a nivel (su terraplén).
    terreno = F.subir_terreno(terreno, 2.0, rasante_calles, rasante, pavimento, T.NIVEL_PEATON)
    relieve = F.subir_terreno(relieve, 2.0, rasante_calles, rasante, pavimento, T.NIVEL_PEATON)
    alturas = T.Alturas(rasante, relieve, terreno, 2.0, ferro)
    trazado = T.trazar_completo(alturas, planta)
    problemas += T.comprobar(trazado, alturas)
    # Lo que estaba encima de un socavón cae dentro (antes de darle su altura).
    DT.hundir_vehiculos()
    alturas_en_el_transito(trazado, alturas)
    meta = exportar_relieve(relieve, 2.0)
    exportar_relieve(rasante, 2.0, "rasante.png")
    meta_transito = {"archivo": "transito.json", **T.exportar(trazado, alturas, SALIDA_DATOS)}
    meta_suelo = exportar_suelo(escombros, 1.0)
    estadisticas = exportar_json(escombros, meta, meta_suelo, calles, meta_transito)
    print(json.dumps(estadisticas, ensure_ascii=False, indent=1))
    if problemas:
        print(f"\n{len(problemas)} problemas:")
        for p in problemas:
            print("  -", p)
    if "--comprobar" in sys.argv:
        return 1 if problemas else 0
    if "--solo-datos" in sys.argv:
        return 0
    import dibujo

    solo = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--plano=")]
    dibujo.TERRENO = terreno
    dibujo.dibujar_todo(relieve, 2.0, escombros, calles, SALIDA_DOCS, solo or None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
