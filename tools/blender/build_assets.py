"""Genera todos los modelos 3D a partir de las recetas.

Uso:
    python3 tools/blender/build_assets.py            # todos los modelos
    python3 tools/blender/build_assets.py caja_carton  # solo los que se indiquen
    python3 tools/blender/build_assets.py --list     # lista los modelos

Cada archivo de ``recipes/`` define ``models() -> dict[nombre, constructor]``.
Cada constructor crea la raíz del modelo en una escena vacía y este script la
exporta a ``assets/models/<nombre>.glb``. Godot la importa sola (ver
tools/godot/post_import.gd).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUTPUT_DIR = ROOT / "assets" / "models"
sys.path.insert(0, str(HERE))

import tumansk_bpy as tb  # noqa: E402  (necesita sys.path)


def load_recipes() -> dict:
    builders = {}
    for path in sorted((HERE / "recipes").glob("*.py")):
        spec = importlib.util.spec_from_file_location(f"recipes.{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, builder in module.models().items():
            if name in builders:
                raise SystemExit(f"Modelo duplicado: {name} ({path.name})")
            builders[name] = builder
    return builders


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="modelos a generar (por defecto, todos)")
    parser.add_argument("--list", action="store_true", help="lista los modelos y sale")
    args = parser.parse_args()

    builders = load_recipes()
    if args.list:
        print("\n".join(builders))
        return 0
    unknown = [name for name in args.names if name not in builders]
    if unknown:
        print(f"Modelos desconocidos: {', '.join(unknown)}", file=sys.stderr)
        return 1

    selected = args.names or list(builders)
    for name in selected:
        start = time.perf_counter()
        tb.reset_scene()
        root = builders[name]()
        vertices = sum(len(o.data.vertices) for o in root.children_recursive if o.type == "MESH" and not tb.is_collision(o))
        path = OUTPUT_DIR / f"{name}.glb"
        tb.export_glb(root, path)
        elapsed = time.perf_counter() - start
        print(f"  {name:<28} {vertices:>6} vértices  {path.stat().st_size / 1024:>7.1f} KB  {elapsed:4.1f} s")
    print(f"{len(selected)} modelos en {OUTPUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
