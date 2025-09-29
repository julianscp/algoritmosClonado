import sys, re
from pathlib import Path
from time import perf_counter

# importar algoritmos
sys.path.append(str(Path(__file__).resolve().parents[1] / "Algoritmos"))
import algoritmos as algo

import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parents[1]
BIB_PATH = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos.bib"
OUT_DIR = Path(__file__).resolve().parent / "graficas"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "ranking_algoritmos_longitud_titulo.png"

# Tamaño de muestra para la medición
SAMPLE_N = 500

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

RE_TITLE = re.compile(r'(?im)^\s*title\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|"([^"]*)")', re.M)

def get_title(entry: str) -> str:
    m = RE_TITLE.search(entry)
    if not m: 
        return ""
    val = (m.group(1) or m.group(2) or "").strip()
    # quitar llaves residuales
    val = re.sub(r'[\{\}]', '', val)
    return val

def main():
    # Cargar títulos y convertir a longitudes
    txt = read_text(BIB_PATH)
    entries = split_bib_entries(txt)
    titles = [get_title(e) for e in entries]
    lens = [len(t) for t in titles if t]  # enteros >= 1

    data = lens[:min(SAMPLE_N, len(lens))]
    gold = sorted(data)

    # Misma lista de algoritmos
    algs_in_order = [
        ("TimSort",               algo.timsort),
        ("Comb Sort",             algo.comb_sort),
        ("Selection Sort",        algo.selection_sort),
        ("Tree Sort",             algo.tree_sort),
        ("Pigeonhole Sort",       algo.pigeonhole_sort),
        ("Bucket Sort",           lambda arr, key=None: algo.bucket_sort(arr, key=lambda x:x, buckets=16)),
        ("QuickSort",             algo.quick_sort),
        ("HeapSort",              algo.heap_sort),
        ("Bitonic Sort",          algo.bitonic_sort),
        ("Gnome Sort",            algo.gnome_sort),
        ("Binary Insertion Sort", algo.binary_insertion_sort),
        ("RadixSort",             algo.radix_sort),
    ]

    # Única salida ordenada (primeros 50)
    print("\nPrimeros 50 (longitud de título) ordenados (asc):")
    print(gold[:1000])

    # Ranking por tiempo (rápido → lento)
    results = []
    for name, func in algs_in_order:
        arr = data[:]
        t0 = perf_counter()
        try:
            out = func(arr)   # son enteros → sirven todos (incl. Radix/Pigeonhole/Bucket)
        except TypeError:
            out = func(arr, key=lambda x: x)
        dt = perf_counter() - t0
        ok = (out == gold)
        results.append((name, dt, ok))

    results.sort(key=lambda t: t[1])

    print("\nRanking (más rápido → más lento):")
    for i, (name, dt, ok) in enumerate(results, 1):
        print(f"{i}. {name:22s}  tiempo={dt:.6f}s  ok={ok}")

    # Gráfica de barras con etiquetas de valor
    names = [r[0] for r in results]
    times = [r[1] for r in results]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, times)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Tiempo (s)")
    plt.title(f"Ranking de algoritmos — longitud del título (n={len(data)})")

    for bar, t in zip(bars, times):
        plt.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height(),
                 f"{t:.5f}s",
                 ha='center', va='bottom', fontsize=8, rotation=0)

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=160)
    print(f"\nGráfica guardada en: {OUT_PNG}")

if __name__ == "__main__":
    main()
