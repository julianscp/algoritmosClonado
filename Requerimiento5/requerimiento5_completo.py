"""
Requerimiento 5: Análisis Visual de Producción Científica

Este script implementa:
1. Mapa de calor con distribución geográfica según primer autor
2. Nube de palabras dinámica (términos frecuentes en abstracts y keywords)
3. Línea temporal de publicaciones por año y por revista
4. Exportación a PDF de las tres visualizaciones
"""

import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from urllib.request import urlretrieve

# Verificar dependencias
try:
    import bibtexparser
except ImportError:
    print("❌ Error: bibtexparser no está instalado. Ejecuta: pip install bibtexparser")
    sys.exit(1)

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_pdf import PdfPages
except ImportError:
    print("❌ Error: matplotlib no está instalado. Ejecuta: pip install matplotlib")
    sys.exit(1)

# Verificar geopandas - REQUERIDO para mapa de calor
GEOPANDAS_AVAILABLE = False
try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    print("=" * 80)
    print("❌ ERROR: geopandas no está instalado.")
    print("=" * 80)
    print("\nEl Requerimiento 5 requiere geopandas para generar el mapa de calor.")
    print("\nOPCIONES DE INSTALACIÓN EN WINDOWS:")
    print("\n1. RECOMENDADO - Usar Conda (más fácil):")
    print("   a) Instalar Miniconda desde: https://docs.conda.io/en/latest/miniconda.html")
    print("   b) Abrir 'Anaconda Prompt' o 'Miniconda Prompt'")
    print("   c) Ejecutar: conda install -c conda-forge geopandas")
    print("\n2. ALTERNATIVA - Usar pip con ruedas precompiladas:")
    print("   a) Descargar ruedas desde: https://www.lfd.uci.edu/~gohlke/pythonlibs/")
    print("   b) Buscar: GDAL, Fiona, Shapely, Pyproj, Geopandas")
    print("   c) Instalar en orden de dependencias")
    print("\n3. ALTERNATIVA - Instalar desde conda-forge en entorno existente:")
    print("   conda install -c conda-forge geopandas")
    print("\n" + "=" * 80)
    sys.exit(1)

try:
    import pycountry
except ImportError:
    print("❌ Error: pycountry no está instalado. Ejecuta: pip install pycountry")
    sys.exit(1)

try:
    from wordcloud import WordCloud
except ImportError:
    print("❌ Error: wordcloud no está instalado. Ejecuta: pip install wordcloud")
    sys.exit(1)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ Error: pandas o numpy no están instalados. Ejecuta: pip install pandas numpy")
    sys.exit(1)

# ==================== CONFIGURACIÓN ====================
BASE_DIR = Path(__file__).resolve().parent.parent
BIB_PATH = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos_limpio.bib"
OUTPUT_DIR = BASE_DIR / "Requerimiento5" / "Resultados"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==================== FUNCIONES AUXILIARES ====================

def limpiar_texto(texto: str) -> str:
    """Limpia texto eliminando etiquetas HTML/MathML y normalizando."""
    if not texto:
        return ""
    # Eliminar etiquetas HTML/MathML
    texto = re.sub(r'<[^>]+>', ' ', texto)
    # Minúsculas y normalizar espacios
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def extraer_primer_autor(autor_str: str) -> str:
    """Extrae el primer autor de una cadena de autores."""
    if not autor_str:
        return ""
    # Separar por "and" y tomar el primero
    autores = [a.strip() for a in autor_str.split(" and ")]
    return autores[0] if autores else ""

def inferir_pais_por_apellido(apellido: str) -> str:
    """Infiere país probable según apellido del autor (heurística mejorada)."""
    if not apellido:
        return None
    
    # Diccionario de apellidos comunes por país
    surname_country_map = {
        # Asia
        "Wang": "China", "Li": "China", "Zhang": "China", "Liu": "China", 
        "Chen": "China", "Yang": "China", "Huang": "China", "Zhao": "China",
        "Wu": "China", "Zhou": "China", "Xu": "China", "Sun": "China",
        "Kim": "South Korea", "Park": "South Korea", "Lee": "South Korea",
        "Singh": "India", "Kumar": "India", "Patel": "India", "Sharma": "India",
        "Yamamoto": "Japan", "Tanaka": "Japan", "Sato": "Japan", "Suzuki": "Japan",
        "Nguyen": "Vietnam", "Tran": "Vietnam", "Le": "Vietnam",
        # Europa
        "Garcia": "Spain", "Martinez": "Spain", "Lopez": "Spain", 
        "Gonzalez": "Spain", "Rodriguez": "Spain", "Fernandez": "Spain",
        "Silva": "Brazil", "Santos": "Brazil", "Oliveira": "Brazil", "Souza": "Brazil",
        "Smith": "United Kingdom", "Jones": "United Kingdom", "Taylor": "United Kingdom",
        "Brown": "United States", "Johnson": "United States", "Williams": "United States",
        "Schmidt": "Germany", "Müller": "Germany", "Mueller": "Germany", "Schneider": "Germany",
        "Rossi": "Italy", "Bianchi": "Italy", "Esposito": "Italy", "Romano": "Italy",
        "Dupont": "France", "Lefevre": "France", "Martin": "France", "Bernard": "France",
        "Andersson": "Sweden", "Johansson": "Sweden", "Nilsson": "Sweden",
        "Nielsen": "Denmark", "Hansen": "Denmark", "Andersen": "Denmark",
        "Olsen": "Norway", "Larsen": "Norway", "Haugen": "Norway",
        "Kowalski": "Poland", "Nowak": "Poland", "Wisniewski": "Poland",
        "Ivanov": "Russia", "Petrov": "Russia", "Sidorov": "Russia",
        # Otros
        "Mohamed": "Egypt", "Hassan": "Egypt", "Ali": "Egypt",
        "Cohen": "Israel", "Levi": "Israel", "Mizrahi": "Israel",
    }
    
    # Extraer apellido (generalmente antes de la coma o último nombre)
    apellido_limpio = apellido.split(",")[0].strip() if "," in apellido else apellido.split()[-1].strip()
    
    for key, country in surname_country_map.items():
        if apellido_limpio.lower() == key.lower():
            return country
    return None

def cargar_articulos_desde_bib(bib_path: Path):
    """Carga artículos desde archivo BibTeX."""
    print(f"📖 Cargando artículos desde {bib_path}...")
    
    if not bib_path.exists():
        raise FileNotFoundError(f"❌ No se encontró el archivo: {bib_path}")
    
    with open(bib_path, 'r', encoding='utf-8') as f:
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = parser.parse_file(f)
    
    articulos = []
    for entry in bib_database.entries:
        # Extraer información
        autor_completo = entry.get('author', '')
        primer_autor = extraer_primer_autor(autor_completo)
        abstract = limpiar_texto(entry.get('abstract', ''))
        keywords = limpiar_texto(entry.get('keywords', ''))
        year = entry.get('year', '')
        journal = entry.get('journal', '')
        title = entry.get('title', '')
        
        articulos.append({
            'titulo': title,
            'primer_autor': primer_autor,
            'autor_completo': autor_completo,
            'abstract': abstract,
            'keywords': keywords,
            'year': year,
            'journal': journal,
            'doi': entry.get('doi', '')
        })
    
    print(f"✅ Se cargaron {len(articulos)} artículos")
    return articulos

# ==================== 1. MAPA DE CALOR ====================

def generar_mapa_calor(articulos, output_dir: Path):
    """Genera mapa de calor con distribución geográfica según primer autor."""
    print("\n🗺️  Generando mapa de calor...")
    
    if not GEOPANDAS_AVAILABLE:
        raise ImportError("geopandas es requerido para generar el mapa de calor. Por favor instálalo siguiendo las instrucciones mostradas.")
    
    # Contar países
    country_counts = Counter()
    no_country = 0
    
    for art in articulos:
        primer_autor = art['primer_autor']
        if primer_autor:
            pais = inferir_pais_por_apellido(primer_autor)
            if pais:
                country_counts[pais] += 1
            else:
                no_country += 1
    
    print(f"   Países detectados: {len(country_counts)}")
    print(f"   Artículos sin país detectado: {no_country}")
    
    # Generar mapa geográfico
    return _generar_mapa_geografico(country_counts, output_dir)

def _generar_mapa_geografico(country_counts, output_dir: Path):
    """Genera mapa geográfico usando geopandas."""
    # Descargar mapa base si no existe
    geojson_path = output_dir / "ne_110m_admin_0_countries.geojson"
    if not geojson_path.exists():
        print("   Descargando mapa base desde Natural Earth...")
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
        try:
            urlretrieve(url, geojson_path)
        except Exception as e:
            print(f"   ⚠️ Error al descargar mapa: {e}")
            print("   Usando mapa existente si está disponible...")
            geojson_path = BASE_DIR / "Requerimiento5" / "Mapa" / "ne_110m_admin_0_countries.geojson"
            if not geojson_path.exists():
                raise FileNotFoundError("No se pudo obtener el archivo GeoJSON del mapa")
    
    # Cargar mapa
    world = gpd.read_file(geojson_path)
    
    # Convertir nombres a códigos ISO alpha3
    country_alpha3_counts = {}
    for name, count in country_counts.items():
        try:
            country_obj = pycountry.countries.lookup(name)
            country_alpha3_counts[country_obj.alpha_3] = count
        except LookupError:
            print(f"   ⚠️ No se pudo convertir {name} a código alpha3")
    
    # Generar mapa
    world["count"] = world["ADM0_A3"].map(country_alpha3_counts).fillna(0)
    
    fig, ax = plt.subplots(figsize=(16, 10))
    world.plot(column="count", cmap="YlOrRd", linewidth=0.8, ax=ax, 
               edgecolor="0.5", legend=True, legend_kwds={'label': 'Número de artículos'})
    ax.set_title("Distribución Geográfica de Artículos según Primer Autor\n(Heurística por apellido)", 
                 fontsize=16, fontweight='bold', pad=20)
    ax.axis("off")
    
    # Guardar
    mapa_path = output_dir / "mapa_calor_distribucion.png"
    plt.savefig(mapa_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"   ✅ Mapa geográfico guardado en: {mapa_path}")
    return mapa_path


# ==================== 2. NUBE DE PALABRAS ====================

def generar_nube_palabras(articulos, output_dir: Path):
    """Genera nube de palabras dinámica de abstracts y keywords."""
    print("\n☁️  Generando nube de palabras...")
    
    # Combinar abstracts y keywords
    textos = []
    for art in articulos:
        texto = f"{art['abstract']} {art['keywords']}".strip()
        if texto:
            textos.append(texto)
    
    texto_completo = " ".join(textos)
    
    if not texto_completo:
        print("   ⚠️ No hay texto disponible para generar la nube")
        return None
    
    # Limpiar y preparar texto
    texto_limpio = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', ' ', texto_completo)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).lower().strip()
    
    # Generar nube de palabras
    try:
        # Configurar stopwords comunes en inglés
        stopwords_set = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'it', 'its', 'they', 'them', 'their', 'we', 'our', 'you', 'your', 'he',
            'she', 'his', 'her', 'its', 'my', 'me', 'i', 'am', 'im', 'ive', 'id'
        }
        
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            max_words=200,
            colormap='viridis',
            relative_scaling=0.5,
            min_font_size=10,
            stopwords=stopwords_set,
            collocations=False
        ).generate(texto_limpio)
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(16, 8))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        ax.set_title("Nube de Palabras - Términos Frecuentes en Abstracts y Keywords", 
                     fontsize=16, fontweight='bold', pad=20)
        
        # Guardar
        nube_path = output_dir / "nube_palabras.png"
        plt.savefig(nube_path, dpi=300, bbox_inches="tight")
        plt.close()
        
        print(f"   ✅ Nube de palabras guardada en: {nube_path}")
        return nube_path
    except Exception as e:
        print(f"   ⚠️ Error al generar nube de palabras: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==================== 3. LÍNEA TEMPORAL ====================

def generar_linea_temporal(articulos, output_dir: Path):
    """Genera línea temporal de publicaciones por año y por revista."""
    print("\n📅 Generando línea temporal...")
    
    # Agrupar por año
    por_anio = Counter()
    por_revista_anio = defaultdict(lambda: Counter())
    
    for art in articulos:
        year_str = art['year']
        if year_str and year_str.isdigit():
            year = int(year_str)
            por_anio[year] += 1
            journal = art['journal'] or "Sin revista"
            por_revista_anio[journal][year] += 1
    
    if not por_anio:
        print("   ⚠️ No hay datos de años disponibles")
        return None
    
    # Crear figura con dos subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Subplot 1: Publicaciones por año
    anos = sorted(por_anio.keys())
    conteos = [por_anio[a] for a in anos]
    
    ax1.plot(anos, conteos, marker='o', linewidth=2, markersize=8, color='#2E86AB')
    ax1.fill_between(anos, conteos, alpha=0.3, color='#2E86AB')
    ax1.set_xlabel("Año", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Número de Publicaciones", fontsize=12, fontweight='bold')
    ax1.set_title("Línea Temporal de Publicaciones por Año", fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(anos)
    ax1.tick_params(axis='x', rotation=45)
    
    # Subplot 2: Top revistas por año
    # Seleccionar top 10 revistas por número total de publicaciones
    revista_totales = {}
    for journal, anos_dict in por_revista_anio.items():
        revista_totales[journal] = sum(anos_dict.values())
    
    top_revistas = sorted(revista_totales.items(), key=lambda x: x[1], reverse=True)[:10]
    top_revistas_nombres = [r[0] for r in top_revistas]
    
    # Preparar datos para el gráfico de barras apiladas
    anos_unicos = sorted(set([a for journal in top_revistas_nombres 
                               for a in por_revista_anio[journal].keys()]))
    
    # Crear matriz de datos
    datos_revistas = []
    for journal in top_revistas_nombres:
        fila = [por_revista_anio[journal].get(a, 0) for a in anos_unicos]
        datos_revistas.append(fila)
    
    # Gráfico de barras apiladas
    x_pos = np.arange(len(anos_unicos))
    bottom = np.zeros(len(anos_unicos))
    colors = plt.cm.tab20(np.linspace(0, 1, len(top_revistas_nombres)))
    
    for i, (journal, datos) in enumerate(zip(top_revistas_nombres, datos_revistas)):
        ax2.bar(x_pos, datos, bottom=bottom, label=journal[:50], color=colors[i], alpha=0.8)
        bottom += datos
    
    ax2.set_xlabel("Año", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Número de Publicaciones", fontsize=12, fontweight='bold')
    ax2.set_title("Distribución de Publicaciones por Revista (Top 10) y Año", 
                  fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(anos_unicos, rotation=45)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Guardar
    temporal_path = output_dir / "linea_temporal.png"
    plt.savefig(temporal_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"   ✅ Línea temporal guardada en: {temporal_path}")
    return temporal_path

# ==================== 4. EXPORTAR A PDF ====================

def exportar_a_pdf(mapa_path, nube_path, temporal_path, output_dir: Path):
    """Exporta las tres visualizaciones a un único archivo PDF."""
    print("\n📄 Exportando visualizaciones a PDF...")
    
    pdf_path = output_dir / "requerimiento5_visualizaciones.pdf"
    
    try:
        with PdfPages(pdf_path) as pdf:
            # Página 1: Mapa de calor
            if mapa_path and mapa_path.exists():
                try:
                    from PIL import Image
                    img = Image.open(mapa_path)
                    fig, ax = plt.subplots(figsize=(16, 10))
                    ax.imshow(img)
                    ax.axis('off')
                    ax.set_title("1. Mapa de Calor - Distribución Geográfica", 
                                fontsize=18, fontweight='bold', pad=20, y=0.95)
                    pdf.savefig(fig, bbox_inches='tight', dpi=300)
                    plt.close()
                    print("   ✓ Mapa agregado al PDF")
                except Exception as e:
                    print(f"   ⚠️ Error al agregar mapa al PDF: {e}")
            
            # Página 2: Nube de palabras
            if nube_path and nube_path.exists():
                try:
                    from PIL import Image
                    img = Image.open(nube_path)
                    fig, ax = plt.subplots(figsize=(16, 8))
                    ax.imshow(img)
                    ax.axis('off')
                    ax.set_title("2. Nube de Palabras - Términos Frecuentes", 
                                fontsize=18, fontweight='bold', pad=20, y=0.95)
                    pdf.savefig(fig, bbox_inches='tight', dpi=300)
                    plt.close()
                    print("   ✓ Nube de palabras agregada al PDF")
                except Exception as e:
                    print(f"   ⚠️ Error al agregar nube de palabras al PDF: {e}")
            
            # Página 3: Línea temporal
            if temporal_path and temporal_path.exists():
                try:
                    from PIL import Image
                    img = Image.open(temporal_path)
                    fig, ax = plt.subplots(figsize=(16, 12))
                    ax.imshow(img)
                    ax.axis('off')
                    ax.set_title("3. Línea Temporal - Publicaciones por Año y Revista", 
                                fontsize=18, fontweight='bold', pad=20, y=0.95)
                    pdf.savefig(fig, bbox_inches='tight', dpi=300)
                    plt.close()
                    print("   ✓ Línea temporal agregada al PDF")
                except Exception as e:
                    print(f"   ⚠️ Error al agregar línea temporal al PDF: {e}")
            
            # Metadatos
            d = pdf.infodict()
            d['Title'] = 'Requerimiento 5 - Análisis Visual de Producción Científica'
            d['Author'] = 'Sistema de Análisis Bibliométrico'
            d['Subject'] = 'Visualizaciones: Mapa de Calor, Nube de Palabras, Línea Temporal'
            d['Keywords'] = 'Bibliometría, Visualización, Análisis Científico'
            d['CreationDate'] = datetime.now()
        
        print(f"   ✅ PDF exportado en: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"   ⚠️ Error al crear PDF: {e}")
        print("   💡 Asegúrate de tener Pillow instalado: pip install Pillow")
        return None

# ==================== FUNCIÓN PRINCIPAL ====================

def main():
    """Función principal."""
    print("=" * 80)
    print("REQUERIMIENTO 5 - ANÁLISIS VISUAL DE PRODUCCIÓN CIENTÍFICA")
    print("=" * 80)
    
    try:
        # 1. Cargar artículos
        articulos = cargar_articulos_desde_bib(BIB_PATH)
        
        # 2. Generar mapa de calor
        mapa_path = generar_mapa_calor(articulos, OUTPUT_DIR)
        
        # 3. Generar nube de palabras
        nube_path = generar_nube_palabras(articulos, OUTPUT_DIR)
        
        # 4. Generar línea temporal
        temporal_path = generar_linea_temporal(articulos, OUTPUT_DIR)
        
        # 5. Exportar a PDF
        pdf_path = exportar_a_pdf(mapa_path, nube_path, temporal_path, OUTPUT_DIR)
        
        print("\n" + "=" * 80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📁 Todos los resultados se encuentran en: {OUTPUT_DIR}")
        print(f"   - Mapa de calor: {mapa_path.name}")
        print(f"   - Nube de palabras: {nube_path.name if nube_path else 'N/A'}")
        print(f"   - Línea temporal: {temporal_path.name if temporal_path else 'N/A'}")
        print(f"   - PDF completo: {pdf_path.name}")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

