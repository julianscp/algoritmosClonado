# Proyecto/Requerimiento1/FiltrarArchivos.py
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IN_DIR = BASE_DIR / "ArchivosDescargados"
OUT_DIR = BASE_DIR / "ArchivosFiltrados"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OPTIMOS = OUT_DIR / "articulosOptimos.bib"
DESCARTADOS = OUT_DIR / "articulosDescartados.bib"

# ------------------------- Utilidades -------------------------

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")

def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    d = doi.strip().lower()
    if d.startswith("https://doi.org/"): d = d[16:]
    if d.startswith("http://doi.org/"):  d = d[15:]
    return d

# patrones robustos para key = {valor} o "valor"
RE_DOI = re.compile(r'(?im)^\s*doi\s*=\s*(?:\{([^}]*)\}|"([^"]*)")', re.M)

def get_doi(entry: str) -> str:
    m = RE_DOI.search(entry)
    val = (m.group(1) or m.group(2)) if m else ""
    return normalize_doi(val)

def split_bib_entries(text: str) -> list[str]:
    """
    Divide un archivo .bib en entradas individuales respetando el balanceo de llaves.
    Considera cualquier bloque que empiece por '@' y cierra con la llave de nivel 0.
    """
    entries = []
    i = 0
    n = len(text)
    while i < n:
        at = text.find('@', i)
        if at == -1:
            break
        lb = text.find('{', at)
        if lb == -1:
            break
        depth = 1
        j = lb + 1
        while j < n and depth > 0:
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
            j += 1
        entry = text[at:j]
        if entry:
            if not entry.endswith("\n\n"):
                entry = entry.rstrip() + "\n\n"
            entries.append(entry)
        i = j
    return entries

# ------------------------- Lógica principal -------------------------

def main():
    if not IN_DIR.exists():
        print(f"[ERROR] No existe carpeta de entrada: {IN_DIR}", file=sys.stderr)
        sys.exit(1)

    bib_files = sorted(IN_DIR.glob("*.bib"))
    if not bib_files:
        print(f"[WARN] No se encontraron .bib en {IN_DIR}", file=sys.stderr)
        OPTIMOS.write_text("", encoding="utf-8")
        DESCARTADOS.write_text("", encoding="utf-8")
        return

    seen_doi = set()
    optimos = []
    descartados = []

    for bf in bib_files:
        text = read_text(bf)
        entries = split_bib_entries(text)
        print(f"[INFO] {bf.name}: {len(entries)} entradas")

        for e in entries:
            doi = get_doi(e)

            # Solo DOI: si no hay DOI, descartar
            if not doi:
                descartados.append(e)
                continue

            key = f"doi::{doi}"
            if key in seen_doi:
                descartados.append(e)
            else:
                seen_doi.add(key)
                optimos.append(e)

    OPTIMOS.write_text("".join(optimos), encoding="utf-8")
    DESCARTADOS.write_text("".join(descartados), encoding="utf-8")

    print(f"[OK] articulosOptimos.bib: {len(optimos)} entradas (únicas por DOI)")
    print(f"[OK] articulosDescartados.bib: {len(descartados)} entradas (duplicados y sin DOI)")
    print(f"[DONE] Archivos en: {OUT_DIR}")

if __name__ == "__main__":
    main()
