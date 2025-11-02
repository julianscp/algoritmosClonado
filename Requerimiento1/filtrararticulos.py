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
    if d.startswith("https://doi.org/"): 
        d = d[16:]
    elif d.startswith("http://doi.org/"):  
        d = d[15:]
    return d

# patrones robustos para key = {valor} o "valor"
RE_DOI = re.compile(r'(?im)^\s*doi\s*=\s*(?:\{([^}]*)\}|"([^"]*)")', re.M)
RE_ABSTRACT = re.compile(r'(?im)^\s*abstract\s*=\s*(?:\{([^}]*)\}|"([^"]*)")', re.M)

def get_doi(entry: str) -> str:
    m = RE_DOI.search(entry)
    val = (m.group(1) or m.group(2)) if m else ""
    return normalize_doi(val)

def has_abstract(entry: str) -> bool:
    """Devuelve True si el entry tiene un campo abstract no vacío."""
    m = RE_ABSTRACT.search(entry)
    if not m:
        return False
    val = (m.group(1) or m.group(2) or "").strip()
    return len(val) > 0

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

    # ✅ Solo procesar archivos que:
    # - Empiezan con acm_, sage_ o elsevier_
    # - Terminan con _con_abstracts.bib
    bib_files = sorted([
        f for f in IN_DIR.glob("*.bib")
        if (
            (f.name.startswith("acm_") or
             f.name.startswith("sage_") or
             f.name.startswith("elsevier_"))
            and f.name.endswith("_con_abstracts.bib")
        )
    ])

    if not bib_files:
        print(f"[WARN] No se encontraron archivos válidos (acm_, sage_, elsevier_ con _con_abstracts.bib)", file=sys.stderr)
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
            abstract_ok = has_abstract(e)

            # ---- Filtro 1: sin DOI → descartar ----
            if not doi:
                descartados.append(e)
                continue

            key = f"doi::{doi}"

            # ---- Filtro 2: duplicado por DOI ----
            if key in seen_doi:
                descartados.append(e)
                continue

            # ---- Filtro 3: sin abstract ----
            if not abstract_ok:
                descartados.append(e)
                continue

            # ---- Pasa todos los filtros ----
            seen_doi.add(key)
            optimos.append(e)

    # Guardar resultados
    OPTIMOS.write_text("".join(optimos), encoding="utf-8")
    DESCARTADOS.write_text("".join(descartados), encoding="utf-8")

    print(f"[OK] articulosOptimos.bib: {len(optimos)} entradas (únicas, con DOI y abstract)")
    print(f"[OK] articulosDescartados.bib: {len(descartados)} entradas (duplicados, sin DOI o sin abstract)")
    print(f"[DONE] Archivos en: {OUT_DIR}")

if __name__ == "__main__":
    main()
