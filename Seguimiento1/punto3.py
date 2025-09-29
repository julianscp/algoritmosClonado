# Proyecto/Seguimiento1/autores_top15.py
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
BIB_PATH = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos.bib"

OUT_DIR = Path(__file__).resolve().parent / "salidas"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GRAF_DIR = Path(__file__).resolve().parent / "graficas"
GRAF_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = GRAF_DIR / "top15_autores.png"
OUT_CSV = OUT_DIR / "top15_autores.csv"

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def split_bib_entries(text: str) -> list[str]:
    entries = []
    i = 0
    n = len(text)
    while i < n:
        at = text.find('@', i)
        if at == -1: break
        lb = text.find('{', at)
        if lb == -1: break
        depth = 1; j = lb + 1
        while j < n and depth > 0:
            c = text[j]
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            j += 1
        entry = text[at:j]
        if entry:
            if not entry.endswith("\n\n"):
                entry = entry.rstrip() + "\n\n"
            entries.append(entry)
        i = j
    return entries

# Captura robusta del campo author = { ... } o " ... "
RE_AUTHOR = re.compile(r'(?im)^\s*author\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|"([^"]*)")', re.M)

def get_author_raw(entry: str) -> str:
    m = RE_AUTHOR.search(entry)
    if not m: return ""
    val = (m.group(1) or m.group(2) or "").strip()
    # quitar llaves residuales
    val = re.sub(r'[\{\}]', '', val)
    # normalizar espacios
    val = re.sub(r'\s+', ' ', val).strip()
    return val

def split_authors(author_field: str) -> list[str]:
    # BibTeX separa autores por la palabra ' and '
    if not author_field:
        return []
    parts = [p.strip() for p in author_field.split(" and ") if p.strip()]
    return parts

def normalize_person(name: str) -> tuple[str, str]:
    """
    Devuelve (display_name, key_norm)
    - Si viene "Apellido, Nombre" → display = "Apellido, Nombre".
    - Si viene "Nombre Apellido" → display = "Apellido, Nombre".
    key_norm: para conteo sin sensibilidad a mayúsculas/espacios.
    """
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    if ',' in name:
        # "Last, First ..."
        last, first = name.split(',', 1)
        last = last.strip(); first = first.strip()
        display = f"{last}, {first}" if first else last
    else:
        # "First Middle Last" → asumimos último token como apellido
        tokens = name.split(' ')
        if len(tokens) == 1:
            display = tokens[0]
        else:
            last = tokens[-1]
            first = " ".join(tokens[:-1])
            display = f"{last}, {first}"
    key_norm = re.sub(r'\s+', ' ', display.lower()).strip()
    return display, key_norm

def main():
    text = read_text(BIB_PATH)
    entries = split_bib_entries(text)

    counter = Counter()
    name_map = {}  # key_norm -> display

    for e in entries:
        raw = get_author_raw(e)
        authors = split_authors(raw)
        for a in authors:
            display, key = normalize_person(a)
            if not key:
                continue
            counter[key] += 1
            # conserva una forma de visualización estable
            if key not in name_map:
                name_map[key] = display

    if not counter:
        print("[WARN] No se encontraron autores.")
        return

    # Top 15 por apariciones (descendente por conteo, desempate por nombre asc)
    top15 = sorted(counter.items(), key=lambda kv: (-kv[1], name_map[kv[0]]))[:15]
    # Estructura: [(key_norm, count), ...] -> mapeamos a (display, count)
    top15_disp = [(name_map[k], c) for k, c in top15]

    # Solicitan "ordenar de manera ascendente los quince primeros autores..."
    # Podemos interpretarlo de dos formas útiles:
    asc_by_name  = sorted(top15_disp, key=lambda t: t[0])      # asc por nombre
    asc_by_count = sorted(top15_disp, key=lambda t: (t[1], t[0]))  # asc por conteo (y nombre)

    # Mostrar en consola
    print("Top 15 autores (por apariciones, desc):")
    for name, c in top15_disp:
        print(f"{name:40s}  {c}")

    print("\nTop 15 autores — orden ASC por nombre:")
    for name, c in asc_by_name:
        print(f"{name:40s}  {c}")

    print("\nTop 15 autores — orden ASC por conteo:")
    for name, c in asc_by_count:
        print(f"{name:40s}  {c}")

    # Guardar CSV (top 15 por apariciones, más una vista ordenada asc por nombre)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        f.write("rank_by_count,name,count\n")
        for i, (name, c) in enumerate(top15_disp, 1):
            f.write(f"{i},{name},{c}\n")
        f.write("\nasc_by_name,name,count\n")
        for i, (name, c) in enumerate(asc_by_name, 1):
            f.write(f"{i},{name},{c}\n")

    # Gráfica de barras: top 15 ordenados ASC por conteo (como pide “ascendente”)
    names = [t[0] for t in asc_by_count]
    counts = [t[1] for t in asc_by_count]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, counts)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Apariciones")
    plt.title("Top 15 autores con más apariciones (orden ascendente)")
    # etiquetas encima de cada barra
    for bar, c in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height(),
                 str(c),
                 ha='center', va='bottom', fontsize=8, rotation=0)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=160)
    print(f"\nCSV guardado en: {OUT_CSV}")
    print(f"Gráfica guardada en: {OUT_PNG}")

if __name__ == "__main__":
    main()
