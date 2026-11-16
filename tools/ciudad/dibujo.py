"""Dibuja los planos de desarrollo de Tumansk (docs/ciudad/).

Estilo de plano soviético entintado: papel crema, relieve sombreado con curvas de
nivel cada 2 m, manzanas en tono tierra, calles claras, edificios coloreados por
uso con el número de plantas dentro (como en los planos topográficos de la época)
y un tramado más denso cuanto más dañado está cada edificio.

Se dibuja al doble de tamaño y se reduce al final para suavizar los bordes.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import shapely
from PIL import Image, ImageChops, ImageDraw, ImageFont
from shapely.geometry import LineString, Point

import datos as D
import relieve as R
from geo import ALTO, ANCHO, SECTOR, banda, eje

RAIZ = Path(__file__).resolve().parents[2]
TERRENO: np.ndarray | None = None  # relieve sin escombros, para las normales de pendiente
SS = 2
ESCALA = 1.5
K = SS * ESCALA
M_IZQ, M_SUP, M_INF, SEP, PANEL = 70, 150, 90, 40, 760
ANCHO_PX = int((M_IZQ + ANCHO * ESCALA + SEP + PANEL + 40) * SS)
ALTO_PX = int((M_SUP + ALTO * ESCALA + M_INF) * SS)

PAPEL = (241, 233, 214)
TIERRA = (219, 205, 174)
CALLE = (250, 246, 236)
TINTA = (36, 33, 40)
AGUA = (176, 192, 195)
AGUA_BORDE = (92, 112, 118)
VERDE = (206, 204, 168)
ARENA = (228, 214, 180)
ROJO = (180, 66, 58)
SOCAVON = (62, 52, 46)
AZUL_TEXTO = (52, 84, 98)
GRUPO_COLOR = {
    "vivienda": (178, 150, 118),
    "servicios": (206, 156, 84),
    "industria": (126, 144, 154),
    "especial": (178, 88, 66),
    "madera": (150, 108, 70),
    "ruina": (118, 106, 94),
    "menor": (150, 140, 124),
    "monton": (74, 68, 62),
}
COLOR_VEHICULO = {"abandonado": (112, 102, 94), "quemado": (58, 50, 48), "volcado": (140, 96, 60)}

_FUENTES = "/usr/share/fonts/truetype/"


def fuente(nombre: str, tam: float) -> ImageFont.FreeTypeFont:
    rutas = {
        "sans": "liberation/LiberationSans-Regular.ttf",
        "sans_b": "liberation/LiberationSans-Bold.ttf",
        "sans_i": "liberation/LiberationSans-Italic.ttf",
        "serif_i": "liberation/LiberationSerif-Italic.ttf",
        "serif_b": "liberation/LiberationSerif-Bold.ttf",
        "serif": "liberation/LiberationSerif-Regular.ttf",
        "dejavu": "dejavu/DejaVuSans.ttf",
        "dejavu_b": "dejavu/DejaVuSans-Bold.ttf",
    }
    return ImageFont.truetype(_FUENTES + rutas[nombre], int(round(tam * SS)))


# ---------------------------------------------------------------------------
# Lienzo
# ---------------------------------------------------------------------------
class Lienzo:
    def __init__(self) -> None:
        self.img = Image.new("RGB", (ANCHO_PX, ALTO_PX), PAPEL)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.ox = M_IZQ * SS
        self.oy = M_SUP * SS
        self.w = int(ANCHO * K)
        self.h = int(ALTO * K)

    def px(self, x: float, y: float) -> tuple[float, float]:
        return (self.ox + x * K, self.oy + (ALTO - y) * K)

    def pts(self, lista) -> list[tuple[float, float]]:
        return [self.px(x, y) for x, y in lista]

    def recorte(self) -> Image.Image:
        """Máscara del área del mapa (para que nada se salga del marco)."""
        m = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(m).rectangle([self.ox, self.oy, self.ox + self.w, self.oy + self.h], fill=255)
        return m

    # --- formas ---
    def poligono(self, geom, relleno=None, borde=None, grueso: float = 1.0, capa: ImageDraw.ImageDraw | None = None) -> None:
        d = capa or self.d
        for g in _poligonos(geom):
            exterior = self.pts(g.exterior.coords)
            if relleno is not None:
                d.polygon(exterior, fill=relleno)
            if borde is not None:
                d.line(exterior + [exterior[0]], fill=borde, width=max(1, int(round(grueso * SS))), joint="curve")
            for hueco in g.interiors:
                interior = self.pts(hueco.coords)
                if borde is not None:
                    d.line(interior + [interior[0]], fill=borde, width=max(1, int(round(grueso * SS))), joint="curve")

    def linea(self, puntos, color, grueso: float, guion: tuple[float, float] | None = None, capa=None) -> None:
        d = capa or self.d
        ancho = max(1, int(round(grueso * SS)))
        if guion is None:
            d.line(self.pts(puntos), fill=color, width=ancho, joint="curve")
            return
        trazo, hueco = guion
        linea = LineString(puntos)
        total = linea.length
        pos = 0.0
        while pos < total:
            fin = min(total, pos + trazo)
            tramo = shapely.ops.substring(linea, pos, fin)
            if tramo.length > 0:
                d.line(self.pts(tramo.coords), fill=color, width=ancho)
            pos = fin + hueco

    def circulo(self, x, y, r_px: float, relleno=None, borde=None, grueso: float = 1.0, capa=None) -> None:
        d = capa or self.d
        cx, cy = self.px(x, y)
        r = r_px * SS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=relleno, outline=borde, width=max(1, int(grueso * SS)))

    def texto(self, x, y, texto: str, f, color=TINTA, halo=PAPEL, grueso_halo: float = 2.5, angulo: float = 0.0,
              ancla: str = "mm", en_px: bool = False) -> None:
        cx, cy = (x, y) if en_px else self.px(x, y)
        texto_rotado(self.img, texto, f, cx, cy, color, halo, grueso_halo, angulo, ancla)


def _poligonos(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [g for g in geom.geoms if g.geom_type == "Polygon"]
    return []


def texto_rotado(img, texto, f, cx, cy, color, halo, grueso_halo, angulo, ancla="mm") -> None:
    halo_px = int(round(grueso_halo * SS)) if halo is not None else 0
    caja = f.getbbox(texto, stroke_width=halo_px)
    w, h = caja[2] - caja[0] + 4, caja[3] - caja[1] + 4
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(capa).text(
        (2 - caja[0], 2 - caja[1]), texto, font=f, fill=color + (255,) if len(color) == 3 else color,
        stroke_width=halo_px, stroke_fill=(halo + (235,)) if halo is not None else None,
    )
    if angulo:
        capa = capa.rotate(angulo, resample=Image.BICUBIC, expand=True)
    if ancla == "mm":
        dx, dy = capa.width / 2, capa.height / 2
    elif ancla == "lm":
        dx, dy = 0, capa.height / 2
    elif ancla == "lt":
        dx, dy = 0, 0
    elif ancla == "rm":
        dx, dy = capa.width, capa.height / 2
    else:
        dx, dy = capa.width / 2, capa.height / 2
    img.paste(capa, (int(cx - dx), int(cy - dy)), capa)


def espaciado(texto: str, espacios: int = 1) -> str:
    sep = " " * espacios
    return sep.join(texto)


# ---------------------------------------------------------------------------
# Texturas y relieve
# ---------------------------------------------------------------------------
def patron_rayas(tam: tuple[int, int], separacion: float, angulo: float, grosor: float) -> Image.Image:
    """Rayado diagonal en una imagen L (255 = raya)."""
    w, h = tam
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angulo)
    v = xx * math.cos(a) + yy * math.sin(a)
    fase = np.mod(v, separacion * SS)
    raya = (fase < grosor * SS).astype(np.uint8) * 255
    return Image.fromarray(raya, "L")


def interpolar_alturas(h: np.ndarray, res: float, l: Lienzo) -> np.ndarray:
    """Alturas a la resolución del lienzo (bilineal), en float32."""
    ny, nx = h.shape
    xs = (np.arange(l.w, dtype=np.float32) + 0.5) / K / res - 0.5
    ys = (ALTO - (np.arange(l.h, dtype=np.float32) + 0.5) / K) / res - 0.5
    x0 = np.clip(np.floor(xs).astype(int), 0, nx - 2)
    y0 = np.clip(np.floor(ys).astype(int), 0, ny - 2)
    fx = np.clip(xs - x0, 0, 1).astype(np.float32)
    fy = np.clip(ys - y0, 0, 1).astype(np.float32)
    hf = h.astype(np.float32)
    a = hf[y0][:, x0]
    b = hf[y0][:, x0 + 1]
    c = hf[y0 + 1][:, x0]
    dd = hf[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (dd - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def aplicar_sombreado(l: Lienzo, h: np.ndarray, res: float, fuerza: float = 0.6) -> None:
    hs = R.sombreado(h, res, 315.0, 38.0)
    plano = math.sin(math.radians(38.0))
    f = np.clip(hs / plano, 0.35, 1.25)
    f = np.flipud(f)
    img = Image.fromarray(((f / 1.25) * 255).astype(np.uint8), "L").resize((l.w, l.h), Image.BICUBIC)
    arr = np.asarray(img).astype(np.float32) / 255.0 * 1.25
    factor = 1.0 + fuerza * (arr - 1.0)
    zona = np.asarray(l.img.crop((l.ox, l.oy, l.ox + l.w, l.oy + l.h))).astype(np.float32)
    zona = np.clip(zona * factor[..., None], 0, 255)
    l.img.paste(Image.fromarray(zona.astype(np.uint8), "RGB"), (l.ox, l.oy))


def dibujar_curvas(l: Lienzo, alturas_lienzo: np.ndarray, color=(140, 116, 84), intervalo: float = 2.0) -> None:
    banda_ = np.floor(alturas_lienzo / intervalo)
    borde = np.zeros(banda_.shape, dtype=bool)
    borde[:, 1:] |= banda_[:, 1:] != banda_[:, :-1]
    borde[1:, :] |= banda_[1:, :] != banda_[:-1, :]
    maestra = np.floor(alturas_lienzo / (intervalo * 5))
    borde_m = np.zeros(banda_.shape, dtype=bool)
    borde_m[:, 1:] |= maestra[:, 1:] != maestra[:, :-1]
    borde_m[1:, :] |= maestra[1:, :] != maestra[:-1, :]
    borde_m2 = borde_m.copy()
    borde_m2[1:, :] |= borde_m[:-1, :]
    borde_m2[:, 1:] |= borde_m[:, :-1]
    alfa = np.where(borde_m2, 150, np.where(borde, 80, 0)).astype(np.uint8)
    capa = Image.new("RGBA", (l.w, l.h), color + (0,))
    capa.putalpha(Image.fromarray(alfa, "L"))
    l.img.paste(capa, (l.ox, l.oy), capa)


def textura_papel(img: Image.Image, fuerza: float = 0.22) -> Image.Image:
    papel = Image.open(RAIZ / "assets" / "textures" / "papel.png").convert("L")
    tile = papel.resize((papel.width * SS, papel.height * SS), Image.BICUBIC)
    capa = Image.new("L", img.size)
    for x in range(0, img.width, tile.width):
        for y in range(0, img.height, tile.height):
            capa.paste(tile, (x, y))
    arr = np.asarray(capa).astype(np.float32) / 255.0
    f = 1.0 - fuerza * (1.0 - arr)
    base = np.asarray(img).astype(np.float32)
    base *= f[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------------------
# Capas del plano
# ---------------------------------------------------------------------------
def capa_arboles(l: Lienzo) -> None:
    for a in D.ARBOLES:
        x, y = a["pos"]
        if a["estado"] == "tumbado":
            # Tumbados: apuntan lejos de la bomba.
            l.linea([(x, y), a["_punta"]], TINTA + (150,), 1.0)
            continue
        l.circulo(x, y, a["copa"] * ESCALA, relleno=(150, 140, 110, 60), borde=TINTA + (120,), grueso=0.6)


def capa_calles(l: Lienzo, calles) -> None:
    l.poligono(calles, relleno=CALLE + (255,))
    l.poligono(calles, borde=TINTA + (120,), grueso=0.9)
    for c in D.CALLES:
        if c["tipo"] == "camino":
            l.linea(c["puntos"], (170, 150, 120, 200), 2.2, guion=(5, 3))
        if c["tipo"] == "escalinata":
            linea = LineString(c["puntos"])
            n = (-math.sin(math.radians(48)) * 18, math.cos(math.radians(48)) * 18)
            for f in np.linspace(0.02, 0.98, 34):
                p = linea.interpolate(f, normalized=True)
                l.linea([(p.x - n[0], p.y - n[1]), (p.x + n[0], p.y + n[1])], TINTA + (90,), 0.8)
        if c["id"] == "avenida_progreso":
            for t in (-8.0, 8.0):
                l.linea([eje(-250, t), eje(-95, t)], TINTA + (70,), 0.7)
                l.linea([eje(95, t), eje(370, t)], TINTA + (70,), 0.7)


def capa_puentes(l: Lienzo) -> None:
    calle = next(c for c in D.CALLES if c["id"] == "puente_progreso")
    s0, s1 = calle["vano_hundido"]
    tablero = banda([eje(372), eje(s0)], 32)
    tablero_n = banda([eje(s1), eje(632)], 32)
    for t in (tablero, tablero_n):
        l.poligono(t, relleno=(232, 226, 212, 255), borde=TINTA + (230,), grueso=1.6)
    hundido = banda([eje(s0 + 3), eje(s1 - 3)], 28)
    l.poligono(hundido, relleno=(150, 140, 126, 200), borde=TINTA + (200,), grueso=1.0)
    for f in np.linspace(0, 1, 9):
        p = eje(s0 + 3 + (s1 - s0 - 6) * f, -12)
        q = eje(s0 + 3 + (s1 - s0 - 6) * f + 4, 12)
        l.linea([p, q], TINTA + (150,), 0.8)
    for s in (440, 470, 545, 600):
        l.poligono(D.rect_eje(s - 3, s + 3, -18, 18), relleno=(120, 112, 100, 255), borde=TINTA + (255,), grueso=0.8)
    pf = D.PUENTE_FERROCARRIL
    l.poligono(banda(pf["puntos"], pf["ancho"]), relleno=(220, 214, 200, 255), borde=TINTA + (240,), grueso=1.6)
    a, b = pf["puntos"]
    for f in np.linspace(0, 1, 14):
        y = a[1] + (b[1] - a[1]) * f
        x = a[0] + (b[0] - a[0]) * f
        l.linea([(x - 7, y), (x + 7, y + 9)], TINTA + (160,), 0.8)
    tubo = next(t for t in D.TUBERIAS if t["id"] == "tubo_rio")
    l.linea(tubo["puntos"], TINTA + (230,), 3.4)
    l.linea(tubo["puntos"], (205, 190, 160, 255), 1.6)


def capa_vias(l: Lienzo) -> None:
    for v in D.VIAS:
        grueso = 3.2 if v["tipo"] == "principal" else 2.0
        l.linea(v["puntos"], TINTA + (255,), grueso)
        l.linea(v["puntos"], (250, 246, 236, 255), grueso * 0.45, guion=(9, 9))
    for t in D.TRANVIAS:
        l.linea(t["puntos"], (143, 59, 46, 200), 1.3, guion=(6, 4))
    for t in D.TROLEBUSES:
        l.linea(t["puntos"], (61, 90, 128, 200), 1.2, guion=(2, 4))
    for t in D.TUBERIAS:
        if t["id"] == "tubo_rio":
            continue
        l.linea(t["puntos"], (107, 91, 75, 230), 2.6)
        l.linea(t["puntos"], (226, 214, 190, 255), 1.0)


def capa_socavones(l: Lienzo) -> None:
    """Los socavones (deterioro.py): el hueco, oscuro, con el fondo más negro."""
    import deterioro as DT

    for s in DT.socavones():
        l.poligono(s.contorno, relleno=SOCAVON + (255,), borde=TINTA + (255,), grueso=1.2)
        fondo = s.contorno.buffer(-min(s.datos["radio"], s.datos["ancho"]) * 0.45)
        if not fondo.is_empty:
            l.poligono(fondo, relleno=(28, 24, 22, 255))


def capa_escombros(l: Lienzo, escombros) -> None:
    rng = np.random.default_rng(3)
    for e in escombros:
        forma = e["forma"]
        tono = (164, 148, 124, 150 if e["dano"] >= 3 else 110)
        l.poligono(forma, relleno=tono)
        n = int(forma.area / (14.0 if e["dano"] >= 3 else 24.0))
        if n <= 0:
            continue
        minx, miny, maxx, maxy = forma.bounds
        px = rng.uniform(minx, maxx, n * 3)
        py = rng.uniform(miny, maxy, n * 3)
        dentro = shapely.contains_xy(forma, px, py)
        for x, y in zip(px[dentro][:n], py[dentro][:n]):
            r = rng.uniform(0.25, 0.6)
            l.circulo(x, y, r * ESCALA, relleno=TINTA + (120,))


def capa_normales(l: Lienzo, h: np.ndarray, res: float, calles, paso: float = 3.2) -> None:
    """Normales de pendiente (hachures): trazos cortos cuesta abajo donde el terreno es empinado.
    Así se lee el relieve de un vistazo: la loma, el barranco, el cráter, los terraplenes y los
    montones de escombros."""
    if TERRENO is not None:
        h = TERRENO
    gy, gx = np.gradient(h, res)
    rng = np.random.default_rng(5)
    xs, ys = np.meshgrid(np.arange(paso / 2, ANCHO, paso), np.arange(paso / 2, ALTO, paso))
    xs = xs.ravel() + rng.uniform(-0.35, 0.35, xs.size) * paso
    ys = ys.ravel() + rng.uniform(-0.35, 0.35, ys.size) * paso
    i = np.clip((ys / res).astype(int), 0, h.shape[0] - 1)
    j = np.clip((xs / res).astype(int), 0, h.shape[1] - 1)
    dx, dy = gx[i, j], gy[i, j]
    pendiente = np.hypot(dx, dy)
    sel = (pendiente > 0.16) & ~shapely.contains_xy(calles, xs, ys) & ~shapely.contains_xy(D.RIO, xs, ys)
    for x, y, ddx, ddy, s in zip(xs[sel], ys[sel], dx[sel], dy[sel], pendiente[sel]):
        largo = min(5.5, 1.4 + 6.0 * s)
        ux, uy = -ddx / s, -ddy / s
        alfa = int(min(200, 70 + 260 * (s - 0.16)))
        l.linea([(x, y), (x + ux * largo, y + uy * largo)], (92, 74, 54, alfa), 0.75)


def capa_patios(l: Lienzo) -> None:
    for p in D.PATIOS:
        f = p["forma"]
        t = p["tipo"]
        if t == "juegos":
            l.poligono(f, relleno=(226, 204, 152, 255), borde=TINTA + (180,), grueso=0.8)
            c = f.centroid
            l.linea([(c.x - 2.5, c.y - 2), (c.x - 1, c.y + 2), (c.x + 1, c.y + 2), (c.x + 2.5, c.y - 2)], TINTA + (200,), 0.8)
        elif t == "pista":
            l.poligono(f, relleno=(186, 192, 164, 255), borde=TINTA + (200,), grueso=0.9)
            c = f.centroid
            pts = list(f.exterior.coords)
            a, b = pts[0], pts[1]
            if math.dist(a, b) > math.dist(pts[1], pts[2]):
                a, b = pts[1], pts[2]
            mx, my = (a[0] + b[0]) / 2 - c.x, (a[1] + b[1]) / 2 - c.y
            l.linea([(c.x - mx, c.y - my), (c.x + mx, c.y + my)], (250, 250, 240, 230), 0.9)
        elif t == "hockey":
            l.poligono(f.buffer(-1.5).buffer(1.5), relleno=(222, 232, 234, 255), borde=TINTA + (210,), grueso=1.0)
        elif t == "basuras":
            l.poligono(f, relleno=(90, 86, 80, 255), borde=TINTA + (200,), grueso=0.6)
        elif t == "aparcamiento":
            l.poligono(f, relleno=(208, 202, 190, 255), borde=TINTA + (120,), grueso=0.6)
        elif t == "carbon":
            l.poligono(f, relleno=(52, 48, 46, 230))
        elif t == "cementerio":
            l.poligono(f, relleno=(198, 196, 160, 255), borde=TINTA + (150,), grueso=0.7)
            minx, miny, maxx, maxy = f.bounds
            for x in np.arange(minx + 4, maxx - 2, 6.0):
                for y in np.arange(miny + 4, maxy - 2, 6.0):
                    l.linea([(x, y - 1.2), (x, y + 1.2)], TINTA + (170,), 0.6)
                    l.linea([(x - 0.8, y + 0.4), (x + 0.8, y + 0.4)], TINTA + (170,), 0.6)
        elif t == "patio_transformadores":
            l.poligono(f, relleno=(196, 192, 182, 255), borde=TINTA + (180,), grueso=0.8)
            minx, miny, maxx, maxy = f.bounds
            for x in np.arange(minx + 8, maxx - 4, 14.0):
                for y in np.arange(miny + 8, maxy - 4, 14.0):
                    l.poligono(D.rect(x, y, 5, 4), relleno=(120, 130, 136, 255), borde=TINTA + (220,), grueso=0.6)
        elif t == "acero":
            l.poligono(f, relleno=(176, 176, 170, 255), borde=TINTA + (160,), grueso=0.7)
        elif t == "huerto":
            l.poligono(f, relleno=(180, 160, 120, 200), borde=TINTA + (120,), grueso=0.5)


def capa_vallas_y_sendas(l: Lienzo) -> None:
    for s in D.SENDAS:
        l.linea(s["puntos"], (250, 246, 236, 255), 2.4)
        l.linea(s["puntos"], (140, 120, 96, 200), 0.7, guion=(3, 2))
    for v in D.VALLAS:
        l.linea(v["puntos"], TINTA + (190,), 0.8, guion=(4, 1.6))
    for linea in D.LINEAS_ELECTRICAS:
        l.linea(linea["puntos"], TINTA + (150,), 0.7, guion=(10, 3))
        for x, y in linea["torres"]:
            l.poligono(D.rect(x, y, 4, 4, 45), relleno=PAPEL + (255,), borde=TINTA + (255,), grueso=0.8)


def capa_vehiculos(l: Lienzo) -> None:
    for v in D.VEHICULOS:
        largo, ancho = D.MEDIDAS[v["tipo"]]
        x, y = v["pos"]
        color = COLOR_VEHICULO[v["estado"]]
        if v["tipo"] in ("vagon", "coche_tren", "locomotora"):
            color = (88, 78, 70) if v["estado"] != "quemado" else (52, 46, 44)
        if v["tipo"] in ("barcaza", "remolcador", "barco", "barca"):
            color = (96, 82, 70)
        forma = D.rect(x, y, largo, ancho, v["angulo"])
        l.poligono(forma, relleno=color + (255,), borde=TINTA + (230,), grueso=0.5)


def capa_edificios(l: Lienzo, numeros: bool = True, apagado: float = 0.0) -> None:
    capa = Image.new("RGBA", l.img.size, (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)
    mascaras = {n: Image.new("L", l.img.size, 0) for n in (2, 3, 4)}
    dm = {n: ImageDraw.Draw(m) for n, m in mascaras.items()}
    orden = sorted(D.EDIFICIOS, key=lambda e: -e["huella"].area)
    for e in orden:
        grupo = D.TIPOS[e["tipo"]]["grupo"]
        color = GRUPO_COLOR[grupo]
        if e["dano"] >= 3:
            color = tuple(int(c * 0.86 + 120 * 0.14) for c in color)
        if apagado:
            color = tuple(int(c * (1 - apagado) + p * apagado) for c, p in zip(color, PAPEL))
        for g in _poligonos(e["huella"]):
            exterior = l.pts(g.exterior.coords)
            dibujo.polygon(exterior, fill=color + (255,))
            for hueco in g.interiors:
                dibujo.polygon(l.pts(hueco.coords), fill=(0, 0, 0, 0))
            if e["dano"] >= 2:
                dm[e["dano"]].polygon(exterior, fill=255)
                for hueco in g.interiors:
                    dm[e["dano"]].polygon(l.pts(hueco.coords), fill=0)
    l.img.paste(capa, (0, 0), capa)
    tramas = {2: (7.0, 45, 1.0, 110), 3: (5.0, 45, 1.1, 150), 4: (3.6, 45, 1.2, 170)}
    for n, (sep, ang, gro, alfa) in tramas.items():
        patron = patron_rayas(l.img.size, sep, ang, gro)
        if n >= 3:
            patron = ImageChops.lighter(patron, patron_rayas(l.img.size, sep * 1.3, -45, gro))
        mascara = ImageChops.multiply(mascaras[n], patron).point(lambda v, a=alfa: v * a // 255)
        tinta = Image.new("RGBA", l.img.size, TINTA + (0,))
        tinta.putalpha(mascara)
        l.img.paste(tinta, (0, 0), tinta)
    for e in orden:
        borde = TINTA + (int(255 * (1 - apagado * 0.6)),)
        grueso = 1.2 if D.TIPOS[e["tipo"]]["grupo"] in ("menor",) else 1.5
        l.poligono(e["huella"], borde=borde, grueso=grueso)
    if not numeros:
        return
    f = fuente("sans", 8.5)
    for e in D.EDIFICIOS:
        if e["huella"].area < 300 or e["pisos"] < 2 or D.TIPOS[e["tipo"]]["grupo"] in ("menor",):
            continue
        p = e["huella"].representative_point()
        l.texto(p.x, p.y, str(e["pisos"]), f, color=TINTA, halo=None, grueso_halo=0)


def capa_agua(l: Lienzo) -> None:
    l.poligono(D.RIO, relleno=AGUA + (255,))
    l.poligono(D.ESTANQUE, relleno=AGUA + (255,))
    rng = np.random.default_rng(11)
    # Grietas del hielo
    for _ in range(170):
        x = rng.uniform(-40, 1640)
        y = float(R.rio_y(x)) + rng.uniform(-50, 50)
        pts = [(x, y)]
        ang = rng.uniform(0, math.pi)
        for _k in range(rng.integers(3, 7)):
            ang += rng.uniform(-0.8, 0.8)
            largo = rng.uniform(4, 16)
            pts.append((pts[-1][0] + math.cos(ang) * largo, pts[-1][1] + math.sin(ang) * largo))
        linea = LineString(pts).intersection(D.RIO.buffer(-2))
        if linea.is_empty:
            continue
        for g in getattr(linea, "geoms", [linea]):
            if g.geom_type == "LineString":
                l.linea(list(g.coords), (236, 242, 242, 200), 0.9)
    l.poligono(D.RIO, borde=AGUA_BORDE + (255,), grueso=1.6)
    l.poligono(D.ESTANQUE, borde=AGUA_BORDE + (255,), grueso=1.2)


def capa_limites(l: Lienzo) -> None:
    """Banda rayada en el borde: lo que hay más allá no se puede pisar."""
    fuera = D.caja(-200, -200, ANCHO + 200, ALTO + 200).difference(D.caja(0, 0, ANCHO, ALTO))
    del fuera
    # Autovía caída (oeste y norte)
    l.linea([(8, 30), (8, 1192), (1240, 1192)], TINTA + (230,), 4.0)
    l.linea([(8, 30), (8, 1192), (1240, 1192)], (160, 150, 136, 255), 2.0, guion=(4, 3))
    # Rastro radiactivo al este
    l.linea([(1592, 30), (1592, 1192)], (180, 120, 40, 220), 3.0, guion=(6, 4))


def capa_zonas(l: Lienzo) -> None:
    for numero, poly in D.ZONA_POLIGONOS.items():
        borde = poly.exterior.difference(D.RIO.buffer(1.0))
        for g in getattr(borde, "geoms", [borde]):
            if g.geom_type == "LineString" and g.length > 5:
                l.linea(list(g.coords), ROJO + (150,), 1.3, guion=(2.5, 3.5))


def limpiar_fuera(l: Lienzo) -> None:
    """Borra lo que se sale del marco del mapa (el río, las líneas de metro, los círculos)."""
    W, H = l.img.size
    for caja_ in ([0, 0, W, l.oy], [0, l.oy + l.h, W, H], [0, 0, l.ox, H], [l.ox + l.w, 0, W, H]):
        l.d.rectangle(caja_, fill=PAPEL)


def capa_rejilla(l: Lienzo) -> None:
    f = fuente("sans_b", 13)
    for i in range(int(ANCHO / SECTOR) + 1):
        x = i * SECTOR
        l.linea([(x, 0), (x, ALTO)], TINTA + (55,), 0.8, guion=(6, 6))
    for j in range(int(ALTO / SECTOR) + 1):
        y = j * SECTOR
        l.linea([(0, y), (ANCHO, y)], TINTA + (55,), 0.8, guion=(6, 6))
    for i in range(int(ANCHO / SECTOR)):
        x = (i + 0.5) * SECTOR
        cx, _ = l.px(x, 0)
        l.texto(cx, l.oy - 14 * SS, "ABCDEFGH"[i], f, halo=None, en_px=True)
        l.texto(cx, l.oy + l.h + 14 * SS, "ABCDEFGH"[i], f, halo=None, en_px=True)
    for j in range(int(ALTO / SECTOR)):
        y = (j + 0.5) * SECTOR
        _, cy = l.px(0, y)
        l.texto(l.ox - 16 * SS, cy, str(j + 1), f, halo=None, en_px=True)
        l.texto(l.ox + l.w + 16 * SS, cy, str(j + 1), f, halo=None, en_px=True)


def capa_marco(l: Lienzo) -> None:
    x0, y0, x1, y1 = l.ox, l.oy, l.ox + l.w, l.oy + l.h
    l.d.rectangle([x0, y0, x1, y1], outline=TINTA + (255,), width=3 * SS)
    l.d.rectangle([x0 - 8 * SS, y0 - 8 * SS, x1 + 8 * SS, y1 + 8 * SS], outline=TINTA + (255,), width=1 * SS)


def rotular_calles(l: Lienzo) -> None:
    tam = {"avenida": 15, "principal": 12.5, "calle": 10.5, "servicio": 9, "peatonal": 9.5, "escalinata": 10, "camino": 9}
    for c in D.CALLES:
        if not c["rotulo"] or c["tipo"] == "puente":
            continue
        linea = LineString(c["puntos"])
        mejor = None
        for a, b in zip(c["puntos"][:-1], c["puntos"][1:]):
            largo = math.dist(a, b)
            if mejor is None or largo > mejor[0]:
                mejor = (largo, a, b)
        largo, a, b = mejor
        estilo = "sans_b" if c["tipo"] in ("avenida", "principal") else ("sans_i" if c["tipo"] == "peatonal" else "sans")
        f = fuente(estilo, tam.get(c["tipo"], 10))
        texto = c["nombre"].upper() if c["tipo"] == "avenida" else c["nombre"]
        ancho_texto = f.getlength(texto) / K
        if ancho_texto > largo * 0.92:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        frac = c.get("rotulo_pos", 0.5)
        x = a[0] + (b[0] - a[0]) * frac
        y = a[1] + (b[1] - a[1]) * frac
        if c["id"] == "avenida_progreso":
            for s in (-200, 270):
                x, y = eje(s, 22)
                l.texto(x, y, texto, f, angulo=48, color=TINTA, halo=CALLE, grueso_halo=2.0)
            continue
        l.texto(x, y, texto, f, angulo=ang, color=TINTA, halo=CALLE, grueso_halo=2.0)
        del linea
    fp = fuente("serif_i", 12)
    for p in D.PLAZAS:
        if not p["rotulo"]:
            continue
        c = p["forma"].centroid
        dy = 0 if p["id"] != "plaza_trabajo" else -48
        l.texto(c.x, c.y + dy, p["nombre"], fp, color=TINTA, halo=CALLE, grueso_halo=2.0)


ROTULOS_EDIFICIOS = {
    "PLZ-06": "Vestíbulo del metro", "PLZ-20": "Estación", "PLZ-07": "Banco", "BLQ-07": "Mineros 7",
    "BLQ-ESC": "Escuela Nº 21", "BLQ-TORRE": "La Torre", "BLQ-CAL": "Calderas", "AVM-01": "Mercado Central",
    "AVM-10": "Grandes Almacenes", "AVM-05": "Cine Cosmos", "AVM-12": "Depósito de trolebuses",
    "OBR-01": "Palacio de la Cultura", "OBR-03": "Panificadora", "OBR-10": "Bomberos", "OBR-17": "Comisaría",
    "OBR-21": "Iglesia vieja", "OBR-07": "Baños", "IND-01": "Depósito de locomotoras", "IND-11": "Fábrica de Maquinaria Nº 2",
    "IND-22": "Almacén 3", "IND-23": "Elevador", "IND-30": "Central Térmica Nº 2", "IND-05": "Parque de carbón",
    "IND-02": "Base de camiones", "HOS-01": "Hospital Clínico Nº 3", "HOS-02": "Policlínica", "PHO-10": "Estadio",
    "CEN-SOV": "Casa de los Sóviets", "CEN-TEA": "Teatro", "CEN-HOT": "Hotel Tumán", "CEN-TEL": "Telégrafo",
    "CEN-COM": "Comisariado Militar", "CEN-UNI": "Universidad", "CEN-RAD": "Casa de la Radio", "CEN-FLU": "Estación Fluvial",
    "CEN-BIB": "Biblioteca", "ZC-01": "EL EDIFICIO PARTIDO", "ZC-02": "Planta Nº 1", "IND-17": "Almacén de la fábrica",
    "IND-15": "Depósito de agua", "IND-33": "Torres de refrigeración", "PHO-03": "Monumento a los Caídos",
    "CEN-VIE": "Torre Vieja", "IND-06T2": "Depósito de combustible", "OBR-04": "Escuela Nº 2",
}


def rotular_edificios(l: Lienzo) -> None:
    f = fuente("sans_i", 9.5)
    fb = fuente("sans_b", 11)
    por_id = {e["id"]: e for e in D.EDIFICIOS}
    for ident, nombre in ROTULOS_EDIFICIOS.items():
        e = por_id.get(ident)
        if e is None:
            continue
        c = e["huella"].centroid
        minx, miny, maxx, maxy = e["huella"].bounds
        y = maxy + 6
        l.texto(c.x, y, nombre, fb if ident == "ZC-01" else f, color=TINTA, halo=PAPEL, grueso_halo=2.2)


def rotular_zonas(l: Lienzo) -> None:
    f = fuente("serif_b", 21)
    fn = fuente("serif_b", 14)
    for numero, z in D.ZONAS.items():
        if "rotulo" not in z:
            continue
        x, y = z["rotulo"]
        l.texto(x, y, espaciado(z["nombre"].upper(), 1), f, color=(70, 52, 44), halo=PAPEL, grueso_halo=4)
        l.texto(x, y - 13, f"ZONA {numero}", fn, color=ROJO, halo=PAPEL, grueso_halo=3)
    fr = fuente("serif_i", 30)
    for x in (560, 1180):
        y = float(R.rio_y(x))
        ang = math.degrees(math.atan2(float(R.rio_y(x + 40)) - float(R.rio_y(x - 40)), 80))
        l.texto(x, y, espaciado("río Tumán", 1), fr, color=AZUL_TEXTO, halo=None, grueso_halo=0, angulo=ang)


def marcar_hitos(l: Lienzo, tam: float = 11.0) -> None:
    f = fuente("sans_b", 9)
    for numero, h in D.HITOS.items():
        x, y = h["pos"]
        l.circulo(x, y, tam * 0.75, relleno=ROJO + (235,), borde=PAPEL + (255,), grueso=1.4)
        l.texto(x, y, str(numero), f, color=(255, 250, 240), halo=None, grueso_halo=0)


# ---------------------------------------------------------------------------
# Panel lateral: título, leyenda y escala
# ---------------------------------------------------------------------------
class Panel:
    def __init__(self, l: Lienzo) -> None:
        self.l = l
        self.x = l.ox + l.w + SEP * SS + 8 * SS
        self.y = l.oy
        self.ancho = PANEL * SS

    def titulo(self, texto: str, tam: float = 17) -> None:
        self.y += 10 * SS
        f = fuente("serif_b", tam)
        texto_rotado(self.l.img, texto.upper(), f, self.x, self.y, TINTA, None, 0, 0, "lt")
        self.y += (tam + 6) * SS
        self.l.d.line([self.x, self.y, self.x + self.ancho - 30 * SS, self.y], fill=TINTA + (180,), width=SS)
        self.y += 8 * SS

    def parrafo(self, texto: str, tam: float = 11.5, color=TINTA, estilo: str = "sans", sangria: float = 0) -> None:
        f = fuente(estilo, tam)
        palabras = texto.split()
        linea = ""
        limite = self.ancho - (36 + sangria) * SS
        for p in palabras:
            prueba = (linea + " " + p).strip()
            if f.getlength(prueba) > limite and linea:
                texto_rotado(self.l.img, linea, f, self.x + sangria * SS, self.y, color, None, 0, 0, "lt")
                self.y += (tam + 4) * SS
                linea = p
            else:
                linea = prueba
        if linea:
            texto_rotado(self.l.img, linea, f, self.x + sangria * SS, self.y, color, None, 0, 0, "lt")
            self.y += (tam + 4) * SS

    def simbolo(self, dibujar, texto: str, tam: float = 11.5) -> None:
        cx, cy = self.x + 18 * SS, self.y + 8 * SS
        dibujar(self.l.d, cx, cy)
        guardado = self.y
        self.x += 44 * SS
        self.ancho -= 44 * SS
        self.parrafo(texto, tam)
        self.x -= 44 * SS
        self.ancho += 44 * SS
        self.y = max(self.y, guardado + 20 * SS) + 2 * SS

    def espacio(self, px: float = 6) -> None:
        self.y += px * SS


def muestra_caja(color, borde=TINTA, rayas: int = 0):
    def dibujar(d, cx, cy):
        w, h = 28 * SS, 16 * SS
        muestra = Image.new("RGBA", (w, h), tuple(color) + (255,))
        dm = ImageDraw.Draw(muestra)
        if rayas:
            sep = {1: 7.0, 2: 5.0, 3: 3.6}[min(rayas, 3)] * SS
            for i in range(-6, 14):
                x = i * sep
                dm.line([x, h, x + h, 0], fill=TINTA + (170,), width=SS)
                if rayas >= 2:
                    dm.line([x, 0, x + h, h], fill=TINTA + (150,), width=SS)
        dm.rectangle([0, 0, w - 1, h - 1], outline=borde + (255,), width=SS)
        d._image.paste(muestra, (int(cx - w / 2), int(cy - h / 2)), muestra)
    return dibujar


def muestra_linea(color, grueso: float, guion: bool = False, fondo=None):
    def dibujar(d, cx, cy):
        if fondo is not None:
            d.line([cx - 16 * SS, cy, cx + 16 * SS, cy], fill=fondo, width=int((grueso + 2) * SS))
        if guion:
            for i in range(4):
                x = cx - 16 * SS + i * 9 * SS
                d.line([x, cy, x + 5 * SS, cy], fill=color, width=int(grueso * SS))
        else:
            d.line([cx - 16 * SS, cy, cx + 16 * SS, cy], fill=color, width=int(grueso * SS))
    return dibujar


def muestra_circulo(relleno, borde=TINTA, r: float = 7):
    def dibujar(d, cx, cy):
        d.ellipse([cx - r * SS, cy - r * SS, cx + r * SS, cy + r * SS], fill=relleno, outline=borde + (255,), width=SS)
    return dibujar


def escala_y_norte(l: Lienzo) -> None:
    x0 = l.ox
    y0 = l.oy + l.h + 30 * SS
    f = fuente("sans_b", 11)
    for i in range(5):
        a = x0 + i * 100 * K
        b = x0 + (i + 1) * 100 * K
        l.d.rectangle([a, y0, b, y0 + 7 * SS], fill=(TINTA if i % 2 == 0 else PAPEL) + (255,), outline=TINTA + (255,), width=SS)
        texto_rotado(l.img, f"{i * 100}", f, a, y0 + 18 * SS, TINTA, None, 0, 0, "mm")
    texto_rotado(l.img, "500 m", f, x0 + 500 * K + 6 * SS, y0 + 18 * SS, TINTA, None, 0, 0, "lm")
    texto_rotado(l.img, "Sectores de 200 × 200 m (A1–H6): son las celdas en las que se carga la ciudad.", fuente("sans", 11),
                 x0 + 580 * K, y0 + 4 * SS, TINTA, None, 0, 0, "lm")
    cx, cy = l.ox + l.w + (SEP + PANEL - 40) * SS, l.oy - 72 * SS
    r = 24 * SS
    l.d.polygon([(cx, cy - r), (cx + r * 0.38, cy + r * 0.6), (cx, cy + r * 0.25)], fill=TINTA + (255,))
    l.d.polygon([(cx, cy - r), (cx - r * 0.38, cy + r * 0.6), (cx, cy + r * 0.25)], fill=PAPEL + (255,), outline=TINTA + (255,))
    texto_rotado(l.img, "N", fuente("serif_b", 16), cx, cy - r - 12 * SS, TINTA, None, 0, 0, "mm")


def cabecera(l: Lienzo, titulo: str, subtitulo: str, hoja: str) -> None:
    texto_rotado(l.img, "TUMANSK", fuente("serif_b", 50), l.ox, 62 * SS, TINTA, None, 0, 0, "lm")
    ancho = fuente("serif_b", 50).getlength("TUMANSK")
    texto_rotado(l.img, titulo, fuente("serif_b", 26), l.ox + ancho + 30 * SS, 52 * SS, ROJO, None, 0, 0, "lm")
    texto_rotado(l.img, subtitulo, fuente("sans", 14), l.ox + ancho + 30 * SS, 84 * SS, TINTA, None, 0, 0, "lm")
    texto_rotado(l.img, hoja, fuente("sans_b", 13), l.ox + l.w, 62 * SS, TINTA, None, 0, 0, "rm")
    texto_rotado(l.img, "SOLO PARA DESARROLLO · NO ES UN MAPA DEL JUEGO", fuente("sans", 11), l.ox + l.w, 86 * SS, ROJO, None, 0, 0, "rm")


def guardar(l: Lienzo, ruta: Path) -> None:
    img = textura_papel(l.img, 0.16)
    final = img.resize((img.width // SS, img.height // SS), Image.LANCZOS).convert("RGB")
    final.save(ruta, quality=90, optimize=True)
    print(f"  {ruta.relative_to(RAIZ)}  {final.width}x{final.height}  {ruta.stat().st_size // 1024} KB")


# ---------------------------------------------------------------------------
# Base común y planos
# ---------------------------------------------------------------------------
def base(h: np.ndarray, res: float, escombros, calles, apagado: float = 0.0, numeros: bool = True, arboles: bool = True) -> Lienzo:
    l = Lienzo()
    l.d.rectangle([l.ox, l.oy, l.ox + l.w, l.oy + l.h], fill=TIERRA + (255,))
    verdes = D.ZONAS_VERDES
    l.poligono(verdes["parque"], relleno=VERDE + (255,))
    l.poligono(verdes["hospital"], relleno=VERDE + (150,))
    l.poligono(verdes["barranco"].difference(D.RIO), relleno=VERDE + (190,))
    l.poligono(verdes["playa"], relleno=ARENA + (255,))
    capa_agua(l)
    aplicar_sombreado(l, h, res, 0.85)
    alturas = interpolar_alturas(h, res, l)
    dibujar_curvas(l, alturas)
    del alturas
    capa_calles(l, calles)
    capa_escombros(l, escombros)
    capa_normales(l, h, res, calles)
    capa_patios(l)
    capa_vallas_y_sendas(l)
    capa_vias(l)
    capa_socavones(l)
    if arboles:
        capa_arboles(l)
    capa_vehiculos(l)
    capa_edificios(l, numeros=numeros)
    capa_puentes(l)
    capa_limites(l)
    if apagado > 0:
        velo = Image.new("RGBA", (l.w, l.h), PAPEL + (int(255 * apagado),))
        l.img.paste(velo, (l.ox, l.oy), velo)
    return l


def plano_general(h, res, escombros, calles, salida: Path) -> None:
    l = base(h, res, escombros, calles)
    capa_zonas(l)
    rotular_calles(l)
    rotular_edificios(l)
    rotular_zonas(l)
    marcar_hitos(l)
    limpiar_fuera(l)
    capa_rejilla(l)
    capa_marco(l)
    escala_y_norte(l)
    cabecera(l, "Plano general", "1,6 × 1,2 km · curvas de nivel cada 2 m · cifras: número de plantas", "Hoja 1 de 4")
    p = Panel(l)
    p.titulo("Cómo leer el plano")
    p.simbolo(muestra_caja(GRUPO_COLOR["vivienda"]), "Viviendas (la cifra es el número de plantas)")
    p.simbolo(muestra_caja(GRUPO_COLOR["servicios"]), "Comercios, servicios y equipamientos")
    p.simbolo(muestra_caja(GRUPO_COLOR["industria"]), "Industria y transporte")
    p.simbolo(muestra_caja(GRUPO_COLOR["especial"]), "Edificios singulares")
    p.simbolo(muestra_caja(GRUPO_COLOR["madera"]), "Casas y barracones de madera")
    p.simbolo(muestra_caja(GRUPO_COLOR["ruina"]), "Ruinas de la Zona Cero")
    p.simbolo(muestra_caja(GRUPO_COLOR["menor"]), "Garajes, cobertizos, quioscos")
    p.espacio()
    p.parrafo("Daño (rayado sobre el edificio):", 11.5, estilo="sans_b")
    p.simbolo(muestra_caja(GRUPO_COLOR["vivienda"]), "1 · Herido: sin cristales, hollín, balcones caídos")
    p.simbolo(muestra_caja(GRUPO_COLOR["vivienda"], rayas=1), "2 · Roto: derrumbes parciales")
    p.simbolo(muestra_caja(GRUPO_COLOR["vivienda"], rayas=2), "3 · Destripado: cascarón, calles cegadas")
    p.simbolo(muestra_caja(GRUPO_COLOR["vivienda"], rayas=3), "4 · Arrasado: muñones y escombros")
    p.simbolo(muestra_caja((150, 136, 116)), "Escombros caídos a la calle (hacia fuera de la bomba)")
    p.simbolo(muestra_caja(SOCAVON), "Socavón: la calle se hundió sobre un colector, una tubería o el metro")
    p.espacio()
    p.simbolo(muestra_linea(TINTA + (255,), 3.2), "Ferrocarril")
    p.simbolo(muestra_linea((143, 59, 46, 255), 1.4, guion=True), "Tranvía")
    p.simbolo(muestra_linea((61, 90, 128, 255), 1.4, guion=True), "Trolebús")
    p.simbolo(muestra_linea((107, 91, 75, 255), 2.6), "Tubería de calefacción elevada")
    p.simbolo(muestra_circulo((150, 140, 110, 80), r=4), "Árbol muerto · cerca de la bomba, tumbado hacia fuera")
    p.simbolo(muestra_caja(COLOR_VEHICULO["abandonado"]), "Vehículos abandonados (los oscuros, quemados): el atasco de la evacuación")
    p.simbolo(muestra_caja((226, 204, 152)), "Parque infantil · pista deportiva · caja de hockey (hielo)")
    p.simbolo(muestra_linea(TINTA + (190,), 0.8, guion=True), "Valla o tapia")
    p.simbolo(muestra_linea((92, 74, 54, 200), 0.8), "Normales de pendiente: terreno empinado (loma, barranco, terraplenes, escombros)")
    p.simbolo(muestra_circulo(ROJO + (235,), PAPEL, r=8), "Hito (lista abajo)")
    p.simbolo(muestra_linea(ROJO + (160,), 1.3, guion=True), "Límite de zona")
    p.espacio()
    p.titulo("Zonas", 15)
    for numero, z in D.ZONAS.items():
        p.parrafo(f"{numero} · {z['nombre']} ({z['salida']})", 11.5, estilo="sans_b")
    p.titulo("Hitos", 15)
    columna = [f"{n}. {v['nombre']}" for n, v in D.HITOS.items()]
    mitad = (len(columna) + 1) // 2
    y0 = p.y
    for i, texto in enumerate(columna):
        x = p.x + (0 if i < mitad else (PANEL / 2 - 10) * SS)
        y = y0 + (i % mitad) * 15.5 * SS
        texto_rotado(l.img, texto, fuente("sans", 10.5), x, y, TINTA, None, 0, 0, "lt")
    p.y = y0 + mitad * 15.5 * SS
    guardar(l, salida)


def plano_subsuelo(h, res, escombros, calles, salida: Path) -> None:
    l = base(h, res, escombros, calles, apagado=0.55, numeros=False, arboles=False)
    for s in D.SUBSUELO:
        if s["tipo"] == "galeria":
            l.linea(s["puntos"], (110, 92, 70, 255), 4.0)
            l.linea(s["puntos"], (232, 210, 170, 255), 1.6)
        elif s["tipo"] == "colector":
            l.linea(s["puntos"], (60, 104, 92, 255), 3.4, guion=(10, 4))
        elif s["tipo"] == "peatonal":
            l.linea(s["puntos"], (90, 70, 110, 255), 7.0)
            l.linea(s["puntos"], (226, 214, 236, 255), 3.6)
        elif s["tipo"] == "sotano":
            l.linea(s["puntos"], (130, 110, 80, 200), 6.0)
    for tramo in D.TRAMOS_INUNDADOS:
        l.linea(tramo["puntos"], (90, 150, 200, 160), 16.0)
    for tramo in D.TRAMOS_HUNDIDOS:
        l.linea(tramo["puntos"], (90, 90, 90, 140), 16.0)
    for linea in D.METRO_LINEAS:
        color = tuple(int(linea["color"][i : i + 2], 16) for i in (1, 3, 5))
        l.linea(linea["puntos"], TINTA + (255,), 7.5)
        l.linea(linea["puntos"], color + (255,), 5.0)
    estados = {"habitada": (60, 140, 80), "inundada": (70, 120, 190), "hundida": (120, 110, 100), "destruida": (60, 50, 50), "abandonada": (190, 150, 60)}
    f = fuente("sans_b", 12)
    fs = fuente("sans", 10.5)
    for s in D.METRO_ESTACIONES:
        l.poligono(s["forma"], relleno=estados[s["estado"]] + (255,), borde=TINTA + (255,), grueso=2.0)
        x, y = s["pos"]
        l.texto(x, y + 26, f"{s['id']} · {s['nombre']}", f, halo=PAPEL)
        l.texto(x, y - 24, s["estado"], fs, color=estados[s["estado"]], halo=PAPEL)
    for r in D.METRO_REJAS:
        x, y = r["pos"]
        l.circulo(x, y, 7, relleno=(60, 140, 80, 255), borde=TINTA, grueso=1.4)
        l.texto(x + 12, y, r["nombre"], fs, ancla="lm", halo=PAPEL)
    for p in D.POZOS:
        x, y = p["pos"]
        l.d.rectangle([*[v - 6 * SS for v in l.px(x, y)], *[v + 6 * SS for v in l.px(x, y)]], fill=PAPEL + (255,), outline=TINTA + (255,), width=2 * SS)
        l.texto(x, y, p["id"], fuente("sans_b", 8), halo=None)
    for p in D.PUNTOS:
        if p["tipo"] != "acceso":
            continue
        x, y = p["pos"]
        l.circulo(x, y, 6, relleno=(232, 200, 120, 255), borde=TINTA, grueso=1.4)
    f_eti = fuente("sans_i", 11)
    for s in D.SUBSUELO:
        if s["tipo"] in ("galeria", "colector"):
            a, b = s["puntos"][len(s["puntos"]) // 2 - 1], s["puntos"][len(s["puntos"]) // 2]
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
            l.texto((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 8, s["nombre"], f_eti, angulo=ang, halo=PAPEL)
    limpiar_fuera(l)
    capa_rejilla(l)
    capa_marco(l)
    escala_y_norte(l)
    cabecera(l, "El subsuelo", "Metro, galerías, colectores y pasos subterráneos", "Hoja 2 de 4")
    p = Panel(l)
    p.titulo("Metro")
    for linea in D.METRO_LINEAS:
        color = tuple(int(linea["color"][i : i + 2], 16) for i in (1, 3, 5))
        p.simbolo(muestra_linea(color + (255,), 5, fondo=TINTA + (255,)), f"{linea['nombre']}: {linea['notas']}")
    for s in D.METRO_ESTACIONES:
        p.simbolo(muestra_caja(estados[s["estado"]]), f"{s['id']} {s['nombre']} ({s['estado']}). {s['notas']}", 10.5)
    p.simbolo(muestra_circulo((60, 140, 80, 255)), "Rejas del gobierno civil: los stalkers salen por aquí con permiso")
    p.simbolo(muestra_linea((90, 150, 200, 200), 10), "Tramo inundado (agua helada hasta el pecho)")
    p.simbolo(muestra_linea((90, 90, 90, 200), 10), "Tramo hundido (no se pasa)")
    p.titulo("Otros caminos bajo tierra", 15)
    p.simbolo(muestra_linea((110, 92, 70, 255), 4), "Galerías de servicio (calefacción, cables): 2 m, se camina de pie")
    p.simbolo(muestra_linea((60, 104, 92, 255), 3.4, guion=True), "Colectores: agachado; desaguan en el río")
    p.simbolo(muestra_linea((90, 70, 110, 255), 6), "Pasos subterráneos peatonales")
    p.simbolo(muestra_linea((130, 110, 80, 220), 6), "Sótanos corridos")
    p.simbolo(muestra_caja(PAPEL), "Pozos de ventilación del metro (V1–V6)")
    p.simbolo(muestra_circulo((232, 200, 120, 255)), "Accesos: bocas, socavón, desagües")
    p.titulo("Pozos", 15)
    for pozo in D.POZOS:
        p.parrafo(f"{pozo['id']}: {pozo['notas']}", 10.5)
    guardar(l, salida)


COLOR_ESPECIE = {"jauria": (176, 92, 40), "inquilino": (110, 60, 130), "llamador": (40, 110, 120), "saqueadores": (170, 40, 40)}


def plano_peligros(h, res, escombros, calles, salida: Path) -> None:
    l = base(h, res, escombros, calles, apagado=0.5, numeros=False, arboles=False)
    # Anillos de daño
    for radio, nivel in [(400, 4), (800, 3), (1250, 2)]:
        circulo = Point(*D.GZ).buffer(radio, 64).exterior
        l.linea(list(circulo.coords), (120, 40, 30, 200), 1.6, guion=(14, 8))
        x, y = D.GZ[0] - radio * 0.71, D.GZ[1] - radio * 0.71
        if 0 < x < ANCHO and 0 < y < ALTO:
            l.texto(x, y, f"daño {nivel}+ dentro", fuente("sans_b", 10), color=(120, 40, 30), halo=PAPEL)
    # Radiación
    for r in D.RASTRO_RADIACTIVO:
        tono = {1: (230, 200, 60, 60), 2: (230, 150, 40, 70), 3: (200, 60, 30, 80)}[r["nivel"]]
        l.poligono(r["forma"].intersection(D.caja(0, 0, ANCHO, ALTO)), relleno=tono)
    for fco in D.FOCOS_RADIACION:
        x, y = fco["pos"]
        tono = {1: (230, 200, 60), 2: (230, 150, 40), 3: (200, 60, 30)}[fco["nivel"]]
        l.poligono(Point(x, y).buffer(fco["radio"]), relleno=tono + (90,), borde=tono + (255,), grueso=1.4)
    for m in D.ZONAS_MASCARA:
        forma = m["forma"].intersection(D.caja(0, 0, ANCHO, ALTO))
        l.poligono(forma, borde=(90, 120, 60, 255), grueso=2.0)
        mask = Image.new("L", l.img.size, 0)
        ImageDraw.Draw(mask).polygon(l.pts(_poligonos(forma)[0].exterior.coords), fill=110)
        rayas = ImageChops.multiply(mask, patron_rayas(l.img.size, 6, -30, 1.0))
        capa = Image.new("RGBA", l.img.size, (90, 120, 60, 0))
        capa.putalpha(rayas)
        l.img.paste(capa, (0, 0), capa)
    for hf in D.HIELO_FINO:
        l.poligono(hf["forma"], relleno=(255, 255, 255, 120), borde=(40, 80, 140, 255), grueso=1.4)
    # Amenazas
    for a in D.AMENAZAS:
        color = COLOR_ESPECIE[a["especie"]]
        l.poligono(a["territorio"].intersection(D.caja(0, 0, ANCHO, ALTO)), relleno=color + (36,), borde=color + (220,), grueso=1.8)
        x, y = a["guarida"]
        l.circulo(x, y, 9, relleno=color + (255,), borde=PAPEL, grueso=2)
        l.texto(x, y - 18, a["nombre"], fuente("sans_b", 10.5), color=color, halo=PAPEL)
    for pa in D.PATRULLAS:
        l.linea(pa["puntos"], (170, 40, 40, 230), 2.2, guion=(8, 5))
        a, b = pa["puntos"][-2], pa["puntos"][-1]
        _flecha(l, a, b, (170, 40, 40, 255))
        m = pa["puntos"][len(pa["puntos"]) // 2]
        l.texto(m[0], m[1] + 10, pa["id"], fuente("sans_b", 11), color=(170, 40, 40), halo=PAPEL)
    for v in D.VIGIAS:
        x, y = v["pos"]
        cono = [v["pos"]]
        for k in range(25):
            ang = math.radians(v["rumbo"] - v["abertura"] / 2 + v["abertura"] * k / 24)
            cono.append((x + math.cos(ang) * v["alcance"], y + math.sin(ang) * v["alcance"]))
        l.poligono(D.poligono(cono).intersection(D.caja(0, 0, ANCHO, ALTO)), relleno=(170, 40, 40, 14), borde=(170, 40, 40, 110), grueso=1.0)
        l.circulo(x, y, 8, relleno=PAPEL + (255,), borde=(170, 40, 40), grueso=2.4)
        l.circulo(x, y, 3, relleno=(170, 40, 40, 255))
    for c in D.CRUCES_RIO:
        x, y = c["pos"]
        l.circulo(x, y, 9, relleno=(40, 80, 140, 255), borde=PAPEL, grueso=2)
        l.texto(x, y + 16, c["nombre"], fuente("sans_b", 10.5), color=(40, 80, 140), halo=PAPEL)
    for lim in D.LIMITES:
        x, y = lim["pos"]
        l.texto(min(max(x, 90), ANCHO - 90), min(max(y, 20), ALTO - 14), lim["nombre"], fuente("sans_b", 10.5),
                color=TINTA, halo=PAPEL, angulo=90 if lim["lado"] in ("oeste", "este") else 0)
    limpiar_fuera(l)
    capa_rejilla(l)
    capa_marco(l)
    escala_y_norte(l)
    cabecera(l, "Amenazas y peligros", "Territorios, guaridas, patrullas, vigías, radiación, aire y hielo", "Hoja 3 de 4")
    p = Panel(l)
    p.titulo("Amenazas")
    for a in D.AMENAZAS:
        color = COLOR_ESPECIE[a["especie"]]
        p.simbolo(muestra_circulo(color + (255,), PAPEL, 8), f"{a['nombre']}. {a['rutina']} {a['notas']}", 10.5)
    p.simbolo(muestra_linea((170, 40, 40, 255), 2.2, guion=True), "Patrullas de los saqueadores (P1–P4)")
    p.simbolo(muestra_circulo(PAPEL + (255,), (170, 40, 40), 8), "Vigías con lo que alcanzan a ver de día")
    p.titulo("Peligros", 15)
    p.simbolo(muestra_caja((230, 200, 60)), "Rastro radiactivo, nivel 1 a 3 (más oscuro, más dosis)")
    p.simbolo(muestra_caja((230, 150, 40)), "Focos de radiación: objetos y sitios contaminados")
    p.simbolo(muestra_caja((150, 170, 120)), "Hace falta máscara")
    p.simbolo(muestra_caja((240, 244, 250), (40, 80, 140)), "Hielo fino")
    p.simbolo(muestra_caja(SOCAVON), "Socavones: caída de 2 a 11 m (el de la avenida baja al túnel)")
    p.simbolo(muestra_linea((120, 40, 30, 255), 1.6, guion=True), "Anillos de daño de la bomba")
    p.simbolo(muestra_circulo((40, 80, 140, 255), PAPEL, 8), "Cruces del río")
    p.titulo("Patrullas", 15)
    for pa in D.PATRULLAS:
        p.parrafo(f"{pa['id']} · {pa['nombre']} ({pa['horario']})", 10.5)
    guardar(l, salida)


def _flecha(l: Lienzo, a, b, color) -> None:
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    largo = 9
    p1 = (b[0] - math.cos(ang - 0.45) * largo, b[1] - math.sin(ang - 0.45) * largo)
    p2 = (b[0] - math.cos(ang + 0.45) * largo, b[1] - math.sin(ang + 0.45) * largo)
    l.d.polygon(l.pts([b, p1, p2]), fill=color)


COLORES_RUTA = [(178, 58, 52), (44, 96, 150), (64, 128, 72), (150, 96, 30), (110, 64, 140)]


def plano_rutas(h, res, escombros, calles, salida: Path) -> None:
    l = base(h, res, escombros, calles, apagado=0.45, numeros=False, arboles=False)
    destinos = []
    for r in D.RUTAS:
        if r["destino"] not in destinos:
            destinos.append(r["destino"])
    for r in D.RUTAS:
        i = destinos.index(r["destino"])
        variante = "abcde".index(r["id"][-1])
        color = COLORES_RUTA[variante % len(COLORES_RUTA)]
        grueso = 3.6 if i == 3 else 2.6
        l.linea(r["puntos"], PAPEL + (255,), grueso + 2.4)
        l.linea(r["puntos"], color + (240,), grueso, guion=None if variante == 0 else (10, 4))
        _flecha(l, r["puntos"][-2], r["puntos"][-1], color + (255,))
        m = r["puntos"][max(1, len(r["puntos"]) // 2)]
        l.texto(m[0], m[1], f"{r['id']} · {r['minutos']}′", fuente("sans_b", 10.5), color=color, halo=PAPEL)
    simbolos = {"padre": ((30, 30, 30), 10), "refugio": ((64, 128, 72), 8), "botin": ((200, 150, 40), 7), "mirador": ((44, 96, 150), 7), "historia": ((140, 120, 100), 6)}
    for p in D.PUNTOS:
        if p["tipo"] not in simbolos:
            continue
        color, r = simbolos[p["tipo"]]
        x, y = p["pos"]
        if p["tipo"] == "padre":
            l.circulo(x, y, r, relleno=PAPEL + (255,), borde=TINTA, grueso=2.6)
            l.circulo(x, y, r * 0.45, relleno=TINTA + (255,))
        elif p["tipo"] == "refugio":
            cx, cy = l.px(x, y)
            s = r * SS
            l.d.polygon([(cx, cy - s * 1.2), (cx + s, cy), (cx + s, cy + s), (cx - s, cy + s), (cx - s, cy)], fill=color + (255,), outline=TINTA + (255,))
        elif p["tipo"] == "botin":
            l.circulo(x, y, r, relleno=color + (255,), borde=TINTA, grueso=1.2)
            l.texto(x, y, str(p.get("peligro", "")), fuente("sans_b", 8), color=TINTA, halo=None)
        elif p["tipo"] == "mirador":
            cx, cy = l.px(x, y)
            s = r * SS
            l.d.polygon([(cx - s, cy + s), (cx + s, cy + s), (cx, cy - s)], fill=color + (255,), outline=TINTA + (255,))
        else:
            l.circulo(x, y, r, relleno=color + (200,), borde=TINTA, grueso=1.0)
    x, y = (334, 296)
    l.circulo(x, y, 13, relleno=(60, 140, 80, 255), borde=PAPEL, grueso=2.5)
    l.texto(x - 18, y - 22, "TU SALIDA", fuente("sans_b", 12), color=(40, 100, 60), halo=PAPEL)
    limpiar_fuera(l)
    capa_rejilla(l)
    capa_marco(l)
    escala_y_norte(l)
    cabecera(l, "Rutas y objetivos", "Siempre hay varias rutas · tiempos a paso prudente, sin contar imprevistos", "Hoja 4 de 4")
    p = Panel(l)
    for destino in destinos:
        p.titulo(destino, 14)
        for r in D.RUTAS:
            if r["destino"] != destino:
                continue
            variante = "abcde".index(r["id"][-1])
            color = COLORES_RUTA[variante % len(COLORES_RUTA)]
            metros = round(LineString(r["puntos"]).length / 10) * 10
            p.simbolo(muestra_linea(color + (255,), 3, guion=variante > 0),
                      f"{r['id']} · {r['nombre']}: {r['perfil']}. ~{metros} m, unos {r['minutos']} min de ida.", 10.5)
    p.titulo("Símbolos", 14)
    p.simbolo(muestra_circulo(PAPEL + (255,), TINTA, 9), "Rastro de tu padre (pocos y ambiguos)")
    p.simbolo(muestra_circulo((200, 150, 40, 255), TINTA, 7), "Botín; la cifra es el peligro (1 a 5)")
    p.simbolo(muestra_caja((64, 128, 72)), "Refugio posible (no son los únicos)")
    p.simbolo(muestra_caja((44, 96, 150)), "Mirador")
    p.simbolo(muestra_circulo((140, 120, 100, 220), TINTA, 6), "Historia del entorno")
    guardar(l, salida)


PLANOS = {
    "general": (plano_general, "plano_tumansk.jpg"),
    "subsuelo": (plano_subsuelo, "plano_tumansk_subsuelo.jpg"),
    "peligros": (plano_peligros, "plano_tumansk_peligros.jpg"),
    "rutas": (plano_rutas, "plano_tumansk_rutas.jpg"),
}


def dibujar_todo(h: np.ndarray, res: float, escombros, calles, salida: Path, solo: list[str] | None = None) -> None:
    for nombre, (funcion, archivo) in PLANOS.items():
        if solo and nombre not in solo:
            continue
        funcion(h, res, escombros, calles, salida / archivo)
