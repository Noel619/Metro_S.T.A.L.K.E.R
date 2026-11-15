"""Texturas de los pavimentos de la ciudad (la red de tránsito de la maqueta).

Grises que se multiplican por el color de cada superficie (lo pone la maqueta): el asfalto
con grietas y parches, las losas de las aceras del centro, el granito de las plazas y de
los peldaños, el adoquín de la ciudad vieja, el bordillo, el hormigón de los muros, la
grava de las sendas, la tierra de los caminos y la pintura gastada de los pasos de cebra.
Todas se enlosan sin costuras y salen siempre iguales (semillas fijas). Cada una cubre
los metros que dice CityTransit.TILE: el dibujo está hecho a esa escala.

Uso: las genera tools/textures/generate_textures.py en assets/textures/pavimentos/.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 512


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


def _crack(rng: np.random.Generator, start, length: float, angle: float, size: int) -> list:
    """Una grieta: camino quebrado que se tuerce poco a poco."""
    points = [tuple(start)]
    x, y = start
    steps = max(3, int(length / 6))
    for _ in range(steps):
        angle += rng.normal(0.0, 0.35)
        x += math.cos(angle) * length / steps
        y += math.sin(angle) * length / steps
        points.append((x, y))
    return points


def _to_image(values: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(values, 0.0, 1.0) * 255).astype(np.uint8), "L")


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


def asfalto(size: int = SIZE) -> Image.Image:
    """Asfalto viejo (4 m): árido, manchas, grietas y un par de parches."""
    rng = np.random.default_rng(101)
    v = 0.8 + 0.09 * (_noise(size, 1.0, 102) - 0.5) + 0.1 * (_noise(size, 2.8, 103) - 0.5)
    v += _speckle(size, 104, 2600, (0.6, 1.4), (-0.12, 0.1))
    img = _to_image(v)
    d = ImageDraw.Draw(img)
    for _ in range(2):
        x, y = rng.uniform(0, size, 2)
        w, h = rng.uniform(60, 140), rng.uniform(40, 90)
        tone = int(255 * rng.uniform(0.7, 0.76))
        corners = [(x, y), (x + w, y + rng.uniform(-3, 3)), (x + w + rng.uniform(-3, 3), y + h), (x, y + h)]
        _wrapped(d, "polygon", corners, size, fill=tone, outline=int(255 * 0.55))
    for _ in range(7):
        line = _crack(rng, rng.uniform(0, size, 2), rng.uniform(60, 220), rng.uniform(0, math.tau), size)
        _wrapped(d, "line", line, size, fill=int(255 * 0.42), width=2)
        if rng.random() < 0.6:
            branch = _crack(rng, line[len(line) // 2], rng.uniform(20, 70), rng.uniform(0, math.tau), size)
            _wrapped(d, "line", branch, size, fill=int(255 * 0.48), width=1)
    return img.filter(ImageFilter.SMOOTH)


def _slabs(size: int, seed: int, rows: int, columns: int, bond: bool, joint: int,
           speckle: float, cracked: float) -> Image.Image:
    """Losas en filas (con aparejo a matajunta si `bond`), cada una de su tono, con juntas,
    cantos gastados y alguna rota."""
    rng = np.random.default_rng(seed)
    grain = 0.06 * (_noise(size, 1.2, seed + 1) - 0.5)
    grain += speckle * (_noise(size, 0.2, seed + 2) - 0.5)
    tone = np.zeros((size, size))
    h = size / rows
    w = size / columns
    for r in range(rows):
        offset = (w / 2.0) if bond and r % 2 else 0.0
        for c in range(columns):
            value = rng.uniform(0.82, 0.97)
            start = int(round(c * w + offset))
            columns_of_slab = [x % size for x in range(start, start + int(round(w)))]
            tone[int(r * h):int((r + 1) * h), columns_of_slab] = value
    img = _to_image(tone + grain)
    d = ImageDraw.Draw(img)
    dark = int(255 * 0.42)
    for r in range(rows + 1):
        y = r * h + rng.uniform(-0.6, 0.6)
        _wrapped(d, "line", [(0, y), (size, y)], size, fill=dark, width=joint)
    for r in range(rows):
        offset = (w / 2.0) if bond and r % 2 else 0.0
        for c in range(columns + 1):
            x = c * w + offset + rng.uniform(-0.6, 0.6)
            _wrapped(d, "line", [(x, r * h), (x, (r + 1) * h)], size, fill=dark, width=joint)
            # Cantos desportillados y alguna losa partida.
            if rng.random() < 0.3:
                cx, cy = x + rng.uniform(2, 8), r * h + rng.uniform(2, 8)
                _wrapped(d, "polygon", [(x, r * h), (cx + 6, r * h), (x, cy + 6)], size, fill=int(255 * 0.6))
            if rng.random() < cracked:
                y0 = r * h + rng.uniform(0.2, 0.8) * h
                line = _crack(rng, (x, y0), w * rng.uniform(0.5, 1.0), rng.uniform(-0.6, 0.6), size)
                _wrapped(d, "line", line, size, fill=int(255 * 0.5), width=1)
    return img


def losas(size: int = SIZE) -> Image.Image:
    """Losas de hormigón de 50 cm de las aceras del centro (2 m: 4 × 4)."""
    return _slabs(size, 201, 4, 4, False, 3, 0.04, 0.12)


def granito(size: int = SIZE) -> Image.Image:
    """Placas de granito a matajunta (2 m: placas de 1 × 0,5 m), con su grano: las plazas
    (a doble escala) y los peldaños."""
    img = _slabs(size, 301, 4, 2, True, 2, 0.16, 0.05)
    v = np.array(img) / 255.0 + _speckle(size, 302, 5200, (0.4, 1.1), (-0.14, 0.08))
    return _to_image(v)


def adoquin(size: int = SIZE) -> Image.Image:
    """Adoquines de granito en hileras (2 m): piedras de 10-18 cm, redondeadas por el uso."""
    rng = np.random.default_rng(401)
    img = Image.new("L", (size, size), int(255 * 0.38))
    d = ImageDraw.Draw(img)
    row = size / 16.0
    for r in range(16):
        # Cada hilera da la vuelta justa a la tesela: los largos se reparten el ancho.
        lengths = rng.uniform(26, 46, int(round(size / 36.0)))
        lengths *= size / lengths.sum()
        x = rng.uniform(0, size)
        for length in lengths:
            tone = int(255 * rng.uniform(0.72, 0.95))
            y0, y1 = r * row + 2.0, (r + 1) * row - 2.0
            x0, x1 = x + 1.5, x + length - 1.5
            corners = [(x0 + 3, y0), (x1 - 3, y0), (x1, y0 + 3), (x1, y1 - 3), (x1 - 3, y1), (x0 + 3, y1),
                       (x0, y1 - 3), (x0, y0 + 3)]
            _wrapped(d, "polygon", corners, size, fill=tone)
            x += length
    v = np.array(img) / 255.0 + 0.05 * (_noise(size, 0.4, 402) - 0.5)
    return _to_image(v).filter(ImageFilter.SMOOTH)


def bordillo(size: int = SIZE) -> Image.Image:
    """Bordillo de granito (1 m a lo largo): el grano de la piedra y una junta por pieza."""
    v = 0.9 + 0.12 * (_noise(size, 0.3, 501) - 0.5) + _speckle(size, 502, 2600, (0.5, 1.2), (-0.12, 0.06))
    v += 0.05 * (_noise(size, 2.4, 503) - 0.5)
    img = _to_image(v)
    d = ImageDraw.Draw(img)
    _wrapped(d, "line", [(1, 0), (1, size)], size, fill=int(255 * 0.45), width=3)
    return img


def hormigon(size: int = SIZE) -> Image.Image:
    """Hormigón de muros y pretiles (2 m): manchas, poros y las marcas del encofrado."""
    rng = np.random.default_rng(601)
    v = 0.86 + 0.08 * (_noise(size, 2.2, 602) - 0.5) + 0.04 * (_noise(size, 0.8, 603) - 0.5)
    v += _speckle(size, 604, 900, (0.5, 1.6), (-0.2, -0.05))
    img = _to_image(v)
    d = ImageDraw.Draw(img)
    for k in range(4):
        y = k * size / 4 + rng.uniform(-1, 1)
        _wrapped(d, "line", [(0, y), (size, y)], size, fill=int(255 * 0.7), width=1)
    # Chorretones de óxido y humedad.
    for _ in range(6):
        x = rng.uniform(0, size)
        line = [(x + rng.normal(0, 1.5), y) for y in np.linspace(0, rng.uniform(60, 200), 8)]
        _wrapped(d, "line", line, size, fill=int(255 * 0.72), width=int(rng.uniform(2, 5)))
    return img.filter(ImageFilter.SMOOTH)


def grava(size: int = SIZE) -> Image.Image:
    """Grava de las sendas (3 m): piedrecitas sueltas sobre tierra."""
    v = 0.66 + 0.1 * (_noise(size, 1.8, 701) - 0.5)
    v += _speckle(size, 702, 9000, (1.0, 2.6), (0.05, 0.3))
    v += _speckle(size, 703, 3000, (0.8, 1.8), (-0.25, -0.1))
    return _to_image(v).filter(ImageFilter.SMOOTH)


def tierra(size: int = SIZE) -> Image.Image:
    """Tierra apisonada (4 m): terrones y piedras."""
    v = 0.76 + 0.12 * (_noise(size, 2.4, 801) - 0.5) + 0.06 * (_noise(size, 1.0, 802) - 0.5)
    v += _speckle(size, 803, 700, (1.0, 2.5), (-0.15, 0.12))
    return _to_image(v).filter(ImageFilter.SMOOTH)


def pintura(size: int = SIZE) -> Image.Image:
    """Pintura vial gastada (2 m): casi blanca, saltada a trozos por las ruedas y el hielo."""
    worn = _noise(size, 2.0, 901)
    v = np.where(worn > 0.62, 0.62, 0.95) + 0.04 * (_noise(size, 0.5, 902) - 0.5)
    return _to_image(v).filter(ImageFilter.SMOOTH)


TEXTURAS = {
    "asfalto.png": asfalto,
    "losas.png": losas,
    "granito.png": granito,
    "adoquin.png": adoquin,
    "bordillo.png": bordillo,
    "hormigon.png": hormigon,
    "grava.png": grava,
    "tierra.png": tierra,
    "pintura.png": pintura,
}
