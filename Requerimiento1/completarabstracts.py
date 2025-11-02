# completar_abstracts.py
import re, time, random, requests, traceback
from pathlib import Path

# === CONFIGURACIÓN ===
BASE_DIR = Path(__file__).resolve().parent
IN_DIR = BASE_DIR / "ArchivosDescargados"
OUT_SUFFIX = "_con_abstracts"
HEADERS = {"Accept": "application/json"}

# === FUNCIONES ===
def get_bib_files():
    """Obtiene los .bib de ACM, SAGE y Elsevier"""
    return list(IN_DIR.glob("acm_*.bib")) + \
           list(IN_DIR.glob("sage_*.bib")) + \
           list(IN_DIR.glob("elsevier_*.bib"))

def get_crossref_abstract(doi, retries=3):
    """Busca el abstract en Crossref (genérico, sirve para ACM/SAGE/Elsevier)"""
    url = f"https://api.crossref.org/works/{doi}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 404:
                print(f"  [WARN] DOI no encontrado: {doi}")
                return None
            r.raise_for_status()
            data = r.json()
            abstract = data.get("message", {}).get("abstract")
            if abstract:
                abstract = re.sub(r'<[^>]+>', '', abstract)  # elimina etiquetas HTML
                return abstract.strip()
            return None
        except Exception as e:
            print(f"  [ERROR] {e} ({doi}), intento {attempt+1}")
            time.sleep(2)
    return None

def enrich_bib_content(bib_text):
    """Agrega el campo abstract a cada entrada si es posible"""
    entries = re.split(r'(?=@[a-zA-Z]+{)', bib_text)
    result = []
    for entry in entries:
        if not entry.strip():
            continue

        doi_match = re.search(r'doi\s*=\s*\{([^}]+)\}', entry, flags=re.I)
        if not doi_match:
            result.append(entry)
            continue

        doi = doi_match.group(1).strip()
        print(f" → Consultando DOI: {doi} ...")
        abs_text = get_crossref_abstract(doi)

        if abs_text:
            if re.search(r'abstract\s*=', entry, flags=re.I):
                entry = re.sub(
                    r'abstract\s*=\s*\{[^}]*\}',
                    f"abstract = {{{abs_text}}}",
                    entry,
                    flags=re.I
                )
            else:
                # Insertar abstract antes de la última llave
                entry = entry.rstrip().rstrip("}") + f"\n  abstract = {{{abs_text}}},\n}}\n"
            print("   ✓ Abstract añadido")
        else:
            print("   ✗ No se encontró abstract")

        result.append(entry)
        time.sleep(random.uniform(0.5, 1.0))  # delay para no saturar Crossref

    return "\n\n".join(result)

def process_bib_file(bib_path: Path):
    """Procesa un archivo .bib y genera su versión con abstracts"""
    print(f"\n[ARCHIVO] {bib_path.name}")
    try:
        text = bib_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] No se pudo leer {bib_path.name}: {e}")
        return

    enriched_text = enrich_bib_content(text)

    out_path = bib_path.with_name(bib_path.stem + OUT_SUFFIX + ".bib")
    try:
        out_path.write_text(enriched_text, encoding="utf-8")
        print(f"  [OK] Guardado → {out_path.name}")
    except Exception as e:
        print(f"  [ERROR] No se pudo escribir {out_path.name}: {e}")

def main():
    print("=== COMPLETAR ABSTRACTS (.bib) ===")
    files = get_bib_files()
    if not files:
        print("No se encontraron archivos .bib que comiencen con acm_, sage_ o elsevier_.")
        return

    print(f"Archivos encontrados: {len(files)}\n")
    for f in files:
        process_bib_file(f)

    print("\n[FINALIZADO] Todos los archivos procesados correctamente.")

# === EJECUCIÓN PRINCIPAL ===
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPCIÓN MANUAL] Proceso detenido.")
    except Exception:
        print("\n[ERROR CRÍTICO]")
        traceback.print_exc()
