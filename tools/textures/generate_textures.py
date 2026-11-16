"""Genera las texturas del estilo entintado (papel, tramado, rampas, ruido).

Uso: python3 tools/textures/generate_textures.py

Todas son repetibles sin costuras (se pueden enlosar) y deterministas (semillas
fijas). Se guardan en assets/textures/ y las usan los shaders de assets/shaders/.

- papel.png      grano y fibras de papel; se multiplica sobre la imagen.
- tramado.png    cuatro tonos de tramado a mano, uno por canal (R, G, B, A).
                 Cada tono contiene los trazos del anterior, para que el paso de
                 un tono a otro no "salte" (tonal art map).
- rampas.png     rampas del sombreado por bandas: una fila por tipo de material.
- ruido_trazo.png ruido suave en R y G para hacer temblar el contorno.
- grano.png      grano fino de película.
- nubes.png      ruido de nubes para el cielo: R forma grande, G detalle, B luz.
- humo.png       bocanada de humo, con borde irregular, para las partículas.
- madera_mesa.png tablero de madera oscura (fondo de las pruebas de interfaz).
- huella_bota.png y huella_perro.png  huellas en la nieve vieja (calcomanías):
                 el color es nieve pisada, más oscura; el alfa, la forma.
- pagina_cuadriculada.png  una página del cuaderno: cuadrícula de 5 mm trazada algo
                 suelta. No se enlosa: cubre la página entera (UV de 0 a 1).
- pavimentos/    los pavimentos de la ciudad (asfalto, losas, granito, adoquín, bordillo,
                 hormigón, grava, tierra, derrumbe y pintura vial): ver pavimentos.py.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "assets" / "textures"


def fft_noise(size: int, beta: float, seed: int) -> np.ndarray:
    """Ruido 1/f^beta sin costuras, normalizado a [0, 1]."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((size, size)))
    ky = np.fft.fftfreq(size)[:, None]
    kx = np.fft.fftfreq(size)[None, :]
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    noise = np.real(np.fft.ifft2(spectrum / k ** (beta / 2.0)))
    noise -= noise.min()
    return noise / noise.max()


def wrapped_lines(draw: ImageDraw.ImageDraw, size: int, points: list[tuple[float, float]], width: float, fill: int) -> None:
    """Dibuja una polilínea repitiéndola en las 9 posiciones del enlosado."""
    for dx in (-size, 0, size):
        for dy in (-size, 0, size):
            shifted = [(x + dx, y + dy) for x, y in points]
            draw.line(shifted, fill=fill, width=max(1, round(width)), joint="curve")


def stroke_points(rng: np.random.Generator, size: int, angle: float, length: float, bend: float) -> list[tuple[float, float]]:
    """Un trazo de lápiz: corto, algo curvado y con el ángulo un poco suelto."""
    x0, y0 = rng.uniform(0, size, 2)
    direction = np.array([math.cos(angle), math.sin(angle)])
    normal = np.array([-direction[1], direction[0]])
    points = []
    for t in np.linspace(0.0, 1.0, 8):
        offset = (t - 0.5) * length * direction + normal * bend * (4.0 * t * (1.0 - t))
        points.append((x0 + offset[0], y0 + offset[1]))
    return points


def paper(size: int = 1024) -> Image.Image:
    blotches = fft_noise(size, 2.6, seed=1)
    grain = fft_noise(size, 0.6, seed=2)
    base = 1.0 - 0.06 * blotches - 0.05 * grain
    fibers = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(fibers)
    rng = np.random.default_rng(3)
    for _ in range(1400):
        angle = rng.uniform(0, math.tau)
        points = stroke_points(rng, size, angle, rng.uniform(10, 40), rng.uniform(-6, 6))
        wrapped_lines(draw, size, points, 1, int(rng.integers(20, 60)))
    base -= 0.05 * (np.asarray(fibers, dtype=np.float64) / 255.0)
    return Image.fromarray(np.clip(base * 255.0, 0, 255).astype(np.uint8), "L")


def hatching(size: int = 512) -> Image.Image:
    """Cuatro tonos acumulativos de tramado, uno por canal."""
    scale = 2
    big = size * scale
    layers = [
        # (cantidad de trazos, ángulo, largo, grosor)
        (220, math.radians(-50), 90, 2.4),
        (260, math.radians(-46), 80, 2.4),
        (240, math.radians(40), 85, 2.2),
        (320, math.radians(-8), 70, 2.0),
    ]
    rng = np.random.default_rng(7)
    canvas = Image.new("L", (big, big), 255)
    draw = ImageDraw.Draw(canvas)
    channels = []
    for count, angle, length, width in layers:
        for _ in range(count):
            jitter = rng.normal(0.0, math.radians(4))
            points = stroke_points(rng, big, angle + jitter, length * scale * rng.uniform(0.7, 1.3), rng.uniform(-5, 5))
            wrapped_lines(draw, big, points, width * scale * rng.uniform(0.8, 1.2), int(rng.integers(0, 70)))
        channels.append(canvas.resize((size, size), Image.Resampling.LANCZOS))
    return Image.merge("RGBA", channels)


def ramps(width: int = 256) -> Image.Image:
    """Una fila por tipo de material: de sombra (izquierda) a luz (derecha).

    Filas: 0 neutro, 1 depósito, 2 superficie, 3 piel, 4 metal. Los tonos medios
    llevan tinte (más fríos o más cálidos según la fila).
    """
    rows = {
        # nombre: [(posición donde empieza la banda, color multiplicador)]
        # La primera banda es 0: ahí solo llega la luz ambiente (el color de la
        # sombra), así que las sombras propias y las proyectadas coinciden.
        "neutro": [(0.00, (0.0, 0.0, 0.0)), (0.40, (0.50, 0.50, 0.54)), (0.64, (1.00, 0.98, 0.95))],
        "deposito": [(0.00, (0.0, 0.0, 0.0)), (0.38, (0.56, 0.47, 0.50)), (0.62, (1.00, 0.95, 0.86))],
        "superficie": [(0.00, (0.0, 0.0, 0.0)), (0.42, (0.46, 0.52, 0.60)), (0.70, (0.96, 0.97, 0.98))],
        "piel": [(0.00, (0.0, 0.0, 0.0)), (0.30, (0.70, 0.52, 0.50)), (0.58, (1.00, 0.94, 0.88))],
        "metal": [(0.00, (0.0, 0.0, 0.0)), (0.45, (0.45, 0.48, 0.54)), (0.80, (1.00, 1.00, 1.00)), (0.95, (1.60, 1.55, 1.45))],
    }
    softness = 0.025
    image = np.zeros((len(rows), width, 3), dtype=np.float64)
    for row, bands in enumerate(rows.values()):
        for x in range(width):
            t = x / (width - 1)
            color = np.array(bands[0][1])
            for start, band_color in bands[1:]:
                weight = np.clip((t - start) / softness + 0.5, 0.0, 1.0)
                color = color * (1.0 - weight) + np.array(band_color) * weight
            image[row, x] = color
    # Los valores pueden superar 1 (brillo del metal): se guardan a la mitad.
    return Image.fromarray(np.clip(image * 0.5 * 255.0, 0, 255).astype(np.uint8), "RGB")


def boil_noise(size: int = 256) -> Image.Image:
    red = fft_noise(size, 2.2, seed=11)
    green = fft_noise(size, 2.2, seed=12)
    blue = np.zeros_like(red)
    rgb = np.stack([red, green, blue], axis=-1)
    return Image.fromarray((rgb * 255.0).astype(np.uint8), "RGB")


def grain(size: int = 256) -> Image.Image:
    noise = fft_noise(size, 0.2, seed=21)
    return Image.fromarray((noise * 255.0).astype(np.uint8), "L")


def clouds(size: int = 512) -> Image.Image:
    """Tres capas de ruido para las nubes del cielo (sin costuras)."""
    channels = [fft_noise(size, beta, seed) for beta, seed in ((3.6, 31), (2.6, 32), (3.0, 33))]
    rgb = np.stack(channels, axis=-1)
    return Image.fromarray((rgb * 255.0).astype(np.uint8), "RGB")


def smoke_puff(size: int = 256) -> Image.Image:
    """Bocanada de humo: mancha redonda de borde irregular, blanca con alfa."""
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2.0 - 1.0
    radius = np.sqrt(xx * xx + yy * yy)
    detail = fft_noise(size, 2.0, seed=41) - 0.5
    alpha = np.clip(1.0 - (radius + detail * 0.45) / 0.85, 0.0, 1.0) ** 1.6
    shade = 0.75 + 0.25 * fft_noise(size, 1.6, seed=42)
    rgba = np.stack([shade, shade, shade, alpha], axis=-1)
    return Image.fromarray((rgba * 255.0).astype(np.uint8), "RGBA")


def _footprint(size: tuple[int, int], shapes, seed: int, tread: bool) -> Image.Image:
    """Huella en nieve vieja: hundida (más oscura) con el borde algo levantado."""
    from PIL import ImageFilter

    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for kind, box in shapes:
        if kind == "ellipse":
            draw.ellipse(box, fill=255)
        else:
            draw.polygon(box, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2.2))
    rng = np.random.default_rng(seed)
    noise = fft_noise(max(w, h), 1.6, seed)[:h, :w]
    alpha = np.asarray(mask).astype(np.float32) / 255.0
    if tread:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        chevron = np.sin(yy * 0.5 + np.abs(xx - w / 2) * 0.32) > 0.15
        alpha = alpha * (0.72 + 0.28 * chevron)
    alpha = np.clip(alpha * (0.75 + 0.5 * noise) - rng.uniform(0, 0.05), 0, 1)
    rim = np.asarray(mask.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255.0
    rim = np.clip(rim - alpha, 0, 1)
    color = np.zeros((h, w, 4), np.float32)
    base = np.array([0.42, 0.40, 0.37])
    color[..., :3] = base * (0.85 + 0.3 * noise[..., None])
    color[..., :3] += rim[..., None] * 0.25
    color[..., 3] = np.clip(alpha * 0.85 + rim * 0.35, 0, 1)
    return Image.fromarray((color * 255).astype(np.uint8), "RGBA")


def table_wood(size: int = 512) -> Image.Image:
    """Tablero de madera oscura: vetas alargadas en horizontal y tablas separadas."""
    rng = np.random.default_rng(311)
    grain = fft_noise(size, 2.2, 312)
    fine = fft_noise(size, 1.2, 313)
    yy = np.arange(size, dtype=np.float32)[:, None]
    narrow = Image.fromarray((grain[:, :: size // 32] * 255).astype(np.uint8), "L")
    stretched = np.asarray(narrow.resize((size, size), Image.BICUBIC)).astype(np.float32) / 255.0
    rings = 0.5 + 0.5 * np.sin(yy * 0.35 + stretched * 9.0)
    tone = 0.55 + 0.25 * rings + 0.15 * fine
    board = (yy // (size / 4)).astype(int)
    tone *= 0.9 + 0.1 * rng.random(4)[board % 4]
    seams = (np.mod(yy, size / 4) < 2).astype(np.float32)
    tone *= 1.0 - 0.6 * seams
    base = np.array([0.36, 0.24, 0.16])
    rgb = np.clip(base * tone[..., None] * 1.15, 0, 1)
    return Image.fromarray((rgb * 255).astype(np.uint8), "RGB")


def boot_print() -> Image.Image:
    w, h = 128, 320
    shapes = [
        ("ellipse", (20, 8, 108, 158)),
        ("polygon", [(30, 118), (100, 118), (92, 206), (40, 206)]),
        ("ellipse", (34, 196, 96, 306)),
    ]
    return _footprint((w, h), shapes, seed=301, tread=True)


def paw_print() -> Image.Image:
    w, h = 128, 128
    shapes = [("ellipse", (36, 58, 92, 110))]
    for cx, cy in ((30, 40), (52, 22), (78, 22), (100, 40)):
        shapes.append(("ellipse", (cx - 11, cy - 13, cx + 11, cy + 13)))
    return _footprint((w, h), shapes, seed=302, tread=False)


def grid_page(width: int = 544, height: int = 808) -> Image.Image:
    """Página cuadriculada (136 × 202 mm a 4 px/mm). Casi blanca: el color del papel lo pone el modelo."""
    rng = np.random.default_rng(31)
    scale = 3  # se dibuja más grande y se reduce, para que las líneas queden suaves
    cell = 20 * scale
    ink = Image.new("L", (width * scale, height * scale), 0)
    draw = ImageDraw.Draw(ink)
    left, top = 2 * scale, 4 * scale
    for column in range(width * scale // cell + 1):
        x = left + column * cell + rng.uniform(-0.6, 0.6)
        tone = int(rng.uniform(165, 225))
        draw.line([(x + rng.uniform(-0.5, 0.5), 0), (x + rng.uniform(-0.5, 0.5), height * scale)], fill=tone, width=scale)
    for row in range(height * scale // cell + 1):
        y = top + row * cell + rng.uniform(-0.6, 0.6)
        tone = int(rng.uniform(165, 225))
        draw.line([(0, y + rng.uniform(-0.5, 0.5)), (width * scale, y + rng.uniform(-0.5, 0.5))], fill=tone, width=scale)
    lines = np.asarray(ink.resize((width, height), Image.LANCZOS), dtype=np.float64) / 255.0
    size = 1024
    fibre = fft_noise(size, 1.6, seed=32)[:height, :width]
    paper_tone = 0.94 + 0.06 * fibre
    blue = np.array([0.42, 0.55, 0.68])
    rgb = paper_tone[..., None] * (1.0 - lines[..., None] * (1.0 - blue[None, None, :]))
    return Image.fromarray((np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8), "RGB")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "papel.png": paper,
        "tramado.png": hatching,
        "rampas.png": ramps,
        "ruido_trazo.png": boil_noise,
        "grano.png": grain,
        "nubes.png": clouds,
        "humo.png": smoke_puff,
        "madera_mesa.png": table_wood,
        "huella_bota.png": boot_print,
        "huella_perro.png": paw_print,
        "pagina_cuadriculada.png": grid_page,
    }
    for name, build in outputs.items():
        image = build()
        path = OUT_DIR / name
        image.save(path, optimize=True)
        print(f"  {path.relative_to(ROOT)}  {image.size[0]}x{image.size[1]} {image.mode}")
    from pavimentos import TEXTURAS

    folder = OUT_DIR / "pavimentos"
    folder.mkdir(parents=True, exist_ok=True)
    for name, build in TEXTURAS.items():
        image = build()
        path = folder / name
        image.save(path, optimize=True)
        print(f"  {path.relative_to(ROOT)}  {image.size[0]}x{image.size[1]} {image.mode}")
    print(f"{len(outputs) + len(TEXTURAS)} texturas generadas.")


if __name__ == "__main__":
    main()
