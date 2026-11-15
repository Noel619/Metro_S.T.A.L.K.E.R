// Genera las ilustraciones 2D del juego con aspecto dibujado a mano (rough.js).
//
// Uso: node generate.mjs            (desde tools/svg/, tras `npm ci`)
//
// Cada entrada de ASSETS es una función que devuelve el SVG completo. Todo es
// determinista: cada trazo lleva su semilla, así que el resultado no cambia
// entre ejecuciones. Los SVG se guardan en assets/ui/ y Godot los importa solos.
// El texto no va en los SVG: se pone en Godot con las tipografías del juego.

import rough from "roughjs";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..");
const OUT_DIR = join(ROOT, "assets", "ui");

// Paleta (docs/ESTILO.md).
const INK = "#1B1A22";
const PAPER = "#F2E6CF";
const CARDBOARD = "#C9A276";
const AMBER = "#E8A33D";

const generator = rough.generator();

/** Opciones comunes de trazo: tinta, algo de temblor y curvatura. */
function ink(seed, extra = {}) {
    return { seed, stroke: INK, strokeWidth: 3, roughness: 1.1, bowing: 1.2, ...extra };
}

/** Convierte un dibujo de rough.js en elementos <path>. */
function toSvgPaths(drawable) {
    return generator
        .toPaths(drawable)
        .map(
            (p) =>
                `  <path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" ` +
                `fill="${p.fill ?? "none"}" stroke-linecap="round" stroke-linejoin="round"/>`,
        )
        .join("\n");
}

function svg(width, height, drawables) {
    const body = drawables.map(toSvgPaths).join("\n");
    return (
        `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" ` +
        `viewBox="0 0 ${width} ${height}">\n${body}\n</svg>\n`
    );
}

const ASSETS = {
    // Etiqueta de precio de cartón, con su agujero y el cordel.
    "etiqueta_precio.svg": () =>
        svg(256, 128, [
            generator.polygon(
                [
                    [42, 14],
                    [240, 14],
                    [240, 114],
                    [42, 114],
                    [14, 64],
                ],
                ink(11, { fill: CARDBOARD, fillStyle: "solid" }),
            ),
            generator.polygon(
                [
                    [42, 14],
                    [240, 14],
                    [240, 114],
                    [42, 114],
                    [14, 64],
                ],
                ink(12, { fill: INK, fillStyle: "hachure", hachureGap: 14, hachureAngle: -40, fillWeight: 1, strokeWidth: 0 }),
            ),
            generator.circle(46, 64, 16, ink(13, { fill: PAPER, fillStyle: "solid" })),
            generator.curve(
                [
                    [46, 64],
                    [26, 40],
                    [10, 30],
                    [2, 10],
                ],
                ink(14, { strokeWidth: 2.5 }),
            ),
        ]),

    // Iconos de interacción: aparecen junto al punto de mira.
    "icono_lupa.svg": () =>
        svg(128, 128, [
            generator.circle(52, 52, 58, ink(21, { strokeWidth: 7, fill: PAPER, fillStyle: "solid" })),
            generator.line(74, 74, 112, 112, ink(22, { strokeWidth: 11 })),
        ]),

    "icono_mano.svg": () =>
        svg(128, 128, [
            generator.path(
                "M38 112 L38 62 Q38 54 46 54 L46 30 Q46 22 54 22 Q62 22 62 30 L62 52 L62 22 " +
                    "Q62 14 70 14 Q78 14 78 22 L78 52 L78 26 Q78 18 86 18 Q94 18 94 26 L94 58 " +
                    "L94 42 Q94 34 101 34 Q108 34 108 42 L108 82 Q108 114 80 118 L50 118 Q38 118 38 112 Z",
                ink(31, { strokeWidth: 6, fill: PAPER, fillStyle: "solid" }),
            ),
        ]),

    "icono_punto.svg": () =>
        svg(32, 32, [generator.circle(16, 16, 9, ink(41, { strokeWidth: 2, fill: INK, fillStyle: "solid" }))]),

    // Telaraña colgando de una esquina del techo (el anclaje es el centro de arriba).
    "telarana.svg": () => {
        const web = "#DCD6C6";
        const anchor = [256, 0];
        const drawables = [];
        const spokes = 9;
        const ends = [];
        for (let k = 0; k < spokes; k++) {
            const angle = Math.PI * (0.06 + (0.88 * k) / (spokes - 1));
            const length = 180 + ((k * 37) % 60);
            const end = [anchor[0] + Math.cos(angle) * length * 1.3, anchor[1] + Math.sin(angle) * length];
            ends.push({ angle, length });
            drawables.push(generator.line(anchor[0], anchor[1], end[0], end[1], ink(60 + k, { stroke: web, strokeWidth: 1.6, roughness: 0.8 })));
        }
        for (let ring = 1; ring <= 6; ring++) {
            for (let k = 0; k < spokes - 1; k++) {
                if ((ring * 7 + k * 3) % 11 === 0) continue; // hilos rotos
                const f = ring / 7;
                const a = ends[k];
                const b = ends[k + 1];
                const p1 = [anchor[0] + Math.cos(a.angle) * a.length * f * 1.3, anchor[1] + Math.sin(a.angle) * a.length * f];
                const p2 = [anchor[0] + Math.cos(b.angle) * b.length * f * 1.3, anchor[1] + Math.sin(b.angle) * b.length * f];
                const mid = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 8 + ring * 2];
                drawables.push(generator.curve([p1, mid, p2], ink(100 + ring * 13 + k, { stroke: web, strokeWidth: 1.3, roughness: 0.6 })));
            }
        }
        drawables.push(generator.curve([[180, 120], [176, 170], [182, 230]], ink(150, { stroke: web, strokeWidth: 1.2 })));
        return svg(512, 256, drawables);
    },

    // Hoja de papel suelta, arrugada y garabateada.
    "papel_suelto.svg": () =>
        svg(256, 320, [
            generator.polygon(
                [
                    [18, 14],
                    [130, 6],
                    [238, 18],
                    [246, 160],
                    [234, 306],
                    [120, 314],
                    [12, 300],
                    [22, 150],
                ],
                ink(71, { fill: PAPER, fillStyle: "solid", strokeWidth: 2.5 }),
            ),
            generator.line(22, 150, 246, 160, ink(72, { strokeWidth: 1, stroke: "#B9AE96" })),
            ...[60, 92, 124, 196, 228, 260].map((y, i) =>
                generator.curve(
                    [
                        [40, y],
                        [90, y - 6 + (i % 3) * 4],
                        [150, y + 4],
                        [200 - (i % 2) * 40, y - 2],
                    ],
                    ink(80 + i, { strokeWidth: 2, roughness: 1.6, stroke: "#3A3550" }),
                ),
            ),
        ]),

    // Marco de papel para notas y fichas.
    "marco_papel.svg": () =>
        svg(512, 320, [
            generator.rectangle(12, 12, 488, 296, ink(51, { fill: PAPER, fillStyle: "solid", strokeWidth: 4 })),
            generator.line(40, 92, 472, 90, ink(52, { strokeWidth: 1.5, stroke: AMBER })),
        ]),
};

mkdirSync(OUT_DIR, { recursive: true });
for (const [name, build] of Object.entries(ASSETS)) {
    const path = join(OUT_DIR, name);
    writeFileSync(path, build());
    console.log(`  ${relative(ROOT, path)}`);
}
console.log(`${Object.keys(ASSETS).length} ilustraciones generadas.`);
