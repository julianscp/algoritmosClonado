# Seguimiento2/grafo_coocurrencia.py
# Construcción de grafo no dirigido de coocurrencia de términos

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import json

# ==================== CONFIGURACIÓN DE RUTAS ====================
BASE_DIR = Path(__file__).resolve().parent
PALABRAS_FILE = BASE_DIR / "../Requerimiento3/ResultadosNuevasPalabras/nuevas_palabras_tfidf.csv"
ABSTRACTS_FILE = BASE_DIR / "../Requerimiento3/DatosProcesados/abstracts_limpios.csv"
OUT_DIR = BASE_DIR / "resultados_coocurrencia"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Archivos de salida
GRAFO_GEXF = OUT_DIR / "grafo_coocurrencia.gexf"
GRADOS_CSV = OUT_DIR / "grados_nodos.csv"
COMPONENTES_CSV = OUT_DIR / "componentes_conexas.csv"
RESUMEN_TXT = OUT_DIR / "resumen_grafo.txt"
GRAFO_JSON = OUT_DIR / "grafo_coocurrencia.json"

print("=" * 60)
print("CONSTRUCCIÓN DE GRAFO DE COOCURRENCIA")
print("=" * 60)

# ==================== 1. CARGAR PALABRAS CLAVE ====================
print("\n[1] Cargando palabras clave...")
if not PALABRAS_FILE.exists():
    raise FileNotFoundError(f"[ERROR] No se encontro el archivo: {PALABRAS_FILE}")

df_palabras = pd.read_csv(PALABRAS_FILE, encoding='utf-8')
palabras_clave = df_palabras['palabra'].str.lower().tolist()

print(f"[OK] Se cargaron {len(palabras_clave)} palabras clave:")
for i, palabra in enumerate(palabras_clave, 1):
    print(f"   {i:2d}. {palabra}")

# ==================== 2. CARGAR ABSTRACTS ====================
print(f"\n[2] Cargando abstracts procesados desde: {ABSTRACTS_FILE}")
if not ABSTRACTS_FILE.exists():
    raise FileNotFoundError(f"[ERROR] No se encontro el archivo: {ABSTRACTS_FILE}")

df_abstracts = pd.read_csv(ABSTRACTS_FILE, encoding='utf-8')
abstracts = df_abstracts['abstract_limpio'].astype(str).fillna("").tolist()

print(f"[OK] Se cargaron {len(abstracts)} abstracts")

# ==================== 3. CONSTRUIR GRAFO DE COOCURRENCIA ====================
print("\n[3] Construyendo grafo de coocurrencia...")

# Crear grafo no dirigido
G = nx.Graph()

# Diccionario para contar coocurrencias (peso de las aristas)
coocurrencias = defaultdict(int)

# Para cada abstract, encontrar qué palabras clave aparecen
for idx, abstract in enumerate(abstracts):
    abstract_lower = abstract.lower()
    
    # Encontrar qué palabras clave aparecen en este abstract
    palabras_presentes = []
    for palabra in palabras_clave:
        if palabra in abstract_lower:
            palabras_presentes.append(palabra)
            # Asegurar que el nodo existe
            G.add_node(palabra)
    
    # Crear aristas entre todas las palabras que aparecen juntas en este abstract
    for i, palabra1 in enumerate(palabras_presentes):
        for palabra2 in palabras_presentes[i+1:]:
            # Incrementar el peso de coocurrencia
            par = tuple(sorted([palabra1, palabra2]))
            coocurrencias[par] += 1

# Añadir aristas al grafo con sus pesos
for (palabra1, palabra2), peso in coocurrencias.items():
    G.add_edge(palabra1, palabra2, weight=peso, count=peso)

print(f"[OK] Grafo construido:")
print(f"   - Nodos: {G.number_of_nodes()}")
print(f"   - Aristas: {G.number_of_edges()}")

# ==================== 4. CALCULAR GRADOS DE NODOS ====================
print("\n[4] Calculando grados de los nodos...")

grados = []
for nodo in G.nodes():
    grado = G.degree(nodo)
    # Sumar pesos de todas las aristas conectadas (fuerza del nodo)
    fuerza = sum(G[nodo][vecino].get('weight', 1) for vecino in G.neighbors(nodo))
    grados.append({
        'palabra': nodo,
        'grado': grado,
        'fuerza': fuerza,  # Suma de pesos de todas las conexiones
        'vecinos': list(G.neighbors(nodo))
    })

# Ordenar por grado descendente
grados = sorted(grados, key=lambda x: x['grado'], reverse=True)

# Guardar grados en CSV
df_grados = pd.DataFrame(grados)
df_grados.to_csv(GRADOS_CSV, index=False, encoding='utf-8-sig')
print(f"[OK] Grados guardados en: {GRADOS_CSV}")

print("\n[TOP 5] Terminos mas relacionados (mayor grado):")
for i, item in enumerate(grados[:5], 1):
    print(f"   {i}. {item['palabra']}: grado={item['grado']}, fuerza={item['fuerza']}")

# ==================== 5. DETECTAR COMPONENTES CONEXAS ====================
print("\n[5] Detectando componentes conexas...")

componentes = list(nx.connected_components(G))
print(f"[OK] Se encontraron {len(componentes)} componentes conexas")

# Preparar datos de componentes
datos_componentes = []
for idx, componente in enumerate(componentes, 1):
    # Crear subgrafo de esta componente
    subgrafo = G.subgraph(componente)
    
    datos_componentes.append({
        'componente': idx,
        'tamaño': len(componente),
        'términos': ', '.join(sorted(componente)),
        'número_aristas': subgrafo.number_of_edges(),
        'densidad': nx.density(subgrafo)
    })

# Ordenar por tamaño descendente
datos_componentes = sorted(datos_componentes, key=lambda x: x['tamaño'], reverse=True)

# Guardar componentes en CSV
df_componentes = pd.DataFrame(datos_componentes)
df_componentes.to_csv(COMPONENTES_CSV, index=False, encoding='utf-8-sig')
print(f"[OK] Componentes conexas guardadas en: {COMPONENTES_CSV}")

print("\n[RESUMEN] Componentes conexas:")
for comp in datos_componentes:
    print(f"   Componente {comp['componente']}: {comp['tamaño']} términos")
    print(f"      {comp['términos']}")
    print()

# ==================== 6. GUARDAR GRAFO ====================
print("\n[6] Guardando grafo...")

# Guardar en formato GEXF (para Gephi u otras herramientas)
nx.write_gexf(G, GRAFO_GEXF)
print(f"[OK] Grafo guardado en formato GEXF: {GRAFO_GEXF}")

# Guardar en formato JSON
grafo_dict = {
    "nodos": {nodo: {"grado": G.degree(nodo)} for nodo in G.nodes()},
    "aristas": {f"{u}-{v}": {"peso": G[u][v].get('weight', 1), "count": G[u][v].get('count', 1)} 
                for u, v in G.edges()}
}
with open(GRAFO_JSON, 'w', encoding='utf-8') as f:
    json.dump(grafo_dict, f, indent=2, ensure_ascii=False)
print(f"[OK] Grafo guardado en formato JSON: {GRAFO_JSON}")

# ==================== 7. GENERAR RESUMEN ====================
with open(RESUMEN_TXT, 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("RESUMEN DEL GRAFO DE COOCURRENCIA\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Total de palabras clave analizadas: {len(palabras_clave)}\n")
    f.write(f"Total de abstracts procesados: {len(abstracts)}\n\n")
    
    f.write(f"ESTADÍSTICAS DEL GRAFO:\n")
    f.write(f"  - Nodos: {G.number_of_nodes()}\n")
    f.write(f"  - Aristas: {G.number_of_edges()}\n")
    f.write(f"  - Densidad: {nx.density(G):.4f}\n")
    f.write(f"  - Componentes conexas: {len(componentes)}\n\n")
    
    f.write("TOP 5 TÉRMINOS MÁS RELACIONADOS:\n")
    for i, item in enumerate(grados[:5], 1):
        f.write(f"  {i}. {item['palabra']}: grado={item['grado']}, fuerza={item['fuerza']}\n")
    
    f.write("\nCOMPONENTES CONEXAS:\n")
    for comp in datos_componentes:
        f.write(f"  Componente {comp['componente']}: {comp['tamaño']} términos\n")
        f.write(f"    Términos: {comp['términos']}\n")
        f.write(f"    Aristas: {comp['número_aristas']}, Densidad: {comp['densidad']:.4f}\n\n")

print(f"[OK] Resumen guardado en: {RESUMEN_TXT}")

# ==================== 8. VISUALIZACIÓN ====================
print("\n[7] Generando visualizacion del grafo...")

plt.figure(figsize=(16, 12))

# Posicionamiento de nodos
pos = nx.spring_layout(G, k=1, iterations=50, seed=42)

# Dibujar aristas (más gruesas si tienen mayor peso)
edges = G.edges()
weights = [G[u][v].get('weight', 1) for u, v in edges]
nx.draw_networkx_edges(G, pos, width=[w * 0.5 for w in weights], 
                       alpha=0.3, edge_color='gray')

# Dibujar nodos (más grandes si tienen mayor grado)
node_sizes = [G.degree(n) * 300 for n in G.nodes()]
node_colors = [G.degree(n) for n in G.nodes()]

nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                       node_color=node_colors, cmap=plt.cm.plasma,
                       alpha=0.8)

# Etiquetas
labels = {n: n for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')

plt.title("Grafo de Coocurrencia de Términos\n(Tamaño del nodo = grado, Grosor de arista = frecuencia de coocurrencia)", 
          fontsize=14, fontweight='bold')
plt.axis('off')
plt.tight_layout()

# Guardar figura
fig_path = OUT_DIR / "grafo_coocurrencia.png"
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
print(f"[OK] Visualizacion guardada en: {fig_path}")

# También mostrar la figura (comentado para evitar problemas en algunos entornos)
# plt.show()

print("\n" + "=" * 60)
print("[OK] PROCESO COMPLETADO EXITOSAMENTE")
print("=" * 60)
print(f"\n[INFO] Todos los resultados se encuentran en: {OUT_DIR}")

