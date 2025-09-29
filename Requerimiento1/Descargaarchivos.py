# descargaarchivos.py
import argparse, datetime as dt, time, textwrap, sys, re, csv
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "ArchivosDescargados"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_MAP = {
    "acm":    {"member": 320, "filename": "acm"},
    "sage":   {"member": 179, "filename": "sage"},
    "scidir": {"member": 78,  "filename": "scidir"},  # Elsevier = ScienceDirect
}

def now_tag(): 
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def pick_year(issued):
    try: return issued["date-parts"][0][0]
    except Exception: return None

def fmt_authors(lst):
    if not lst: return "N/D"
    names=[]
    for a in lst:
        g=(a.get("given") or "").strip(); f=(a.get("family") or "").strip()
        nm=(g+" "+f).strip() or (a.get("name") or "").strip()
        if nm: names.append(nm)
    return "N/D" if not names else (", ".join(names[:6]) + (" et al." if len(names)>6 else ""))

def normalize_text(x):
    return (x or "").strip()

def to_bibkey(title, year, first_author):
    base = re.sub(r'[^A-Za-z0-9]+', '', (first_author or "ref").split()[-1] + (str(year) if year else "") + title[:20])
    return (base or f"key{int(time.time())}")[:40]

def escape_bib(s):
    return s.replace("{","\\{").replace("}","\\}")

def make_bib_entry(it):
    doi = it.get("DOI") or ""
    title   = normalize_text((it.get("title") or [""])[0])
    authors = it.get("author") or []
    year    = pick_year(it.get("issued"))
    journal = normalize_text((it.get("container-title") or [""])[0])
    publisher = normalize_text(it.get("publisher"))
    volume = normalize_text(it.get("volume"))
    issue  = normalize_text(it.get("issue") or it.get("journal-issue",{}).get("issue"))
    pages  = normalize_text(it.get("page"))
    url    = f"https://doi.org/{doi}" if doi else normalize_text(it.get("URL"))

    # autores BibTeX
    bib_authors=[]
    for a in authors:
        g=(a.get("given") or "").strip(); f=(a.get("family") or "").strip()
        nm = (f + (", " + g if g else "")).strip() if f or g else (a.get("name") or "").strip()
        if nm: bib_authors.append(nm)
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
    ]
    # construir bib
    bib = f"@article{{{key},\n"
    for k,v in fields:
        if v:
            bib += f"  {k} = {{{v}}},\n"
    bib += "}\n\n"
    return bib

def record_block(it):
    doi = it.get("DOI") or ""
    url = f"https://doi.org/{doi}" if doi else (it.get("URL") or "")
    title   = (it.get("title") or ["N/D"])[0]
    authors = fmt_authors(it.get("author"))
    year    = pick_year(it.get("issued")) or "N/D"
    journal = (it.get("container-title") or ["N/D"])[0]
    publisher = it.get("publisher") or "N/D"
    return textwrap.dedent(f"""\
        TÍTULO: {title}
        AUTORES: {authors}
        AÑO: {year}
        REVISTA: {journal}
        EDITOR: {publisher}
        DOI: {doi if doi else 'N/D'}
        URL: {url if url else 'N/D'}
        ———————————————————————————————————————————————
    """)

def write_txt(path, items):
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(record_block(it))

def write_bib(path, items):
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(make_bib_entry(it))

def write_csv(path, items):
    cols = ["title","authors","year","journal","publisher","doi","url","source"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for it in items:
            doi = it.get("DOI") or ""
            url = f"https://doi.org/{doi}" if doi else (it.get("URL") or "")
            title   = (it.get("title") or [""])[0]
            authors = fmt_authors(it.get("author"))
            year    = pick_year(it.get("issued")) or ""
            journal = (it.get("container-title") or [""])[0]
            publisher = it.get("publisher") or ""
            src = it.get("_source","")
            w.writerow([title, authors, year, journal, publisher, doi, url, src])

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
    r = requests.get("https://api.crossref.org/works", params=params, headers=headers, timeout=40)
    r.raise_for_status()
    return r.json().get("message", {}).get("items", [])

def main():
    ap = argparse.ArgumentParser("Crossref → ACM/SAGE/ScienceDirect: export TXT/BIB/CSV, filtros y dedupe")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=25, help="Resultados por fuente")
    ap.add_argument("--sources", nargs="+", default=["acm","sage","scidir"], choices=list(SOURCE_MAP.keys()))
    ap.add_argument("--mailto", default=None)
    ap.add_argument("--year-min", type=int, default=None)
    ap.add_argument("--year-max", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--formats", nargs="+", default=["txt"], choices=["txt","bib","csv"])
    ap.add_argument("--title-only", action="store_true", help="Buscar solo en el título (query.title)")
    ap.add_argument("--must-contain", default=None, help="Regex: conservar si coincide en TÍTULO o REVISTA")
    ap.add_argument("--dedupe", action="store_true", help="Genera también archivos COMBINADOS sin duplicados por DOI")
    args = ap.parse_args()

    tag = now_tag()
    all_items = []
    must_rx = re.compile(args.must_contain, flags=re.I) if args.must_contain else None

    for src in args.sources:
        meta = SOURCE_MAP[src]
        print(f"[{src.upper()}] Buscando… (query='{args.query}', limit={args.limit})")
        try:
            items = call_crossref(
                query=args.query, rows=args.limit, member_id=meta["member"],
                mailto=args.mailto, year_min=args.year_min, year_max=args.year_max,
                title_only=args.title_only
            )
        except requests.HTTPError as e:
            print(f"[{src.upper()}] ERROR Crossref: {e}", file=sys.stderr)
            items = []

        # marca fuente y filtra por must-contain
        kept=[]
        for it in items:
            it["_source"]=src
            if must_rx:
                title   = (it.get("title") or [""])[0]
                journal = (it.get("container-title") or [""])[0]
                hay = " ".join([title, journal])
                if not must_rx.search(hay):
                    continue
            kept.append(it)

        # escribir por fuente
        base = OUT_DIR / f"{meta['filename']}_{tag}"
        if "txt" in args.formats: write_txt(base.with_suffix(".txt"), kept)
        if "bib" in args.formats: write_bib(base.with_suffix(".bib"), kept)
        if "csv" in args.formats: write_csv(base.with_suffix(".csv"), kept)

        print(f"[{src.upper()}] Guardados {len(kept)} artículos en {base}.[txt|bib|csv] según formatos")
        all_items.extend(kept)
        time.sleep(args.sleep)

    if args.dedupe:
        seen=set(); merged=[]
        for it in all_items:
            doi=(it.get("DOI") or "").lower().strip()
            if doi and doi in seen: 
                continue
            if doi: seen.add(doi)
            merged.append(it)
        comb_base = OUT_DIR / f"combined_{tag}"
        if "txt" in args.formats: write_txt(comb_base.with_suffix(".txt"), merged)
        if "bib" in args.formats: write_bib(comb_base.with_suffix(".bib"), merged)
        if "csv" in args.formats: write_csv(comb_base.with_suffix(".csv"), merged)
        print(f"[COMBINED] {len(merged)} artículos únicos por DOI en {comb_base}.[txt|bib|csv]")

if __name__ == "__main__":
    main()
