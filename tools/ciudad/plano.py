"""Genera el plano de Tumansk a partir de datos.py.

Uso: python3 tools/ciudad/plano.py [--solo-datos | --comprobar] [--plano=general|subsuelo|peligros|rutas]

--comprobar  valida y exporta los datos; termina con error si hay problemas (lo usa la CI).
--solo-datos valida y exporta los datos, sin dibujar.
--plano=...  dibuja solo ese plano (se puede repetir).

1. Valida los datos: edificios dentro del mapa, fuera del río y de las calles, sin
   solaparse y en la zona que dicen.
2. Calcula el daño de cada edificio (distancia a la Zona Cero, con variación fija
   por edificio), los incendios y los escombros que caen a la calle.
3. Calcula el relieve con los terraplenes y los escombros.
4. Exporta data/ciudad/plano.json y data/ciudad/relieve.png (16 bits).
5. Dibuja los planos de desarrollo en docs/ciudad/.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import STRtree
from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))

import datos as D  # noqa: E402
import relieve as R  # noqa: E402
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


def calcular_relieve(escombros: list[dict], res: float = 2.0) -> np.ndarray:
    nx, ny = int(ANCHO / res), int(ALTO / res)
    xs = (np.arange(nx) + 0.5) * res
    ys = (np.arange(ny) + 0.5) * res
    gx, gy = np.meshgrid(xs, ys)
    h = R.altura_natural(gx, gy)
    for t in D.TERRAPLENES:
        h = h + R.terraplen(gx, gy, t["puntos"], t["alto"], t["corona"], t["talud"])
    terreno = h.copy()
    montones = rasterizar([(e["forma"], e["alto"]) for e in escombros], res, nx, ny)
    h = h + suavizar(montones, max(1, int(4 / res)))
    return h, terreno


def exportar_relieve(h: np.ndarray, res: float) -> dict:
    from PIL import Image

    codigo = np.clip((h + 50.0) * 100.0, 0, 65535).astype(np.uint16)
    Image.fromarray(np.flipud(codigo)).save(SALIDA_DATOS / "relieve.png")
    return {"archivo": "relieve.png", "resolucion": res, "codificacion": "metros = valor / 100 - 50",
            "filas": "la primera fila es el borde norte", "min": round(float(h.min()), 2), "max": round(float(h.max()), 2)}


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def exportar_json(escombros: list[dict], meta_relieve: dict, calles) -> dict:
    def pts(lista):
        return [(round(x, 1), round(y, 1)) for x, y in lista]

    edificios = []
    for e in D.EDIFICIOS:
        c = e["huella"].centroid
        registro = {k: v for k, v in e.items() if k not in ("huella",)}
        registro["sector"] = sector_de(c.x, c.y)
        registro["centro"] = (round(c.x, 1), round(c.y, 1))
        registro["superficie"] = round(e["huella"].area, 1)
        registro["huella"] = coords(e["huella"])
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
        "calles": [{**c, "puntos": pts(c["puntos"])} for c in D.CALLES],
        "plazas": [{**{k: v for k, v in p.items() if k != "forma"}, "forma": coords(p["forma"])} for p in D.PLAZAS],
        "vias": [{**v, "puntos": pts(v["puntos"])} for v in D.VIAS],
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
        "vehiculos": D.VEHICULOS,
        "lineas_electricas": D.LINEAS_ELECTRICAS,
        "estadisticas": estadisticas,
    }
    texto = json.dumps(plano, ensure_ascii=False, separators=(",", ":"))
    (SALIDA_DATOS / "plano.json").write_text(texto, encoding="utf-8")
    return estadisticas


def main() -> int:
    SALIDA_DATOS.mkdir(parents=True, exist_ok=True)
    SALIDA_DOCS.mkdir(parents=True, exist_ok=True)
    calles = calles_poligono()
    problemas = validar(calles)
    calcular_danos()
    escombros = calcular_escombros()
    relieve, terreno = calcular_relieve(escombros, 2.0)
    meta = exportar_relieve(relieve, 2.0)
    estadisticas = exportar_json(escombros, meta, calles)
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
