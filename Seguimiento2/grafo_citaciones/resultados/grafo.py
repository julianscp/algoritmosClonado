import json
import networkx as nx

# Cargar JSON
with open("grafo_citaciones.json", "r", encoding="utf-8") as f:
    data = json.load(f)

G = nx.Graph()

# Añadir aristas y nodos conectados
for nodo, vecinos in data["aristas"].items():
    for vecino, peso in vecinos.items():
        G.add_edge(nodo, vecino, weight=peso)

# Añadir información de los nodos (ej. título del artículo)
for nodo in G.nodes():
    titulo = data["nodos"].get(nodo, {}).get("titulo", nodo)
    G.nodes[nodo]["label"] = titulo

# Guardar grafo en formato GEXF
nx.write_gexf(G, "grafoAUTKEY.gexf")
print("Archivo GEXF generado: grafoAUTKEY.gexf")
