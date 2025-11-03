import os
import sys
import time
from pathlib import Path
from grafo_citaciones import GrafoCitaciones

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BIB_PATH = BASE_DIR / "Requerimiento1" / "ArchivosFiltrados" / "articulosOptimos_limpio.bib"
RESULTADOS_DIR = Path(__file__).resolve().parent / "resultados"
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Función principal para ejecutar el análisis del grafo de citaciones."""
    print("=" * 80)
    print("CONSTRUCCIÓN Y ANÁLISIS DE GRAFO DE CITACIONES")
    print("=" * 80)
    
    # Crear instancia del grafo
    grafo = GrafoCitaciones()
    
    # Verificar existencia del archivo BibTeX
    if not BIB_PATH.exists():
        print(f"ERROR: No se encontró el archivo BibTeX en {BIB_PATH}")
        print("Buscando archivos .bib en el directorio del proyecto...")
        
        # Buscar archivos .bib alternativos
        bib_files = list(BASE_DIR.glob("**/*.bib"))
        if bib_files:
            print(f"Se encontraron {len(bib_files)} archivos .bib:")
            for i, bib_file in enumerate(bib_files):
                print(f"  {i+1}. {bib_file}")
            
            # Usar el primer archivo encontrado
            bib_path = bib_files[0]
            print(f"Usando: {bib_path}")
        else:
            print("No se encontraron archivos .bib en el proyecto.")
            return
    else:
        bib_path = BIB_PATH
    
    # Cargar artículos desde BibTeX
    print(f"\n1. Cargando artículos desde {bib_path}...")
    inicio = time.time()
    num_articulos = grafo.cargar_articulos_desde_bibtex(bib_path)
    fin = time.time()
    print(f"   Se cargaron {num_articulos} artículos en {fin-inicio:.2f} segundos")
    
    # Inferir relaciones por similitud
    print("\n2. Inferiendo relaciones de citación por similitud...")
    inicio = time.time()
    umbral = 0.25  # Umbral de similitud reducido para encontrar más relaciones
    max_comparaciones = 200000  # Aumentado el número de comparaciones
    num_relaciones = grafo.inferir_relaciones_por_similitud(
        umbral=umbral, 
        max_comparaciones=max_comparaciones,
        usar_filtro_previo=True
    )
    fin = time.time()
    print(f"   Se infirieron {num_relaciones} relaciones en {fin-inicio:.2f} segundos")
    
    # Calcular estadísticas del grafo
    print("\n3. Calculando estadísticas del grafo...")
    estadisticas = grafo.estadisticas_grafo()
    print(f"   Número de nodos: {estadisticas['num_nodos']}")
    print(f"   Número de aristas: {estadisticas['num_aristas']}")
    print(f"   Densidad del grafo: {estadisticas['densidad']:.4f}")
    print(f"   Número de componentes fuertemente conexas: {estadisticas['num_componentes']}")
    print(f"   Tamaño de la componente más grande: {estadisticas['tamaño_componente_mayor']}")
    
    # Mostrar artículos más citados
    print("\n4. Artículos más citados:")
    for i, (nodo, grado) in enumerate(estadisticas['nodos_mas_citados'][:5]):
        titulo = grafo.nodos[nodo].get('titulo', 'Sin título')
        autores = ', '.join(grafo.nodos[nodo].get('autores', []))
        print(f"   {i+1}. {titulo} ({autores}) - {grado} citaciones")
    
    # Guardar el grafo para análisis posterior
    grafo_path = RESULTADOS_DIR / "grafo_citaciones.json"
    print(f"\n5. Guardando grafo en {grafo_path}...")
    grafo.guardar_grafo(grafo_path)
    
    # Ejemplo de cálculo de camino mínimo
    if estadisticas['num_nodos'] >= 2:
        print("\n6. Ejemplo de cálculo de camino mínimo:")
        # Tomar dos nodos aleatorios
        nodos = list(grafo.nodos.keys())
        origen, destino = nodos[0], nodos[-1]
        
        print(f"   Calculando camino mínimo entre:")
        print(f"   - Origen: {grafo.nodos[origen].get('titulo', 'Sin título')}")
        print(f"   - Destino: {grafo.nodos[destino].get('titulo', 'Sin título')}")
        
        distancia, camino = grafo.calcular_camino_minimo_dijkstra(origen, destino)
        
        if distancia == float('infinity'):
            print("   No existe un camino entre estos artículos")
        else:
            print(f"   Distancia: {distancia:.4f}")
            print(f"   Longitud del camino: {len(camino)} nodos")
            print("   Camino:")
            for i, nodo in enumerate(camino):
                print(f"     {i+1}. {grafo.nodos[nodo].get('titulo', 'Sin título')}")
    
    print("\nAnálisis completado con éxito.")

if __name__ == "__main__":
    main()