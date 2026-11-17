"""Texturas de los pavimentos de la ciudad (la red de tránsito de la maqueta).

Grises que se multiplican por el color de cada superficie (lo pone la maqueta). Nada está
intacto (ver «La ambientación de la superficie» en el README): es el pavimento de una
ciudad soviética que ya estaba gastado antes de la guerra y lleva dos años sin que nadie lo
toque, con heladas que lo levantan y lo abren.

- Asfalto: piel de cocodrilo, grietas largas con los bordes desgranados, parches viejos
  (también rotos), zonas donde el árido se ha soltado, baches pequeños y manchas.
- Hormigón: el de mala calidad de los muros, los andenes y las losas de los pasos a nivel:
  poros, juntas del encofrado, desconchones con la armadura oxidada que chorrea, grietas
  con salitre y churretes de suciedad.
- Losas, granito y adoquín: piezas de tonos dispares, partidas, hundidas o que faltan
  (queda la tierra), cantos desportillados y juntas abiertas con verdín.
- Bordillo, grava, tierra y la pintura vial, que se ha ido a trozos: su alfa recorta lo
  que queda (debajo se ve el asfalto).
- Derrumbe: el interior de los socavones y el corte de la calle en su borde: tierra helada
  revuelta con cascotes de asfalto, de hormigón y de ladrillo, piedras y escarcha.
- Matojo: una mata de hierba seca (en color, con el alfa recortando las hojas) para los
  matojos que salen por las grietas, junto a los bordillos y en el balasto.

Todas se enlosan sin costuras y salen siempre iguales (semillas fijas). Cada una cubre
los metros que dice CityTransit.TILE: el dibujo está hecho a esa escala.

Uso: las genera tools/textures/generate_textures.py en assets/textures/pavimentos/.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _noise(size: int, beta: float, seed: int) -> np.ndarray:
    """Ruido 1/f^beta sin costuras, en [0, 1]."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((size, size)))
    ky = np.fft.fftfreq(size)[:, None]
    kx = np.fft.fftfreq(size)[None, :]
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    noise = np.real(np.fft.ifft2(spectrum / k ** (beta / 2.0)))
    noise -= noise.min()
    return noise / noise.max()


def _smoothstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _wrapped(draw: ImageDraw.ImageDraw, shape: str, coords, size: int, **style) -> None:
    """Dibuja una figura repetida en las nueve posiciones del enlosado."""
    for dx in (-size, 0, size):
        for dy in (-size, 0, size):
            if shape == "line":
                draw.line([(x + dx, y + dy) for x, y in coords], **style)
            elif shape == "polygon":
                draw.polygon([(x + dx, y + dy) for x, y in coords], **style)
            elif shape == "ellipse":
                x0, y0, x1, y1 = coords
                draw.ellipse((x0 + dx, y0 + dy, x1 + dx, y1 + dy), **style)


def _crack(rng: np.random.Generator, start, length: float, angle: float, wander: float = 0.35) -> list:
    """Una grieta: camino quebrado que se tuerce poco a poco."""
    points = [tuple(start)]
    x, y = start
    steps = max(3, int(length / 6))
    for _ in range(steps):
        angle += rng.normal(0.0, wander)
        x += math.cos(angle) * length / steps
        y += math.sin(angle) * length / steps
        points.append((x, y))
    return points


def _to_image(values: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(values, 0.0, 1.0) * 255).astype(np.uint8), "L")


def _mask(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("L", (size, size), 0)
    return img, ImageDraw.Draw(img)


def _array(img: Image.Image, blur: float = 0.0) -> np.ndarray:
    if blur > 0.0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(img, dtype=np.float64) / 255.0


def _speckle(size: int, seed: int, count: int, radius: tuple[float, float], tone: tuple[float, float]) -> np.ndarray:
    """Granos sueltos (árido, mica, piedrecitas), como desviación del tono."""
    rng = np.random.default_rng(seed)
    img = Image.new("F", (size, size), 0.0)
    d = ImageDraw.Draw(img)
    for _ in range(count):
        x, y = rng.uniform(0, size, 2)
        r = rng.uniform(*radius)
        _wrapped(d, "ellipse", (x - r, y - r, x + r, y + r), size, fill=float(rng.uniform(*tone)))
    return np.array(img)


def _voronoi(size: int, cell: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Distancias al punto más cercano y al segundo de una malla de celdas desordenada (sin
    costuras: donde se parecen está la arista entre dos celdas) y el número de la celda."""
    n = size // cell
    rng = np.random.default_rng(seed)
    seeds = rng.uniform(0.08, 0.92, (n, n, 2))
    ys, xs = np.mgrid[0:size, 0:size] + 0.5
    cx = (xs // cell).astype(int)
    cy = (ys // cell).astype(int)
    d1 = np.full((size, size), np.inf)
    d2 = np.full((size, size), np.inf)
    ident = np.zeros((size, size), dtype=np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            nx = (cx + ox) % n
            ny = (cy + oy) % n
            sx = (cx + ox + seeds[ny, nx, 0]) * cell
            sy = (cy + oy + seeds[ny, nx, 1]) * cell
            d = np.hypot(xs - sx, ys - sy)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            ident = np.where(closer, ny * n + nx, ident)
            d1 = np.where(closer, d, d1)
    return d1, d2, ident


def _blotches(size: int, seed: int, count: int, radius: tuple[float, float], blur: float) -> np.ndarray:
    """Manchas blandas (aceite, hollín, humedad), de 0 a 1."""
    rng = np.random.default_rng(seed)
    img, d = _mask(size)
    for _ in range(count):
        x, y = rng.uniform(0, size, 2)
        r = rng.uniform(*radius)
        pts = []
        for k in range(10):
            a = k / 10 * math.tau
            rr = r * rng.uniform(0.6, 1.2)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * rng.uniform(0.6, 1.0)))
        _wrapped(d, "polygon", pts, size, fill=int(255 * rng.uniform(0.5, 1.0)))
    return _array(img, blur)


def _cracks(size: int, seed: int, count: int, length: tuple[float, float], width: tuple[int, int],
            branches: float = 0.6) -> tuple[np.ndarray, np.ndarray]:
    """Grietas largas: el trazo oscuro y su borde desgranado (más ancho, para aclararlo)."""
    rng = np.random.default_rng(seed)
    dark, d = _mask(size)
    halo, h = _mask(size)
    for _ in range(count):
        line = _crack(rng, rng.uniform(0, size, 2), rng.uniform(*length), rng.uniform(0, math.tau))
        w = int(rng.integers(width[0], width[1] + 1))
        _wrapped(h, "line", line, size, fill=255, width=w * 4)
        _wrapped(d, "line", line, size, fill=255, width=w)
        if rng.random() < branches:
            branch = _crack(rng, line[len(line) // 2], rng.uniform(length[0] * 0.2, length[0] * 0.6),
                            rng.uniform(0, math.tau))
            _wrapped(h, "line", branch, size, fill=180, width=max(1, w - 1) * 4)
            _wrapped(d, "line", branch, size, fill=255, width=max(1, w - 1))
    return _array(dark, 0.6), _array(halo, 2.5)


# ---------------------------------------------------------------------------
# Asfalto
# ---------------------------------------------------------------------------
def asfalto(size: int = SIZE) -> Image.Image:
    """Asfalto viejo (6 m): parches, piel de cocodrilo, grietas largas desgranadas, árido
    suelto, baches pequeños y manchas de aceite y hollín."""
    rng = np.random.default_rng(101)
    v = 0.72 + 0.16 * (_noise(size, 1.0, 102) - 0.5) + 0.1 * (_noise(size, 2.6, 103) - 0.5)
    v += _speckle(size, 104, 9000, (0.7, 1.6), (-0.13, 0.1))
    # Donde el ligante se ha ido queda el árido suelto: más claro y más basto.
    ravel = _smoothstep(0.56, 0.68, _noise(size, 1.7, 105))
    v += ravel * (0.05 + _speckle(size, 106, 14000, (1.0, 2.4), (-0.18, 0.16)))
    # Parches de reparaciones viejas, cada uno de su tono, con la junta sellada y alguno roto.
    edges, ed = _mask(size)
    tones = np.zeros((size, size))
    for k in range(8):
        x, y = rng.uniform(0, size, 2)
        w, hgt = rng.uniform(90, 330), rng.uniform(70, 220)
        corners = [(x, y), (x + w, y + rng.uniform(-6, 6)), (x + w + rng.uniform(-6, 6), y + hgt),
                   (x + rng.uniform(-6, 6), y + hgt)]
        one, od = _mask(size)
        _wrapped(od, "polygon", corners, size, fill=255)
        tones += _array(one) * rng.uniform(-0.12, 0.08)
        _wrapped(ed, "line", corners + [corners[0]], size, fill=255, width=3)
    v += np.clip(tones, -0.12, 0.08)
    v -= 0.22 * _array(edges, 0.8)
    # Piel de cocodrilo: celdas de 12-25 cm en las zonas más castigadas.
    d1, d2, _ = _voronoi(size, 34, 107)
    alligator = _smoothstep(0.42, 0.56, _noise(size, 2.2, 108))
    cells = (1.0 - _smoothstep(0.6, 2.2, d2 - d1)) * alligator
    v -= 0.42 * cells
    v += 0.04 * _smoothstep(2.2, 6.0, d2 - d1) * alligator * (_noise(size, 0.3, 109) - 0.3)
    # Grietas largas: de la helada y de la onda, con el borde desgranado.
    dark, halo = _cracks(size, 110, 30, (200, 800), (2, 6))
    v += 0.06 * halo - 0.5 * dark
    # Grietas viejas selladas con brea: bandas oscuras y brillantes que serpentean.
    tar, _ = _cracks(size, 113, 6, (300, 900), (9, 14), branches=0.2)
    v -= 0.2 * tar
    # Baches pequeños: hoyo oscuro con piedras sueltas y el canto roto más claro.
    holes, hd = _mask(size)
    rims, rd = _mask(size)
    for _ in range(12):
        x, y = rng.uniform(0, size, 2)
        r = rng.uniform(14, 46)
        pts = []
        for k in range(12):
            a = k / 12 * math.tau
            rr = r * rng.uniform(0.65, 1.15)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        _wrapped(rd, "polygon", [((px - x) * 1.25 + x, (py - y) * 1.25 + y) for px, py in pts], size, fill=255)
        _wrapped(hd, "polygon", pts, size, fill=255)
    hole = _array(holes, 1.0)
    v += 0.07 * (_array(rims, 1.5) - hole)
    v = v * (1.0 - hole) + hole * (0.36 + _speckle(size, 111, 3000, (1.0, 2.5), (-0.1, 0.25)))
    # Manchas de aceite y de hollín.
    v -= 0.16 * _blotches(size, 112, 9, (25, 90), 12.0) * (0.6 + 0.8 * _noise(size, 0.6, 114))
    return _to_image(v).filter(ImageFilter.SMOOTH)


# ---------------------------------------------------------------------------
# Losas, granito y adoquín
# ---------------------------------------------------------------------------
def _slabs(size: int, seed: int, rows: int, columns: int, bond: bool, joint: int, speckle: float,
           cracked: float, broken: float, missing: float) -> Image.Image:
    """Losas en filas (a matajunta si `bond`): cada una de su tono; unas partidas, otras
    rotas en pedazos, alguna que falta (queda la tierra) y alguna hundida, más oscura. Las
    juntas, abiertas y con verdín; los cantos, desportillados."""
    rng = np.random.default_rng(seed)
    grain = 0.07 * (_noise(size, 1.2, seed + 1) - 0.5)
    grain += speckle * (_noise(size, 0.2, seed + 2) - 0.5)
    tone = np.zeros((size, size))
    soil = np.zeros((size, size))
    h = size / rows
    w = size / columns
    fractures, fd = _mask(size)
    broken_mask = np.zeros((size, size))
    for r in range(rows):
        offset = (w / 2.0) if bond and r % 2 else 0.0
        for c in range(columns):
            fate = rng.random()
            value = rng.uniform(0.68, 0.97)
            if fate < missing:
                value = -1.0
            elif fate < missing + 0.04:
                value *= 0.78
            start = int(round(c * w + offset))
            cols = [x % size for x in range(start, start + int(round(w)))]
            rows_px = slice(int(r * h), int((r + 1) * h))
            if value < 0.0:
                soil[rows_px, cols] = 1.0
                continue
            tone[rows_px, cols] = value
            x0, y0 = c * w + offset, r * h
            if fate > 1.0 - broken:
                # Rota en pedazos: los trozos (las celdas de un Voronoi dentro de la losa) se
                # hunden o se levantan cada uno a su manera.
                broken_mask[rows_px, cols] = 1.0
            elif fate > 1.0 - broken - cracked:
                line = _crack(rng, (x0 + rng.uniform(0.0, 0.3) * w, y0 + rng.uniform(0.2, 0.8) * h),
                              w * rng.uniform(0.6, 1.1), rng.uniform(-0.5, 0.5))
                _wrapped(fd, "line", line, size, fill=255, width=1)
    v = tone + grain
    v -= 0.3 * _array(fractures, 0.5)
    if broken_mask.any():
        d1, d2, ident = _voronoi(size, max(32, int(min(w, h) / 2.2)), seed + 7)
        pieces = np.random.default_rng(seed + 8).uniform(-0.16, 0.08, ident.max() + 1)[ident]
        edge = 1.0 - _smoothstep(0.8, 2.6, d2 - d1)
        v += broken_mask * (pieces - 0.38 * edge)
    # Juntas abiertas, sucias y con verdín.
    joints, jd = _mask(size)
    for r in range(rows + 1):
        y = r * h + rng.uniform(-0.8, 0.8)
        _wrapped(jd, "line", [(0, y), (size, y)], size, fill=255, width=joint)
    for r in range(rows):
        offset = (w / 2.0) if bond and r % 2 else 0.0
        for c in range(columns + 1):
            x = c * w + offset + rng.uniform(-0.8, 0.8)
            _wrapped(jd, "line", [(x, r * h), (x, (r + 1) * h)], size, fill=255, width=joint)
    moss = _smoothstep(0.45, 0.7, _noise(size, 1.4, seed + 3))
    jointmask = _array(joints, 0.7)
    v = v * (1.0 - jointmask) + jointmask * (0.36 - 0.1 * moss)
    # Cantos desportillados.
    chips, cd = _mask(size)
    for _ in range(int(rows * columns * 1.2)):
        x = rng.integers(0, columns + 1) * w + rng.uniform(-2, 2)
        y = rng.uniform(0, size)
        s = rng.uniform(4, 16) * size / 1024
        _wrapped(cd, "polygon", [(x, y), (x + s * rng.uniform(0.6, 1.4), y + s * 0.3), (x + s * 0.2, y + s)], size,
                 fill=255)
    v -= 0.14 * _array(chips, 0.6)
    # Donde falta la losa queda la tierra helada, con piedras.
    dirt = 0.42 + 0.08 * (_noise(size, 1.6, seed + 4) - 0.5) + _speckle(size, seed + 5, 2500, (1.0, 3.0), (-0.1, 0.12))
    soil = _array(_to_image(soil), 1.2)
    v = v * (1.0 - soil) + dirt * soil
    v -= 0.12 * _blotches(size, seed + 6, 8, (20, 70), 10.0)
    return _to_image(v)


def losas(size: int = SIZE) -> Image.Image:
    """Losas de hormigón de 50 cm de las aceras del centro (2 m: 4 × 4)."""
    return _slabs(size, 201, 4, 4, False, 6, 0.06, 0.25, 0.2, 0.07)


def granito(size: int = SIZE) -> Image.Image:
    """Placas de granito a matajunta (2 m: placas de 1 × 0,5 m), con su grano: las plazas
    (a doble escala) y los peldaños."""
    img = _slabs(size, 301, 4, 2, True, 4, 0.16, 0.25, 0.15, 0.04)
    v = np.array(img) / 255.0 + _speckle(size, 302, 16000, (0.6, 1.6), (-0.14, 0.08))
    v -= 0.08 * _smoothstep(0.55, 0.75, _noise(size, 1.8, 303))
    return _to_image(v)


def adoquin(size: int = SIZE) -> Image.Image:
    """Adoquines de granito en hileras (2 m): piedras de 10-18 cm redondeadas por el uso;
    alguna hundida y algún hueco donde falta la piedra."""
    rng = np.random.default_rng(401)
    img = Image.new("L", (size, size), int(255 * 0.34))
    d = ImageDraw.Draw(img)
    rows = 16
    row = size / rows
    unit = size / 512.0
    for r in range(rows):
        lengths = rng.uniform(26 * unit, 46 * unit, int(round(size / (36.0 * unit))))
        lengths *= size / lengths.sum()
        x = rng.uniform(0, size)
        for length in lengths:
            fate = rng.random()
            if fate < 0.04:
                x += length
                continue
            tone = int(255 * rng.uniform(0.66, 0.95) * (0.75 if fate < 0.1 else 1.0))
            y0, y1 = r * row + 2.0 * unit, (r + 1) * row - 2.0 * unit
            x0, x1 = x + 1.5 * unit, x + length - 1.5 * unit
            c = 3 * unit
            corners = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1),
                       (x0, y1 - c), (x0, y0 + c)]
            _wrapped(d, "polygon", corners, size, fill=tone)
            x += length
    v = np.array(img) / 255.0 + 0.06 * (_noise(size, 0.4, 402) - 0.5)
    v -= 0.1 * _blotches(size, 403, 8, (20, 80), 10.0)
    return _to_image(v).filter(ImageFilter.SMOOTH)


# ---------------------------------------------------------------------------
# Bordillo, hormigón, grava y tierra
# ---------------------------------------------------------------------------
def bordillo(size: int = SIZE) -> Image.Image:
    """Bordillo de granito (1 m a lo largo): el grano, una junta por pieza, desconchones y
    alguna grieta."""
    rng = np.random.default_rng(504)
    v = 0.86 + 0.14 * (_noise(size, 0.3, 501) - 0.5) + _speckle(size, 502, 10000, (0.7, 1.8), (-0.12, 0.06))
    v += 0.07 * (_noise(size, 2.4, 503) - 0.5)
    chips, cd = _mask(size)
    for _ in range(26):
        x, y = rng.uniform(0, size, 2)
        s = rng.uniform(10, 50)
        pts = [(x + math.cos(a) * s * rng.uniform(0.4, 1.0), y + math.sin(a) * s * rng.uniform(0.3, 0.8))
               for a in np.linspace(0, math.tau, 7, endpoint=False)]
        _wrapped(cd, "polygon", pts, size, fill=255)
    chip = _array(chips, 1.0)
    v = v * (1.0 - chip) + chip * (0.62 + _speckle(size, 505, 3000, (0.8, 1.8), (-0.15, 0.1)))
    dark, _ = _cracks(size, 506, 5, (150, 500), (1, 2))
    v -= 0.4 * dark
    joint, jd = _mask(size)
    _wrapped(jd, "line", [(2, 0), (2, size)], size, fill=255, width=6)
    v -= 0.4 * _array(joint, 0.8)
    v -= 0.12 * _blotches(size, 507, 6, (30, 120), 14.0)
    return _to_image(v)


def hormigon(size: int = SIZE) -> Image.Image:
    """Hormigón soviético de mala calidad (3 m): manchas, poros, juntas y latiguillos del
    encofrado, desconchones con la armadura oxidada que chorrea, grietas con salitre y
    churretes de suciedad."""
    rng = np.random.default_rng(601)
    v = 0.8 + 0.14 * (_noise(size, 2.2, 602) - 0.5) + 0.06 * (_noise(size, 0.8, 603) - 0.5)
    v += _speckle(size, 604, 5000, (0.6, 2.2), (-0.24, -0.06))
    marks, md = _mask(size)
    for k in range(6):
        y = k * size / 6 + rng.uniform(-2, 2)
        _wrapped(md, "line", [(0, y), (size, y)], size, fill=150, width=2)
        for j in range(4):
            x = (j + 0.5) * size / 4 + rng.uniform(-3, 3)
            yy = y + size / 12
            _wrapped(md, "ellipse", (x - 5, yy - 5, x + 5, yy + 5), size, fill=255)
    v -= 0.2 * _array(marks, 0.6)
    # Desconchones: falta la piel, asoma el árido y, en algunos, la armadura oxidada.
    spalls, sd = _mask(size)
    rust, rd = _mask(size)
    for k in range(9):
        x, y = rng.uniform(0, size, 2)
        r = rng.uniform(20, 90)
        pts = [(x + math.cos(a) * r * rng.uniform(0.5, 1.1), y + math.sin(a) * r * rng.uniform(0.4, 0.9))
               for a in np.linspace(0, math.tau, 11, endpoint=False)]
        _wrapped(sd, "polygon", pts, size, fill=255)
        if k % 3 == 0:
            a = rng.uniform(-0.2, 0.2)
            bar = [(x - r * 0.8, y + math.sin(a) * r), (x + r * 0.8, y - math.sin(a) * r)]
            _wrapped(rd, "line", bar, size, fill=255, width=6)
            for _ in range(3):
                sx = x + rng.uniform(-r * 0.7, r * 0.7)
                streak = [(sx + rng.normal(0, 2), y + t) for t in np.linspace(0, rng.uniform(80, 260), 9)]
                _wrapped(rd, "line", streak, size, fill=140, width=int(rng.uniform(5, 12)))
    spall = _array(spalls, 1.2)
    rough = 0.6 + 0.1 * (_noise(size, 0.6, 608) - 0.5) + _speckle(size, 605, 9000, (1.0, 3.2), (-0.24, 0.16))
    rim = np.clip(_array(spalls, 4.0) - spall, 0.0, 1.0)
    v = v * (1.0 - spall) + spall * rough - 0.3 * rim
    v -= 0.3 * _array(rust, 2.0)
    # Grietas con salitre (un halo claro que baja).
    dark, halo = _cracks(size, 606, 18, (150, 700), (1, 4))
    v += 0.08 * halo - 0.45 * dark
    # Churretes de suciedad desde arriba.
    streaks, std = _mask(size)
    for _ in range(18):
        x = rng.uniform(0, size)
        top = rng.uniform(0, size)
        line = [(x + rng.normal(0, 2.5), top + t) for t in np.linspace(0, rng.uniform(120, 420), 10)]
        _wrapped(std, "line", line, size, fill=int(rng.uniform(90, 200)), width=int(rng.uniform(6, 22)))
    v -= 0.12 * _array(streaks, 6.0)
    v -= 0.1 * _blotches(size, 607, 10, (40, 160), 20.0)
    return _to_image(v).filter(ImageFilter.SMOOTH)


def grava(size: int = SIZE) -> Image.Image:
    """Grava sucia de las sendas y del balasto (3 m): piedras sueltas, polvo de carbón y
    manchas de grasa."""
    v = 0.6 + 0.12 * (_noise(size, 1.8, 701) - 0.5)
    v += _speckle(size, 702, 30000, (1.4, 3.6), (0.05, 0.32))
    v += _speckle(size, 703, 9000, (1.0, 2.6), (-0.28, -0.1))
    v -= 0.18 * _blotches(size, 704, 10, (40, 160), 18.0)
    return _to_image(v).filter(ImageFilter.SMOOTH)


def tierra(size: int = SIZE) -> Image.Image:
    """Tierra helada (4 m): roderas, charcos helados (lisos y oscuros) y piedras."""
    rng = np.random.default_rng(805)
    v = 0.74 + 0.14 * (_noise(size, 2.4, 801) - 0.5) + 0.07 * (_noise(size, 1.0, 802) - 0.5)
    v += _speckle(size, 803, 2400, (1.4, 3.6), (-0.15, 0.12))
    ruts, rd = _mask(size)
    for k in range(2):
        y = rng.uniform(0, size)
        line = [(x, y + 25 * math.sin(x / size * math.tau * 2 + k)) for x in np.linspace(0, size, 40)]
        _wrapped(rd, "line", line, size, fill=255, width=22)
        _wrapped(rd, "line", [(x, py + 130) for x, py in line], size, fill=255, width=22)
    v -= 0.1 * _array(ruts, 6.0)
    ponds = _blotches(size, 804, 5, (30, 90), 4.0)
    v = v * (1.0 - ponds) + ponds * (0.52 + 0.04 * _noise(size, 0.5, 806))
    return _to_image(v).filter(ImageFilter.SMOOTH)


def derrumbe(size: int = SIZE) -> Image.Image:
    """Tierra revuelta de un socavón (4 m): cascotes angulosos de asfalto (oscuros), de
    hormigón (claros) y de ladrillo, en relieve (con luz y sombra) y medio enterrados,
    terrones, piedras sueltas, grietas de la helada y escarcha en lo hondo."""
    rng = np.random.default_rng(905)
    v = 0.56 + 0.17 * (_noise(size, 2.3, 901) - 0.5) + 0.1 * (_noise(size, 1.1, 902) - 0.5)
    v += 0.1 * _blotches(size, 912, 26, (12, 40), 3.0) - 0.08 * _blotches(size, 913, 18, (20, 60), 6.0)
    v += _speckle(size, 903, 4200, (1.0, 3.2), (-0.14, 0.12))
    relief = np.zeros((size, size))
    for cell, share, seed in ((34, 0.2, 906), (64, 0.16, 907), (120, 0.06, 914)):
        d1, d2, ident = _voronoi(size, cell, seed)
        cells = int(ident.max()) + 1
        present = rng.random(cells) < share
        tones = rng.choice([0.28, 0.34, 0.48, 0.56, 0.68, 0.76], cells) + rng.uniform(-0.05, 0.05, cells)
        # Lo que asoma de cada cascote: la tierra tapa el resto.
        buried = _noise(size, 3.4, seed + 20) > 0.6
        edge = d2 - d1
        inside = present[ident] & (edge > 1.5) & ~buried
        height = np.where(inside, np.minimum(edge, cell * 0.12) / (cell * 0.12), 0.0)
        relief = np.maximum(relief, height * (cell / 58.0) ** 0.5)
        grain = 0.07 * (_noise(size, 0.7, seed + 10) - 0.5)
        v = np.where(inside, tones[ident] + grain, v)
    # Luz del noroeste sobre el relieve de los cascotes: canto claro arriba, sombra abajo.
    relief = _array(_to_image(relief), 1.2)
    light = np.roll(np.roll(relief, 3, axis=0), 3, axis=1) - np.roll(np.roll(relief, -3, axis=0), -3, axis=1)
    v = v * (1.0 + 0.5 * light)
    dark, halo = _cracks(size, 909, 12, (50, 150), (1, 3), 0.5)
    v = v * (1.0 - 0.08 * halo) - 0.3 * dark
    frost = _blotches(size, 910, 6, (40, 100), 7.0)
    v = v * (1.0 - 0.35 * frost) + 0.35 * frost * (0.82 + 0.05 * _noise(size, 0.6, 911))
    return _to_image(v).filter(ImageFilter.SMOOTH)


def pintura(size: int = SIZE) -> Image.Image:
    """Pintura vial (2 m) que se ha ido a trozos con las ruedas y el hielo: el alfa dice
    lo que queda (lo demás se recorta y se ve el asfalto) y lo que queda está sucio."""
    worn = 0.6 * _noise(size, 2.2, 901) + 0.4 * _noise(size, 1.2, 903)
    scratches, sd = _mask(size)
    rng = np.random.default_rng(904)
    for _ in range(140):
        x, y = rng.uniform(0, size, 2)
        length = rng.uniform(20, 160)
        a = rng.normal(0.0, 0.25)
        _wrapped(sd, "line", [(x, y), (x + math.cos(a) * length, y + math.sin(a) * length)], size, fill=255,
                 width=int(rng.uniform(2, 7)))
    keep = (worn > 0.5) & (_array(scratches) < 0.5)
    lum = 0.88 + 0.06 * (_noise(size, 0.5, 902) - 0.5) - 0.14 * _blotches(size, 905, 10, (30, 120), 16.0)
    alpha = np.where(keep, 1.0, 0.0)
    rgba = np.stack([np.clip(lum, 0, 1) * 255, alpha * 255], axis=-1).astype(np.uint8)
    return Image.fromarray(rgba, "LA")


def matojo(size: int = 512) -> Image.Image:
    """Una mata de hierba seca de frente (RGBA): hojas finas que salen de abajo y se abren,
    unas dobladas, de pajizo a pardo, con alguna espiga. El alfa recorta las hojas."""
    rng = np.random.default_rng(1101)
    big = size * 2
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tones = [(178, 158, 112), (158, 136, 92), (132, 112, 76), (108, 92, 64), (190, 172, 128)]
    for k in range(78):
        base_x = big * (0.5 + rng.normal(0.0, 0.09))
        lean = rng.normal(0.0, 0.42)
        height = big * rng.uniform(0.35, 0.96)
        bend = rng.normal(0.0, 0.35)
        width = rng.uniform(6.0, 13.0)
        color = tones[k % len(tones)]
        points = []
        for j in range(13):
            f = j / 12
            x = base_x + math.sin(lean + bend * f * f) * height * f
            y = big - math.cos(lean + bend * f * f) * height * f
            points.append((x, y, width * (1.0 - f) + 1.2))
        for (x0, y0, w0), (x1, y1, w1) in zip(points, points[1:]):
            d.line([(x0, y0), (x1, y1)], fill=color + (255,), width=max(1, int(round((w0 + w1) / 2))))
        if rng.random() < 0.22:
            x, y, _ = points[-1]
            r = rng.uniform(5.0, 9.0)
            d.ellipse((x - r * 0.6, y - r * 1.8, x + r * 0.6, y + r * 0.6), fill=(96, 80, 56, 255))
    return img.resize((size, size), Image.LANCZOS)


TEXTURAS = {
    "asfalto.png": asfalto,
    "losas.png": losas,
    "granito.png": granito,
    "adoquin.png": adoquin,
    "bordillo.png": bordillo,
    "hormigon.png": hormigon,
    "grava.png": grava,
    "tierra.png": tierra,
    "derrumbe.png": derrumbe,
    "pintura.png": pintura,
    "matojo.png": matojo,
}
