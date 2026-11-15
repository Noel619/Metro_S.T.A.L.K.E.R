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

// --------------------------------------------------------------------------
// Caras de los protagonistas
// --------------------------------------------------------------------------
// El rostro es un dibujo 2D pegado sobre la cabeza 3D (README 9.3). Cada cara es
// una lámina de 4 × 2 casillas de 256 px, una por expresión; el material elige
// la casilla (scripts/actors/player_avatar.gd). La lámina envuelve el frente de
// la cabeza (116° de lado a lado), así que los ojos van más separados de lo que
// parece natural, y el centro queda libre: ahí está la nariz, que tiene volumen.
//
// El tono es el del juego: dos años bajo tierra. Ojos pequeños y cansados,
// ojeras, mejillas hundidas, la boca apretada. Nada de colorete ni de brillos.

const EYE_WHITE = "#D6CEBD";
const FACE_SHADOW = "#6B5548";
const FACE_DIRT = "#B29782";
const FACE_CELL = 256;
const FACE_COLUMNS = 4;
const FACE_EXPRESSIONS = ["neutro", "parpadeo", "esfuerzo", "miedo", "sonrisa", "sorpresa", "dolor", "cansado"];

/** Trazo de cara: más limpio que el del resto de ilustraciones. */
function faceInk(seed, extra = {}) {
    return { seed, stroke: INK, strokeWidth: 4.5, roughness: 0.45, bowing: 0.5, ...extra };
}

// Por expresión: apertura del ojo (px), radio del iris, cejas [interior, exterior].
const FACE_POSES = {
    neutro: { open: 9, iris: 7.5, brows: [4, 0] },
    parpadeo: { open: 0, iris: 0, brows: [4, 0] },
    esfuerzo: { open: 6, iris: 6, brows: [11, -4] },
    miedo: { open: 15, iris: 5.5, brows: [-11, 3] },
    sonrisa: { open: 8, iris: 7, brows: [1, 0] },
    sorpresa: { open: 14, iris: 6, brows: [-12, -9] },
    dolor: { open: -1, iris: 0, brows: [10, -2] },
    cansado: { open: 5.5, iris: 5.5, brows: [-1, 6] },
};

function faceSheet(style) {
    const drawables = [];
    FACE_EXPRESSIONS.forEach((expression, index) => {
        const ox = (index % FACE_COLUMNS) * FACE_CELL;
        const oy = Math.floor(index / FACE_COLUMNS) * FACE_CELL;
        const seed = style.seed + index * 40;
        const at = (x, y) => [ox + x, oy + y];
        const pose = FACE_POSES[expression];
        const ey = style.eyeY;
        const w = style.eyeW;
        [-1, 1].forEach((side, k) => {
            const ex = 128 + side * style.eyeGap;
            const s = seed + k * 13;
            const h = pose.open * style.eyeOpen;
            if (pose.open > 0) {
                const [x0, y0] = at(ex - w, ey);
                const [x1, y1] = at(ex + w, ey);
                const [cx] = at(ex, ey);
                drawables.push(
                    generator.path(
                        `M ${x0} ${y0} Q ${cx} ${y0 - h * 2.1} ${x1} ${y1} Q ${cx} ${y0 + h * 1.5} ${x0} ${y0} Z`,
                        faceInk(s, { fill: EYE_WHITE, fillStyle: "solid", stroke: EYE_WHITE, strokeWidth: 1, roughness: 0 }),
                    ),
                    generator.circle(cx + side * style.gaze, y0 - 0.5, Math.min(pose.iris, h * 1.15) * 2, faceInk(s + 1, { fill: INK, fillStyle: "solid", strokeWidth: 1 })),
                    // Párpado de arriba, pesado; el de abajo, apenas una línea.
                    generator.curve([at(ex - w - 3, ey + 2), at(ex, ey - h * 1.05 - 1), at(ex + w + 3, ey + 1)], faceInk(s + 2, { strokeWidth: style.lid })),
                    generator.curve([at(ex - w + 4, ey + 3), at(ex, ey + h * 0.72 + 1), at(ex + w - 3, ey + 2)], faceInk(s + 3, { strokeWidth: 2, stroke: FACE_SHADOW })),
                );
            } else if (pose.open === 0) {
                drawables.push(generator.curve([at(ex - w - 2, ey), at(ex, ey + 5), at(ex + w + 2, ey)], faceInk(s + 2, { strokeWidth: style.lid })));
            } else {
                // Ojos apretados, con arrugas en el rabillo.
                drawables.push(
                    generator.curve([at(ex - w, ey + 3), at(ex, ey - 3), at(ex + w, ey + 2)], faceInk(s + 2, { strokeWidth: style.lid })),
                    generator.line(...at(ex + side * (w + 3), ey - 1), ...at(ex + side * (w + 12), ey - 7), faceInk(s + 4, { strokeWidth: 2.5 })),
                    generator.line(...at(ex + side * (w + 3), ey + 3), ...at(ex + side * (w + 12), ey + 7), faceInk(s + 5, { strokeWidth: 2.5 })),
                );
            }
            // Ojeras.
            const bag = ey + Math.max(h, 4) * 0.72 + 8;
            drawables.push(generator.curve([at(ex - w + 2, bag - 2), at(ex - side * 2, bag + 3), at(ex + w - 3, bag - 3)], faceInk(s + 6, { strokeWidth: 2.6, stroke: FACE_SHADOW })));
            if (style.bags > 1 || expression === "cansado") {
                drawables.push(generator.curve([at(ex - w + 7, bag + 5), at(ex, bag + 8), at(ex + w - 9, bag + 3)], faceInk(s + 7, { strokeWidth: 2, stroke: FACE_SHADOW })));
            }
            // Cejas.
            drawables.push(
                generator.curve(
                    [
                        at(ex - side * style.browW * 0.5, style.browY + pose.brows[0]),
                        at(ex, style.browY + (pose.brows[0] + pose.brows[1]) / 2 - 2),
                        at(ex + side * style.browW * 0.5, style.browY + pose.brows[1]),
                    ],
                    faceInk(s + 8, { strokeWidth: style.browWeight, stroke: style.browColor }),
                ),
            );
            // Mejillas hundidas: tres rayas de lápiz bajo el pómulo.
            for (let n = 0; n < 3; n++) {
                const hx = 128 + side * (style.cheekX + n * 8);
                const hy = style.cheekY + n * 5;
                drawables.push(generator.line(...at(hx - side * 5, hy - 10), ...at(hx + side * 4, hy + 10), faceInk(s + 9 + n, { strokeWidth: 2.2, stroke: FACE_SHADOW })));
            }
        });
        // Marcas propias de cada uno: una cicatriz, una mancha de hollín.
        if (style.scar) {
            const [sx, sy] = style.scar;
            drawables.push(
                generator.line(...at(sx - 12, sy - 7), ...at(sx + 11, sy + 8), faceInk(seed + 60, { strokeWidth: 2.4, stroke: "#8A5A50" })),
                generator.line(...at(sx - 5, sy + 4), ...at(sx + 1, sy - 5), faceInk(seed + 61, { strokeWidth: 2, stroke: "#8A5A50" })),
                generator.line(...at(sx + 3, sy + 8), ...at(sx + 8, sy), faceInk(seed + 62, { strokeWidth: 2, stroke: "#8A5A50" })),
            );
        }
        style.dirt.forEach(([dx, dy, dw, dh], n) => {
            const [cx, cy] = at(dx, dy);
            drawables.push(generator.ellipse(cx, cy, dw, dh, faceInk(style.seed + 70 + n, { stroke: FACE_DIRT, fill: FACE_DIRT, fillStyle: "solid", strokeWidth: 2, roughness: 1.6 })));
        });
        // Boca.
        const my = style.mouthY;
        const line = (points, extra = {}) => drawables.push(generator.curve(points.map(([x, y]) => at(128 + x, my + y)), faceInk(seed + 30, extra)));
        const lip = () => line([[-7, 9], [0, 10], [7, 9]], { strokeWidth: 2, stroke: FACE_SHADOW });
        if (expression === "sonrisa") {
            line([[-15, 2], [0, 4], [17, -4]]);
            lip();
        } else if (expression === "esfuerzo") {
            line([[-16, 4], [0, -2], [16, 5]], { strokeWidth: 5 });
            drawables.push(generator.line(...at(128 - 20, my + 1), ...at(128 - 17, my + 9), faceInk(seed + 31, { strokeWidth: 2.2 })));
            drawables.push(generator.line(...at(128 + 20, my + 2), ...at(128 + 17, my + 10), faceInk(seed + 32, { strokeWidth: 2.2 })));
        } else if (expression === "dolor") {
            drawables.push(generator.linearPath([[-18, 3], [-9, -4], [0, 3], [9, -4], [18, 3]].map(([x, y]) => at(128 + x, my + y)), faceInk(seed + 30)));
        } else if (expression === "miedo") {
            const [cx, cy] = at(128, my + 3);
            drawables.push(generator.ellipse(cx, cy, 24, 11, faceInk(seed + 30, { fill: "#3A2224", fillStyle: "solid", roughness: 0.9, strokeWidth: 3.5 })));
        } else if (expression === "sorpresa") {
            const [cx, cy] = at(128, my + 4);
            drawables.push(generator.ellipse(cx, cy, 13, 16, faceInk(seed + 30, { fill: "#3A2224", fillStyle: "solid", strokeWidth: 3.5 })));
        } else if (expression === "cansado") {
            line([[-12, 2], [0, 1], [12, 4]]);
            lip();
        } else {
            line([[-14, 0], [0, 1], [14, 3]]);
            lip();
        }
    });
    return svg(FACE_CELL * FACE_COLUMNS, FACE_CELL * 2, drawables);
}

const FACE_CHICO = {
    seed: 500, eyeGap: 47, eyeY: 78, eyeW: 19, eyeOpen: 1.0, gaze: -1, lid: 5.5,
    browY: 52, browW: 46, browWeight: 6.5, browColor: "#221C19", bags: 1,
    cheekX: 74, cheekY: 142, mouthY: 194, scar: [50, 120], dirt: [[198, 176, 36, 12]],
};
const FACE_CHICA = {
    seed: 900, eyeGap: 47, eyeY: 79, eyeW: 21, eyeOpen: 1.15, gaze: 1, lid: 5,
    browY: 54, browW: 42, browWeight: 4.5, browColor: "#3F2F22", bags: 2,
    cheekX: 76, cheekY: 144, mouthY: 196, scar: null, dirt: [[52, 172, 34, 12]],
};

const ASSETS = {
    "cara_chico.svg": () => faceSheet(FACE_CHICO),
    "cara_chica.svg": () => faceSheet(FACE_CHICA),

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
