# descargaarchivos.py
import argparse, datetime as dt, time, textwrap, sys, re, csv, requests, random, traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "ArchivosDescargados"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = "302399c7683708da34f3049c80edb69a"
ELSEVIER_HEADERS = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json"
}

def now_tag():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def pick_year(issued):
    try:
        return issued["date-parts"][0][0]
    except Exception:
        return None

def normalize_text(x):
    return (x or "").strip()

def escape_bib(s):
    return s.replace("{", "\\{").replace("}", "\\}")

def to_bibkey(title, year, first_author):
    base = re.sub(r'[^A-Za-z0-9]+', '', (first_author or "ref").split()[-1] + (str(year) if year else "") + title[:20])
    return (base or f"key{int(time.time())}")[:40]

def make_bib_entry(it):
    doi = it.get("DOI") or ""
    title = normalize_text((it.get("title") or [""])[0])
    authors = it.get("author") or []
    year = pick_year(it.get("issued"))
    journal = normalize_text((it.get("container-title") or [""])[0])
    publisher = normalize_text(it.get("publisher"))
    volume = normalize_text(it.get("volume"))
    issue = normalize_text(it.get("issue") or it.get("journal-issue", {}).get("issue"))
    pages = normalize_text(it.get("page"))
    url = f"https://doi.org/{doi}" if doi else normalize_text(it.get("URL"))
    abstract = it.get("abstract", "")

    # autores BibTeX
    bib_authors = []
    for a in authors:
        g = (a.get("given") or "").strip()
        f = (a.get("family") or "").strip()
        nm = (f + (", " + g if g else "")).strip() if f or g else (a.get("name") or "").strip()
        if nm:
            bib_authors.append(nm)
    auth_bib = " and ".join(bib_authors) if bib_authors else ""

    key = to_bibkey(title, year, (authors[0].get("family") if authors and authors[0].get("family") else "ref"))

    fields = [
        ("title", escape_bib(title)),
        ("author", escape_bib(auth_bib)),
        ("journal", escape_bib(journal)),
        ("year", str(year) if year else ""),
        ("publisher", escape_bib(publisher)),
        ("volume", volume),
        ("number", issue),
        ("pages", pages),
        ("doi", doi),
        ("url", url),
        ("abstract", escape_bib(abstract))
    ]
    bib = f"@article{{{key},\n"
    for k, v in fields:
        if v:
            bib += f"  {k} = {{{v}}},\n"
    bib += "}\n\n"
    return bib

def write_bib(path, items):
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(make_bib_entry(it))
    print(f"[AUTO-SAVE] Progreso guardado: {len(items)} registros → {path.name}")

def call_crossref(query, rows, member_id, mailto=None, year_min=None, year_max=None, title_only=False):
    filt = [f"member:{member_id}", "type:journal-article"]
    if year_min: filt.append(f"from-pub-date:{year_min}-01-01")
    if year_max: filt.append(f"until-pub-date:{year_max}-12-31")
    params = {
        ("query.title" if title_only else "query"): query,
        "rows": rows,
        "filter": ",".join(filt),
        "select": "DOI,title,author,issued,container-title,publisher,type,URL,volume,issue,page",
        "sort": "published",
        "order": "desc",
    }
    headers = {"User-Agent": f"PAA/1.0 (mailto:{mailto})" if mailto else "PAA/1.0"}
    r = requests.get("https://api.crossref.org/works", params=params, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json().get("message", {}).get("items", [])

def get_elsevier_abstract(doi, retries=3):
    if not doi:
        return None
    url = f"https://api.elsevier.com/content/article/doi/{doi}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=ELSEVIER_HEADERS, timeout=30)
            if r.status_code == 401:
                print(f"[WARN] 401 Unauthorized para {doi}")
                return None
            if r.status_code == 404:
                print(f"[WARN] No encontrado: {doi}")
                return None
            if r.status_code != 200:
                print(f"[WARN] Error {r.status_code} en {doi}, intento {attempt+1}")
                time.sleep(2)
                continue
            data = r.json()
            abs_text = (
                data.get("full-text-retrieval-response", {})
                    .get("coredata", {})
                    .get("dc:description")
            )
            return abs_text.strip() if abs_text else None
        except Exception as e:
            print(f"[ERROR] Fallo en abstract {doi}: {e}")
            time.sleep(2)
    return None

def main():
    ap = argparse.ArgumentParser("Descarga artículos de Elsevier (ScienceDirect) con abstracts y genera BibTeX")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--mailto", default=None)
    ap.add_argument("--year-min", type=int, default=None)
    ap.add_argument("--year-max", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    tag = now_tag()
    base = OUT_DIR / f"elsevier_{tag}.bib"
    all_items = []

    print(f"[ELSEVIER] Buscando artículos sobre '{args.query}'...\n")

    try:
        items = call_crossref(
            query=args.query,
            rows=args.limit,
            member_id=78,
            mailto=args.mailto,
            year_min=args.year_min,
            year_max=args.year_max
        )
    except Exception as e:
        print(f"[ERROR] Llamada a Crossref falló: {e}")
        return

    print(f"[INFO] {len(items)} artículos obtenidos de Crossref.\n")

    for i, it in enumerate(items, start=1):
        doi = it.get("DOI")
        it["_source"] = "scidir"
        abs_text = get_elsevier_abstract(doi)
        it["abstract"] = abs_text or "N/D"

        print(f"[{i}/{len(items)}] {'✓' if abs_text else '✗'} {doi or 'sin DOI'}")

        all_items.append(it)

        # Guardado automático cada 20 artículos o en fallos
        if i % 20 == 0:
            write_bib(base, all_items)

        # Delay con pequeña variabilidad
        time.sleep(args.sleep + random.uniform(0.1, 0.6))

    # Guardado final
    write_bib(base, all_items)
    print(f"\n[FINALIZADO] {len(all_items)} artículos guardados en {base.name}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPCIÓN] Guardando progreso parcial...")
        sys.exit(0)
    except Exception:
        print("\n[ERROR CRÍTICO] El proceso terminó inesperadamente.")
        traceback.print_exc()
