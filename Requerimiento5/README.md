# Requerimiento 5 - Análisis Visual de Producción Científica

Este módulo implementa el análisis visual de la producción científica según los requisitos especificados.

## Funcionalidades

1. **Mapa de Calor**: Distribución geográfica de artículos según el primer autor
2. **Nube de Palabras**: Términos más frecuentes en abstracts y keywords (dinámica)
3. **Línea Temporal**: Publicaciones por año y por revista
4. **Exportación a PDF**: Los tres visualizaciones exportadas a un único PDF

## Requisitos

### Dependencias Python (Mínimas)

```bash
pip install bibtexparser matplotlib pycountry wordcloud pandas numpy Pillow
```

### Dependencias Requeridas

**geopandas** (REQUERIDO para el mapa de calor):
- **En Windows**: Se recomienda usar conda (más fácil):
  ```bash
  # Opción 1: Con conda (recomendado)
  conda install -c conda-forge geopandas
  
  # Opción 2: Si no tienes conda, instala Miniconda primero
  # Descarga desde: https://docs.conda.io/en/latest/miniconda.html
  # Luego: conda install -c conda-forge geopandas
  ```
- **Alternativa con pip**: Puede ser complicado en Windows. Se recomienda usar conda.

### Archivo de Entrada

El script utiliza el archivo:
- `Requerimiento1/ArchivosFiltrados/articulosOptimos_limpio.bib`

Este archivo debe contener los artículos científicos en formato BibTeX.

## Instalación de Dependencias

### Opción 1: Script Automático (Recomendado)

**Windows:**
```bash
# Ejecuta el script .bat (doble clic o desde la terminal)
instalar_dependencias.bat
```

**Linux/Mac:**
```bash
# Hacer el script ejecutable (solo la primera vez)
chmod +x instalar_dependencias.sh

# Ejecutar el script
./instalar_dependencias.sh
```

### Opción 2: Instalación Manual

**Con Conda (Recomendado para Windows):**
```bash
conda install -c conda-forge geopandas
pip install bibtexparser matplotlib pycountry wordcloud pandas numpy Pillow
```

**Con pip (puede fallar en Windows):**
```bash
pip install bibtexparser matplotlib pycountry wordcloud pandas numpy Pillow geopandas
```

## Ejecución

```bash
cd Requerimiento5
python requerimiento5_completo.py
```

## Salidas

Todos los resultados se guardan en `Requerimiento5/Resultados/`:

- `mapa_calor_distribucion.png` - Mapa de calor geográfico
- `nube_palabras.png` - Nube de palabras
- `linea_temporal.png` - Gráficos de línea temporal
- `requerimiento5_visualizaciones.pdf` - PDF con las tres visualizaciones

## Notas

- **Mapa de calor**: 
  - Se genera un mapa geográfico mundial con distribución por países
  - Utiliza una heurística basada en apellidos para inferir el país del primer autor
  - **REQUIERE geopandas** - el script no funcionará sin esta dependencia
- **Nube de palabras**: Se genera dinámicamente a partir de abstracts y keywords
- **Línea temporal**: Muestra tanto publicaciones por año como distribución por revista
- **PDF**: Se genera automáticamente con todas las visualizaciones

## Solución de Problemas

### Error al instalar geopandas en Windows

**El mapa de calor REQUIERE geopandas.** Si encuentras errores al instalar con pip:

1. **Instala Miniconda** (recomendado):
   - Descarga desde: https://docs.conda.io/en/latest/miniconda.html
   - Instala y reinicia tu terminal

2. **Abre "Anaconda Prompt" o "Miniconda Prompt"** (no PowerShell normal)

3. **Instala geopandas**:
   ```bash
   conda install -c conda-forge geopandas
   ```

4. **Ejecuta el script desde el mismo prompt de conda**:
   ```bash
   cd C:\Users\julia\Downloads\algoritmos\proyectoalgoritmos\Requerimiento5
   python requerimiento5_completo.py
   ```

**NOTA**: Si ya tienes Python instalado sin conda, puedes crear un entorno conda solo para este proyecto:
```bash
conda create -n requerimiento5 python=3.10
conda activate requerimiento5
conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow
```

## Estructura del Código

- `requerimiento5_completo.py` - Script principal con todas las funcionalidades
- `instalar_dependencias.bat` - Script de instalación automática para Windows
- `instalar_dependencias.sh` - Script de instalación automática para Linux/Mac
- `Mapa/generate_map.py` - Script original para generación de mapas (puede usarse como alternativa)

