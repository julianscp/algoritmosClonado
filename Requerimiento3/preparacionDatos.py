# Proyecto/Requerimiento3/PrepararDatos.py

import re
import pandas as pd
from pathlib import Path
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Descargar recursos necesarios de NLTK (solo la primera vez)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)  # ← Agrega esta
nltk.download('stopwords', quiet=True)

# --- CONFIGURACIONES ---
BASE_DIR = Path(__file__).resolve().parent
IN_FILE = BASE_DIR / "../Requerimiento1/ArchivosFiltrados/articulosOptimos.bib"
OUT_DIR = BASE_DIR / "DatosProcesados"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "abstracts_limpios.csv"
print(">>> Script iniciado correctamente")
print("Ruta esperada del archivo:", IN_FILE)
print("Existe archivo:", IN_FILE.exists())

# --- FUNCIONES AUXILIARES ---

def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: elimina etiquetas, minúsculas, quita signos, números y stopwords."""
    if not texto:
        return ""
    
    # --- ELIMINAR ETIQUETAS HTML / MathML ---
    texto = re.sub(r'<[^>]+>', ' ', texto)  # elimina cualquier cosa entre < y >
    
    # Minúsculas
    texto = texto.lower()

    # Quitar caracteres especiales, números y saltos de línea
    texto = re.sub(r'[^a-záéíóúüñ\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Tokenización
    tokens = word_tokenize(texto, language='english')

    # Stopwords en inglés y español
    stop_words = set(stopwords.words('english')).union(set(stopwords.words('spanish')))

    # Filtrar stopwords
    tokens_filtrados = [t for t in tokens if t not in stop_words and len(t) > 2]

    # Unir de nuevo en texto limpio
    texto_limpio = ' '.join(tokens_filtrados)

    return texto_limpio


def extraer_abstracts(bib_path: Path):
    """Extrae los abstracts de un archivo .bib."""
    abstracts = []
    current_entry = {}
    inside_entry = False

    with open(bib_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()

            # Detectar inicio y fin de un registro BibTeX
            if line.startswith('@'):
                inside_entry = True
                current_entry = {}
                continue
            if inside_entry and line == '}':
                if 'abstract' in current_entry:
                    abstracts.append(current_entry['abstract'])
                inside_entry = False
                continue

            # Extraer campo abstract (maneja varias líneas)
            if inside_entry:
                match = re.match(r'abstract\s*=\s*[{"](.+)[}"],?', line, re.IGNORECASE)
                if match:
                    current_entry['abstract'] = match.group(1)
                else:
                    # Manejar abstracts multilínea
                    if 'abstract' in current_entry:
                        current_entry['abstract'] += ' ' + line

    return abstracts


def main():
    print("📘 Cargando y procesando abstracts...")

    abstracts = extraer_abstracts(IN_FILE)
    print(f"✅ {len(abstracts)} abstracts extraídos del archivo.")

    datos_limpios = [limpiar_texto(abs_) for abs_ in abstracts]

    df = pd.DataFrame({
        'abstract_original': abstracts,
        'abstract_limpio': datos_limpios
    })

    df.to_csv(OUT_FILE, index=False, encoding='utf-8-sig')
    print(f"💾 Archivo procesado guardado en: {OUT_FILE}")
    print("✅ Limpieza completa y datos listos para análisis.")


if __name__ == "__main__":
    main()
