# Proyecto/Seguimiento1/ordenar_productos.py
import re
import sys
from pathlib import Path
from time import perf_counter

# importar algoritmos
sys.path.append(str(Path(__file__).resolve().parents[1] / "Algoritmos"))
import algoritmos as algo

import matplotlib.pyplot as plt  # opcional para ranking en barras

BASE_DIR = Path(__file__).resolve().parents[1]
# Entrada por defecto: el resultado filtrado
IN_BIB  = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos.bib"

# Salidas
OUT_DIR = Path(__file__).resolve().parent / "graficas"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_BIB = OUT_DIR / "productos_ordenados_por_anio_titulo.bib"
OUT_CSV = OUT_DIR / "productos_ordenados_por_anio_titulo.csv"
OUT_RANK_PNG = OUT_DIR / "ranking_algoritmos_anio_titulo.png"

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

# Patrones robustos: {valor} o "valor"
RE_YEAR   = re.compile(r'(?im)^\s*year\s*=\s*(?:\{([^}]*)\}|"([^"]*)")', re.M)
RE_TITLE  = re.compile(r'(?im)^\s*title\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|"([^"]*)")', re.M)
RE_TYPE   = re.compile(r'(?is)^\s*@\s*([A-Za-z]+)\s*{')  # @article{... → article

def get_field(rx: re.Pattern, entry: str) -> str:
    m = rx.search(entry)
    if not m: return ""
    val = (m.group(1) or m.group(2) or "").strip()
    return val

def get_year(entry: str) -> int:
    raw = get_field(RE_YEAR, entry)
    m = re.search(r'\b(19|20)\d{2}\b', raw)
    return int(m.group(0)) if m else 0  # si falta, al inicio

def get_title(entry: str) -> str:
    t = get_field(RE_TITLE, entry)
    t = re.sub(r'[\{\}]', '', t).strip()
    return t

def get_type(entry: str) -> str:
    m = RE_TYPE.search(entry)
    return (m.group(1).lower() if m else "unknown")

def to_csv_row(entry: str) -> str:
    year = get_year(entry)
    title = get_title(entry).replace('"', '""')
    kind  = get_type(entry)
    return f'"{kind}","{year}","{title}"\n'

def main():
    # Permitir pasar otra ruta .bib por CLI (opcional)
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else IN_BIB
    if not in_path.exists():
        print(f"[ERROR] No existe el archivo de entrada: {in_path}", file=sys.stderr)
        sys.exit(1)

    text = read_text(in_path)
    entries = split_bib_entries(text)
    print(f"[INFO] Entradas totales: {len(entries)}")

    # Construir registros y claves
    records = []
    titles_norm = []
    for e in entries:
        year = get_year(e)
        title = get_title(e)
        tnorm = title.lower()
        records.append({"entry": e, "year": year, "title": title, "title_norm": tnorm})
        titles_norm.append(tnorm)

    # Mapa determinista de títulos → ids según orden lexicográfico
    uniq_titles = sorted(set(titles_norm))
    t2id = {t:i for i,t in enumerate(uniq_titles)}

    # Clave compuesta (tupla) y clave entera para no-comparativos
    for r in records:
        r["key_tuple"] = (r["year"], r["title_norm"])
        r["key_int"]   = r["year"] * 1_000_000 + t2id.get(r["title_norm"], 0)

    # "Oro" (orden correcto) con sort de Python (timsort real)
    gold = sorted(records, key=lambda r: r["key_tuple"])

    # Guardar BIB/CSV según el orden requerido
    OUT_BIB.write_text("".join([r["entry"] for r in gold]), encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        f.write('"type","year","title"\n')
        for r in gold:
            f.write(to_csv_row(r["entry"]))

    print("\nPrimeros 10 (year, title):")
    for r in gold[:10]:
        print(r["year"], "—", r["title"][:100])

    # === Medición de los 12 algoritmos sobre (año,título) ===
    # Comparativos usan key_tuple; no comparativos usan key_int
    algs = [
        ("TimSort",               algo.timsort,               "tuple"),
        ("Comb Sort",             algo.comb_sort,             "tuple"),
        ("Selection Sort",        algo.selection_sort,        "tuple"),
        ("Tree Sort",             algo.tree_sort,             "tuple"),
        ("Pigeonhole Sort",       algo.pigeonhole_sort,       "int"),
        ("Bucket Sort",           lambda arr, key=None: algo.bucket_sort(arr, key=key, buckets=16), "int"),
        ("QuickSort",             algo.quick_sort,            "tuple"),
        ("HeapSort",              algo.heap_sort,             "tuple"),
        ("Bitonic Sort",          algo.bitonic_sort,          "tuple"),
        ("Gnome Sort",            algo.gnome_sort,            "tuple"),
        ("Binary Insertion Sort", algo.binary_insertion_sort, "tuple"),
        ("RadixSort",             algo.radix_sort,            "int"),
    ]

    # Copia de trabajo (no modifiques records ni gold)
    data = records[:]
    results = []  # (name, time, ok)

    for name, func, mode in algs:
        arr = data[:]  # copia para cada algoritmo
        t0 = perf_counter()
        if mode == "tuple":
            out = func(arr, key=lambda r: r["key_tuple"])
        else:  # "int"
            out = func(arr, key=lambda r: r["key_int"])
        dt = perf_counter() - t0
        ok = [x["entry"] for x in out] == [x["entry"] for x in gold]
        results.append((name, dt, ok))
        print(f"{name:22s}  time={dt:.6f}s  ok={ok}")

    # Ranking: más rápido → más lento
    results.sort(key=lambda t: t[1])

    print("\nRanking (más rápido → más lento) para (año, título):")
    for i, (name, dt, ok) in enumerate(results, 1):
        print(f"{i}. {name:22s}  tiempo={dt:.6f}s  ok={ok}")

    # Gráfica opcional del ranking
    names = [r[0] for r in results]
    times = [r[1] for r in results]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, times)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Tiempo (s)")
    plt.title(f"Ranking de algoritmos — Orden (año, título) n={len(data)}")
    for bar, t in zip(bars, times):
        plt.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height(),
                 f"{t:.5f}s",
                 ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT_RANK_PNG, dpi=160)
    print(f"\n[OK] Bib ordenado guardado en: {OUT_BIB}")
    print(f"[OK] CSV ordenado guardado en: {OUT_CSV}")
    print(f"[OK] Ranking en: {OUT_RANK_PNG}")

if __name__ == "__main__":
    main()
