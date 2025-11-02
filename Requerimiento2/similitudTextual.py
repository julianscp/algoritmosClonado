import re
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein
from sentence_transformers import SentenceTransformer
import bibtexparser
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------------------------------------
# 1️⃣ Lectura de abstracts desde el archivo BibTeX unificado
# -----------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
BIB_PATH = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos.bib"

with open(BIB_PATH, encoding="utf-8") as bibfile:
    bib_database = bibtexparser.load(bibfile)

# Extraemos títulos y abstracts
data = []
for entry in bib_database.entries:
    title = entry.get("title", "Sin título").replace("\n", " ").strip()
    abstract = entry.get("abstract", "").replace("\n", " ").strip()
    if abstract:
        data.append({"titulo": title, "abstract": abstract})

df = pd.DataFrame(data)
if df.empty:
    print("⚠️ No se encontraron abstracts en el archivo BibTeX.")
    exit()

print(f"\nSe cargaron {len(df)} artículos con abstracts.\n")

# -----------------------------------------------------------
# 2️⃣ Funciones de similitud clásicas
# -----------------------------------------------------------

def jaccard_similarity(a: str, b: str) -> float:
    """
    Jaccard(A,B) = |A ∩ B| / |A ∪ B|
    Mide el solapamiento de conjuntos de palabras.
    """
    A = set(re.findall(r'\w+', a.lower()))
    B = set(re.findall(r'\w+', b.lower()))
    return len(A & B) / len(A | B) if (A | B) else 0.0


def cosine_tfidf_similarity(a: str, b: str) -> float:
    """
    Similaridad del coseno entre vectores TF-IDF.
    cos(θ) = (A·B) / (||A|| * ||B||)
    """
    vectorizer = TfidfVectorizer().fit([a, b])
    tfidf = vectorizer.transform([a, b])
    return float(cosine_similarity(tfidf[0], tfidf[1]))


def levenshtein_similarity(a: str, b: str) -> float:
    """
    Distancia de edición normalizada:
    sim = 1 - (dist_lev / max_len)
    """
    dist = Levenshtein.distance(a, b)
    return 1 - dist / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0


def ngram_overlap_similarity(a: str, b: str, n=3) -> float:
    """
    Coincidencia de n-gramas:
    sim = |Ngram(A) ∩ Ngram(B)| / |Ngram(A) ∪ Ngram(B)|
    """
    def ngrams(text, n):
        text = re.sub(r'\s+', ' ', text.lower())
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    A, B = ngrams(a, n), ngrams(b, n)
    return len(A & B) / len(A | B) if (A | B) else 0.0

# -----------------------------------------------------------
# 3️⃣ Modelos IA
# -----------------------------------------------------------

print("Cargando modelos de IA (esto puede tardar unos segundos)...")
model_sbert = SentenceTransformer('all-MiniLM-L6-v2')
model_distilbert = SentenceTransformer('distilbert-base-nli-stsb-mean-tokens')

def embedding_similarity(model, a: str, b: str) -> float:
    """
    Similaridad del coseno entre embeddings semánticos generados por un modelo de lenguaje.
    """
    embeddings = model.encode([a, b])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

# -----------------------------------------------------------
# 4️⃣ Selección de artículos y comparación múltiple
# -----------------------------------------------------------

print("Lista de artículos disponibles:\n")
for i, row in df.iterrows():
    print(f"[{i}] {row['titulo'][:100]}{'...' if len(row['titulo'])>100 else ''}")

indices_input = input(
    "\nIngrese los índices de los artículos a comparar (separados por coma, ej: 0,2,5): "
)
try:
    indices = [int(x.strip()) for x in indices_input.split(",") if x.strip().isdigit()]
except ValueError:
    print("❌ Entrada inválida.")
    exit()

if len(indices) < 2:
    print("⚠️ Debe seleccionar al menos dos artículos.")
    exit()

for i in indices:
    if i not in df.index:
        print(f"❌ Índice fuera de rango: {i}")
        exit()

# -----------------------------------------------------------
# 5️⃣ Cálculo de matriz de similitud para cada algoritmo
# -----------------------------------------------------------

print("\nCalculando similitudes... Esto puede tardar un poco.\n")

# Preparamos los abstracts seleccionados
abstracts = [df.loc[i, "abstract"] for i in indices]
titulos = [df.loc[i, "titulo"][:50] + ("..." if len(df.loc[i, 'titulo']) > 50 else "") for i in indices]

# Diccionario para almacenar resultados por algoritmo
matrices = {}

# 1. Jaccard
jac = np.zeros((len(abstracts), len(abstracts)))
for i in range(len(abstracts)):
    for j in range(len(abstracts)):
        jac[i, j] = jaccard_similarity(abstracts[i], abstracts[j])
matrices["Jaccard"] = jac

# 2. Coseno TF-IDF
tfidf = TfidfVectorizer().fit_transform(abstracts)
matrices["Coseno (TF-IDF)"] = cosine_similarity(tfidf)

# 3. Levenshtein
lev = np.zeros((len(abstracts), len(abstracts)))
for i in range(len(abstracts)):
    for j in range(len(abstracts)):
        lev[i, j] = levenshtein_similarity(abstracts[i], abstracts[j])
matrices["Levenshtein"] = lev

# 4. N-Gramas
ng = np.zeros((len(abstracts), len(abstracts)))
for i in range(len(abstracts)):
    for j in range(len(abstracts)):
        ng[i, j] = ngram_overlap_similarity(abstracts[i], abstracts[j])
matrices["N-gramas"] = ng

# 5. Sentence-BERT
emb1 = model_sbert.encode(abstracts)
matrices["Sentence-BERT"] = cosine_similarity(emb1)

# 6. DistilBERT
emb2 = model_distilbert.encode(abstracts)
matrices["DistilBERT STS"] = cosine_similarity(emb2)

# -----------------------------------------------------------
# 6️⃣ Mostrar resultados
# -----------------------------------------------------------

for nombre, matriz in matrices.items():
    print("\n==============================================")
    print(f"   MATRIZ DE SIMILITUD - {nombre}")
    print("==============================================")
    dfmat = pd.DataFrame(matriz, index=titulos, columns=titulos)
    print(dfmat.round(3))
    print()

def exportar_resultados_pdf(resultados_dict, archivo_salida="Resultados_Similitud.pdf"):
    """
    resultados_dict: diccionario con nombre del método como clave
                     y DataFrame pandas con columnas ['Articulo_1', 'Articulo_2', 'Similitud']
    """
    doc = SimpleDocTemplate(archivo_salida, pagesize=letter)
    elementos = []
    estilos = getSampleStyleSheet()
    estilo_titulo = estilos['Heading1']
    estilo_texto = estilos['BodyText']

    for metodo, df in resultados_dict.items():
        elementos.append(Paragraph(f"Resultados - {metodo}", estilo_titulo))
        elementos.append(Spacer(1, 12))

        # Tomar los primeros 20 resultados más altos
        df_sorted = df.sort_values(by='Similitud', ascending=False).head(20)
        datos = [df_sorted.columns.to_list()] + df_sorted.values.tolist()

        # Crear tabla
        tabla = Table(datos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elementos.append(tabla)
        elementos.append(Spacer(1, 24))

    doc.build(elementos)
    print(f"\n✅ Resultados exportados correctamente a {archivo_salida}\n")

# Opcional: guardar resultados en CSV
guardar = input("¿Desea guardar los resultados en CSV? (s/n): ").lower()
if guardar == "s":
    out_dir = BASE_DIR / "Requerimiento2" / "ResultadosSimilitud"
    out_dir.mkdir(exist_ok=True, parents=True)
    for nombre, matriz in matrices.items():
        dfmat = pd.DataFrame(matriz, index=titulos, columns=titulos)
        dfmat.to_csv(out_dir / f"{nombre.replace(' ', '_')}.csv", encoding="utf-8")
    print(f"\n✅ Resultados guardados en: {out_dir}\n")
else:
    print("\nAnálisis finalizado.\n")

    
# -----------------------------------------------------------
# 7️⃣ Generar PDF con todas las tablas de similitud
# -----------------------------------------------------------

# Convertir las matrices en DataFrames planos (pares de artículos)
resultados_dict = {}

for nombre, matriz in matrices.items():
    dfmat = pd.DataFrame(matriz, index=titulos, columns=titulos)
    filas = []
    for i in range(len(titulos)):
        for j in range(i + 1, len(titulos)):  # evitar duplicados (i<j)
            filas.append({
                "Articulo_1": titulos[i],
                "Articulo_2": titulos[j],
                "Similitud": round(float(matriz[i, j]), 4)
            })
    resultados_dict[nombre] = pd.DataFrame(filas)

# Exportar todo en un solo PDF
exportar_resultados_pdf(resultados_dict)

# -----------------------------------------------------------
# 8️⃣ (Opcional) Guardar también CSV individuales
# -----------------------------------------------------------

guardar = input("¿Desea guardar los resultados en CSV además del PDF? (s/n): ").lower()
if guardar == "s":
    out_dir = BASE_DIR / "Requerimiento2" / "ResultadosSimilitud"
    out_dir.mkdir(exist_ok=True, parents=True)
    for nombre, dfres in resultados_dict.items():
        dfres.to_csv(out_dir / f"{nombre.replace(' ', '_')}.csv", index=False, encoding="utf-8")
    print(f"\n✅ Resultados guardados en: {out_dir}\n")
else:
    print("\n✅ Análisis finalizado. PDF generado correctamente.\n")
