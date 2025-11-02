import json
import networkx as nx
import matplotlib.pyplot as plt

# Cargar datos
with open("grafo_citaciones.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Crear grafo dirigido
G = nx.DiGraph()

# Suponemos que "nodos" tiene la información de los artículos
for nodo, info in data["nodos"].items():
    G.add_node(nodo, titulo=info.get("titulo", "Sin título"))

# Añadir aristas
for nodo, adyacentes in data["aristas"].items():
    for vecino in adyacentes.keys():
        G.add_edge(nodo, vecino)

# Dibujar grafo
plt.figure(figsize=(16, 16))
pos = nx.spring_layout(G, seed=42)

nx.draw_networkx_nodes(G, pos, node_size=50, node_color="skyblue")
nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=10, edge_color="gray")

# Dibujar etiquetas con títulos (puede recortar si son muy largos)
labels = {n: G.nodes[n]['titulo'][:30] + "..." if len(G.nodes[n]['titulo']) > 30 else G.nodes[n]['titulo'] for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=8)

plt.axis("off")
plt.tight_layout()
plt.show()
