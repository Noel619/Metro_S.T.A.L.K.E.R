// Genera las ilustraciones 2D del juego con aspecto dibujado a mano (rough.js).
//
// Uso: node generate.mjs            (desde tools/svg/, tras `npm ci`)
//
// Cada entrada de ASSETS es una función que devuelve el SVG completo. Todo es
// determinista: cada trazo lleva su semilla, así que el resultado no cambia
// entre ejecuciones. Los SVG se guardan en assets/ui/ y Godot los importa solos.
// El texto no va en los SVG: se pone en Godot con las tipografías del juego.

import rough from "roughjs";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
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

const GRAPHITE = "#3B3A40";
const RED_PENCIL = "#A8352E";
const BLUE_PENCIL = "#3A5A8C";
const NOTEBOOK = "#EFE6D2";
const GRID = "#9DB0BC";
const VIOLET = "#5B3F86";

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


// --------------------------------------------------------------------------
// Piezas de interfaz (F1-12). Los textos los pone Godot: cada pieza que lleva
// texto escribe al lado un .json con la posición, el tamaño, el giro y el tipo
// de letra de cada rótulo (manuscrita, maquina, rotulo o texto).
// --------------------------------------------------------------------------

const LABELS = {};

function pencil(seed, extra = {}) {
    return { seed, stroke: GRAPHITE, strokeWidth: 2, roughness: 1.4, bowing: 1.5, ...extra };
}

function svgRaw(width, height, body) {
    return (
        `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" ` +
        `viewBox="0 0 ${width} ${height}">\n${body}\n</svg>\n`
    );
}

// Cuaderno abierto: dos páginas de cuadros con margen y costura central.
function notebookSpread() {
    const W = 1600;
    const H = 1040;
    const parts = [];
    parts.push(`  <rect x="28" y="36" width="${W - 44}" height="${H - 52}" rx="10" fill="#000" opacity="0.28"/>`);
    const pages = [
        [40, 22, 792, 1000],
        [808, 22, 1560, 1000],
    ];
    const drawables = [];
    pages.forEach(([x0, y0, x1, y1], i) => {
        drawables.push(generator.polygon([[x0, y0 + 4], [x1, y0], [x1 - 2, y1], [x0 + 3, y1 - 3]],
            ink(200 + i, { fill: NOTEBOOK, fillStyle: "solid", strokeWidth: 1.5, roughness: 0.6, stroke: "#8E8470" })));
    });
    const body = drawables.map(toSvgPaths).join("\n");
    parts.push(body);
    const step = 20;
    pages.forEach(([x0, y0, x1, y1]) => {
        for (let x = x0 + 18; x < x1 - 8; x += step) {
            parts.push(`  <line x1="${x}" y1="${y0 + 14}" x2="${x}" y2="${y1 - 10}" stroke="${GRID}" stroke-width="1" opacity="0.55"/>`);
        }
        for (let y = y0 + 18; y < y1 - 8; y += step) {
            parts.push(`  <line x1="${x0 + 10}" y1="${y}" x2="${x1 - 6}" y2="${y}" stroke="${GRID}" stroke-width="1" opacity="0.55"/>`);
        }
    });
    parts.push(`  <line x1="768" y1="30" x2="768" y2="996" stroke="#C9787A" stroke-width="1.6" opacity="0.7"/>`);
    parts.push(`  <line x1="1536" y1="26" x2="1536" y2="996" stroke="#C9787A" stroke-width="1.6" opacity="0.7"/>`);
    parts.push(`  <rect x="788" y="20" width="24" height="982" fill="#8E8470" opacity="0.35"/>`);
    for (let y = 60; y < 990; y += 46) {
        parts.push(`  <line x1="800" y1="${y}" x2="800" y2="${y + 14}" stroke="#5E5546" stroke-width="2"/>`);
    }
    return svgRaw(W, H, parts.join("\n"));
}

// El mapa que dibujó el jugador: La Plaza y el borde de Los Bloques, sacados del
// plano de la ciudad (data/ciudad/plano.json) y dibujados a lápiz.
function notebookMap() {
    const W = 1600;
    const H = 1040;
    const plan = JSON.parse(readFileSync(join(ROOT, "data", "ciudad", "plano.json"), "utf8"));
    const box = { x0: 150, x1: 620, y0: 160, y1: 600 };
    const scale = 1.5;
    const px = (x, y) => [56 + (x - box.x0) * scale, 975 - (y - box.y0) * scale];
    const drawables = [];
    const labels = [];
    const label = (text, x, y, size = 26, rot = 0, font = "manuscrita", color = GRAPHITE) =>
        labels.push({ text, x: Math.round(x), y: Math.round(y), size: Math.round(size * 1.3), rot, font, color });
    let seed = 300;
    for (const e of plan.edificios) {
        const [cx, cy] = e.centro;
        if (cx < box.x0 || cx > box.x1 || cy < box.y0 || cy > box.y1) continue;
        if (![1, 2, 3].includes(e.zona)) continue;
        if (["cobertizo", "transformador", "tienda_campana"].includes(e.tipo)) continue;
        const ring = e.huella[0].map(([x, y]) => px(x, y));
        const important = ["BLQ-07", "PLZ-06", "PLZ-07", "PLZ-05", "AVM-01"].includes(e.id);
        drawables.push(generator.polygon(ring, pencil(seed++, { strokeWidth: important ? 2.6 : 1.8 })));
        if (e.id === "BLQ-07") {
            drawables.push(generator.polygon(ring, pencil(seed++, {
                stroke: RED_PENCIL, fill: RED_PENCIL, fillStyle: "hachure", hachureGap: 7, fillWeight: 1.4, strokeWidth: 0,
            })));
        } else if (e.dano >= 2 || e.tipo === "garajes") {
            drawables.push(generator.polygon(ring, pencil(seed++, {
                fill: GRAPHITE, fillStyle: "hachure", hachureGap: 11, fillWeight: 0.8, strokeWidth: 0, hachureAngle: 60,
            })));
        }
    }
    // La plaza redonda y el monumento.
    const [pcx, pcy] = px(430, 330);
    drawables.push(generator.circle(pcx, pcy, 85 * 2 * scale, pencil(seed++, { strokeWidth: 1.6, roughness: 1.8 })));
    drawables.push(generator.circle(pcx, pcy, 30 * 2 * scale, pencil(seed++, { strokeWidth: 1.4 })));
    drawables.push(generator.circle(pcx, pcy, 12, pencil(seed++, { fill: GRAPHITE, fillStyle: "solid" })));
    // Paso subterráneo: cruz discontinua.
    drawables.push(generator.line(pcx - 120, pcy + 12, pcx + 130, pcy - 6, pencil(seed++, { strokeWidth: 1.2, strokeLineDash: [6, 6] })));
    // Tu salida: círculo verde de lápiz y flecha.
    const [ex, ey] = px(334, 296);
    drawables.push(generator.circle(ex, ey, 34, pencil(seed++, { stroke: "#2F6B45", strokeWidth: 3 })));
    // Ruta por los patios hasta la farmacia, con flechas.
    const route = [[334, 296], [305, 325], [290, 392], [240, 398], [200, 394], [180, 386]].map(([x, y]) => px(x, y));
    drawables.push(generator.curve(route, pencil(seed++, { stroke: BLUE_PENCIL, strokeWidth: 2.4, strokeLineDash: [10, 8] })));
    const [ax, ay] = route[route.length - 1];
    drawables.push(generator.linearPath([[ax + 16, ay - 10], [ax, ay], [ax + 18, ay + 8]], pencil(seed++, { stroke: BLUE_PENCIL, strokeWidth: 2.4 })));
    // Peligro sobre Mineros 7: triángulo rojo con su signo.
    const [dx, dy] = px(194, 400);
    drawables.push(generator.polygon([[dx, dy - 34], [dx + 30, dy + 18], [dx - 30, dy + 18]], pencil(seed++, { stroke: RED_PENCIL, strokeWidth: 3 })));
    drawables.push(generator.line(dx, dy - 16, dx, dy + 2, pencil(seed++, { stroke: RED_PENCIL, strokeWidth: 3.4 })));
    drawables.push(generator.circle(dx, dy + 10, 5, pencil(seed++, { stroke: RED_PENCIL, fill: RED_PENCIL, fillStyle: "solid" })));
    // Refugio en el banco (casita) y botín en los quioscos (cajitas).
    const [bx, by] = px(468, 452);
    drawables.push(generator.polygon([[bx - 14, by + 12], [bx - 14, by - 4], [bx, by - 18], [bx + 14, by - 4], [bx + 14, by + 12]],
        pencil(seed++, { stroke: "#2F6B45", strokeWidth: 2.4 })));
    for (const [kx, ky] of [[412, 403], [470, 252], [196, 82]]) {
        if (ky < box.y0) continue;
        const [qx, qy] = px(kx, ky);
        drawables.push(generator.rectangle(qx - 9, qy - 9, 18, 18, pencil(seed++, { strokeWidth: 2 })));
        drawables.push(generator.line(qx - 9, qy - 9, qx + 9, qy + 9, pencil(seed++, { strokeWidth: 1.4 })));
    }
    // Huellas de perro junto a la plaza de la estación.
    for (const [hx, hy] of [[230, 175], [248, 188], [262, 203]]) {
        const [fx, fy] = px(hx, hy);
        drawables.push(generator.circle(fx, fy, 8, pencil(seed++, { fill: GRAPHITE, fillStyle: "solid", strokeWidth: 1 })));
        for (const [ox, oy] of [[-6, -8], [-1, -11], [4, -11], [8, -7]]) {
            drawables.push(generator.circle(fx + ox, fy + oy, 3.5, pencil(seed++, { fill: GRAPHITE, fillStyle: "solid", strokeWidth: 0.8 })));
        }
    }
    // Brújula y escala.
    drawables.push(generator.line(700, 190, 700, 110, pencil(seed++, { strokeWidth: 2.4 })));
    drawables.push(generator.linearPath([[688, 126], [700, 108], [712, 126]], pencil(seed++, { strokeWidth: 2.4 })));
    drawables.push(generator.line(84, 990, 84 + 50 * scale, 990, pencil(seed++, { strokeWidth: 2.4 })));
    drawables.push(generator.line(84, 982, 84, 998, pencil(seed++)));
    drawables.push(generator.line(84 + 50 * scale, 982, 84 + 50 * scale, 998, pencil(seed++)));
    // Borrón de goma.
    drawables.push(generator.rectangle(560, 640, 120, 60, pencil(seed++, {
        stroke: "#B9B0A0", fill: "#E8DFCB", fillStyle: "solid", strokeWidth: 0.6, roughness: 2.6,
    })));
    // Página derecha: el bloque de Mineros 7 visto de frente, con sus ventanas.
    const fx0 = 930;
    const fy0 = 600;
    drawables.push(generator.rectangle(fx0, fy0, 470, 300, pencil(seed++, { strokeWidth: 2.4 })));
    for (let fl = 0; fl < 9; fl++) {
        for (let c = 0; c < 12; c++) {
            const wx = fx0 + 14 + c * 38;
            const wy = fy0 + 10 + fl * 31;
            const dark = (fl * 7 + c * 3) % 5 === 0;
            drawables.push(generator.rectangle(wx, wy, 22, 18, pencil(seed++, {
                strokeWidth: 1.2, roughness: 1.6, fill: dark ? GRAPHITE : undefined, fillStyle: "hachure", hachureGap: 4,
            })));
        }
    }
    drawables.push(generator.rectangle(fx0 + 60, fy0 + 250, 60, 50, pencil(seed++, {
        stroke: RED_PENCIL, strokeWidth: 3, fill: RED_PENCIL, fillStyle: "cross-hatch", hachureGap: 8,
    })));
    drawables.push(generator.curve([[fx0 + 340, fy0 + 120], [fx0 + 300, fy0 + 160], [fx0 + 330, fy0 + 210], [fx0 + 290, fy0 + 260]],
        pencil(seed++, { stroke: RED_PENCIL, strokeWidth: 2.6, strokeLineDash: [8, 6] })));
    // Símbolos de la leyenda (página derecha, arriba).
    const legend = [
        ["peligro", 900, 360],
        ["refugio", 900, 410],
        ["botin", 900, 460],
        ["ruta", 900, 510],
    ];
    for (const [kind, lx, ly] of legend) {
        if (kind === "peligro") {
            drawables.push(generator.polygon([[lx, ly - 14], [lx + 14, ly + 10], [lx - 14, ly + 10]], pencil(seed++, { stroke: RED_PENCIL, strokeWidth: 2.4 })));
        } else if (kind === "refugio") {
            drawables.push(generator.polygon([[lx - 12, ly + 10], [lx - 12, ly - 2], [lx, ly - 14], [lx + 12, ly - 2], [lx + 12, ly + 10]],
                pencil(seed++, { stroke: "#2F6B45", strokeWidth: 2.4 })));
        } else if (kind === "botin") {
            drawables.push(generator.rectangle(lx - 9, ly - 9, 18, 18, pencil(seed++, { strokeWidth: 2 })));
            drawables.push(generator.line(lx - 9, ly - 9, lx + 9, ly + 9, pencil(seed++, { strokeWidth: 1.4 })));
        } else {
            drawables.push(generator.line(lx - 16, ly, lx + 16, ly, pencil(seed++, { stroke: BLUE_PENCIL, strokeWidth: 2.4, strokeLineDash: [8, 6] })));
        }
    }
    // Rótulos (los escribe Godot con la letra manuscrita).
    label("LA PLAZA", 120, 70, 54, -2, "manuscrita_negrita");
    label("(desde la salida, 2.º día)", 124, 128, 26, -2);
    label("N", 690, 58, 34, 0, "manuscrita_negrita");
    label("50 pasos", 96, 996, 24, 0);
    label("salida", ex - 58, ey + 30, 28, -4, "manuscrita_negrita", "#2F6B45");
    label("plaza", pcx - 40, pcy - 90, 26, -6);
    label("¡INQUILINO!", dx - 70, dy + 34, 30, -3, "manuscrita_negrita", RED_PENCIL);
    label("farmacia", ax + 28, ay - 46, 24, -2, "manuscrita", BLUE_PENCIL);
    label("banco: cámara", bx - 50, by + 20, 24, -3, "manuscrita", "#2F6B45");
    label("= refugio", bx - 40, by + 44, 24, -3, "manuscrita", "#2F6B45");
    label("quioscos: vacíos", 380, 330, 22, 2);
    label("perros", 150, 870, 24, -8);
    label("avenida →", 520, 470, 28, -42);
    label("Mineros", 130, 735, 26, 0);
    label("Mineros 7 (de frente)", 930, 560, 30, -1, "manuscrita_negrita");
    label("farmacia: abajo a la izquierda", 940, 915, 24, -1, "manuscrita", RED_PENCIL);
    label("ruido en el hueco del ascensor →", 1150, 860, 22, -2, "manuscrita", RED_PENCIL);
    label("peligro", 930, 344, 24, 0);
    label("refugio", 930, 394, 24, 0);
    label("botín", 930, 444, 24, 0);
    label("ruta buena", 930, 494, 24, 0, "manuscrita", BLUE_PENCIL);
    label("Día 2", 900, 60, 40, -1, "manuscrita_negrita");
    label("· los perros cruzan la playa a las 18:10", 900, 120, 26, -1);
    label("· de noche nunca por Mineros", 900, 160, 26, -1);
    label("· la farmacia se ve desde el patio: 3 ventanas", 900, 200, 26, -1);
    label("· el banco cierra por dentro", 900, 240, 26, -1);
    label("¿y si papá entró por el sótano?", 980, 290, 26, -3, "manuscrita", BLUE_PENCIL);
    LABELS["cuaderno_mapa"] = { ancho: W, alto: H, rotulos: labels };
    return svg(W, H, drawables);
}

// Recibo del impuesto diario: papel fino, borde de arriba arrancado.
function receipt() {
    const W = 520;
    const H = 640;
    const top = [];
    for (let x = 0; x <= W; x += 20) top.push([x + 6, 30 + ((x * 37) % 13)]);
    const outline = [...top, [W - 6, H - 20], [10, H - 16]];
    const drawables = [
        generator.polygon(outline, ink(401, { fill: "#F4EEDD", fillStyle: "solid", strokeWidth: 1.4, stroke: "#9A9080", roughness: 0.7 })),
    ];
    for (const y of [150, 300, 360, 420, 480]) {
        drawables.push(generator.line(40, y, W - 40, y, ink(410 + y, { strokeWidth: 1, stroke: "#B8AE98", roughness: 0.4, strokeLineDash: [4, 5] })));
    }
    drawables.push(generator.curve([[300, 560], [340, 540], [380, 570], [430, 545], [460, 560]], ink(420, { strokeWidth: 2.4, stroke: BLUE_PENCIL })));
    LABELS["recibo"] = {
        ancho: W,
        alto: H,
        rotulos: [
            { text: "ADMINISTRACIÓN DE LA ESTACIÓN", x: 40, y: 60, size: 24, rot: 0, font: "maquina", color: INK },
            { text: "RECIBO Nº 0417", x: 40, y: 100, size: 30, rot: 0, font: "maquina", color: INK },
            { text: "Concepto: impuesto diario", x: 40, y: 172, size: 24, rot: 0, font: "maquina", color: INK },
            { text: "por el local del depósito", x: 40, y: 206, size: 24, rot: 0, font: "maquina", color: INK },
            { text: "Día ......... 14", x: 40, y: 270, size: 26, rot: 0, font: "maquina", color: INK },
            { text: "Importe ..... 35 ₽", x: 40, y: 330, size: 26, rot: 0, font: "maquina", color: INK },
            { text: "Debe ........ 0 ₽", x: 40, y: 390, size: 26, rot: 0, font: "maquina", color: INK },
            { text: "Firma del encargado:", x: 40, y: 520, size: 22, rot: 0, font: "maquina", color: INK },
        ],
    };
    return svg(W, H, drawables);
}

// Sello de tinta violeta: doble anillo gastado (el texto lo pone Godot en círculo).
function stamp() {
    const S = 300;
    const c = S / 2;
    const drawables = [
        generator.circle(c, c, 270, ink(501, { stroke: VIOLET, strokeWidth: 7, roughness: 2.2, bowing: 2 })),
        generator.circle(c, c, 186, ink(502, { stroke: VIOLET, strokeWidth: 4, roughness: 2.0 })),
        generator.polygon([[c, c - 26], [c + 8, c - 8], [c + 26, c - 8], [c + 12, c + 4], [c + 18, c + 22], [c, c + 12], [c - 18, c + 22], [c - 12, c + 4], [c - 26, c - 8], [c - 8, c - 8]],
            ink(503, { stroke: VIOLET, strokeWidth: 2, fill: VIOLET, fillStyle: "solid", roughness: 1.6 })),
    ];
    return svg(S, S, drawables);
}

// Ficha de encargo: cartulina pautada clavada con una chincheta.
function jobCard() {
    const W = 640;
    const H = 420;
    const drawables = [
        generator.rectangle(14, 18, W - 28, H - 30, ink(601, { fill: "#E9DDBF", fillStyle: "solid", strokeWidth: 1.6, stroke: "#8E8268", roughness: 0.8 })),
        generator.line(30, 84, W - 30, 84, ink(602, { stroke: "#B4423A", strokeWidth: 2, roughness: 0.5 })),
    ];
    for (let y = 130; y < H - 30; y += 44) {
        drawables.push(generator.line(30, y, W - 30, y, ink(610 + y, { stroke: "#8FA8BC", strokeWidth: 1.2, roughness: 0.4 })));
    }
    for (let k = 0; k < 5; k++) {
        drawables.push(generator.circle(440 + k * 34, 352, 22, pencil(620 + k, {
            stroke: RED_PENCIL, strokeWidth: 2.2, fill: k < 3 ? RED_PENCIL : undefined, fillStyle: "solid",
        })));
    }
    drawables.push(generator.circle(W / 2, 30, 30, ink(640, { fill: "#B4423A", fillStyle: "solid", strokeWidth: 2 })));
    drawables.push(generator.circle(W / 2 - 4, 26, 9, ink(641, { fill: "#E8A0A0", fillStyle: "solid", strokeWidth: 0 })));
    drawables.push(generator.circle(560, 230, 90, ink(642, { stroke: "#9A7A4E", strokeWidth: 3, roughness: 2.4 })));
    LABELS["ficha_encargo"] = {
        ancho: W,
        alto: H,
        rotulos: [
            { text: "ENCARGO", x: 34, y: 34, size: 40, rot: 0, font: "rotulo", color: "#B4423A" },
            { text: "de: Vera, la del puesto de té", x: 250, y: 46, size: 26, rot: 0, font: "manuscrita", color: GRAPHITE },
            { text: "Antibióticos (los que haya).", x: 40, y: 98, size: 34, rot: -1, font: "manuscrita_negrita", color: GRAPHITE },
            { text: "Dice que en la farmacia de Mineros 7", x: 40, y: 142, size: 30, rot: -1, font: "manuscrita", color: GRAPHITE },
            { text: "aún queda algo. Es para su nieta.", x: 40, y: 186, size: 30, rot: -1, font: "manuscrita", color: GRAPHITE },
            { text: "Paga: 300 ₽ + té una semana", x: 40, y: 250, size: 30, rot: -1, font: "manuscrita_negrita", color: GRAPHITE },
            { text: "Antes del día 20", x: 40, y: 330, size: 28, rot: -1, font: "manuscrita", color: GRAPHITE },
            { text: "peligro", x: 330, y: 334, size: 26, rot: 0, font: "manuscrita", color: RED_PENCIL },
        ],
    };
    return svg(W, H, drawables);
}

ASSETS["cuaderno_doble.svg"] = notebookSpread;
ASSETS["cuaderno_mapa.svg"] = notebookMap;
ASSETS["recibo.svg"] = receipt;
ASSETS["sello.svg"] = stamp;
ASSETS["ficha_encargo.svg"] = jobCard;

mkdirSync(OUT_DIR, { recursive: true });
for (const [name, build] of Object.entries(ASSETS)) {
    const path = join(OUT_DIR, name);
    writeFileSync(path, build());
    console.log(`  ${relative(ROOT, path)}`);
}
for (const [name, data] of Object.entries(LABELS)) {
    const path = join(OUT_DIR, `${name}.json`);
    writeFileSync(path, JSON.stringify(data, null, 1) + "\n");
    console.log(`  ${relative(ROOT, path)}`);
}
console.log(`${Object.keys(ASSETS).length} ilustraciones generadas.`);
