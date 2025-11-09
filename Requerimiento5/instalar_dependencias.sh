#!/bin/bash
# Script de instalación de dependencias para Requerimiento 5
# Este script ayuda a instalar las dependencias necesarias

echo "========================================================================"
echo "INSTALACION DE DEPENDENCIAS - REQUERIMIENTO 5"
echo "========================================================================"
echo ""

# Verificar si conda está disponible
if command -v conda &> /dev/null; then
    echo "[OK] Conda encontrado"
    echo ""
    echo "Instalando dependencias con conda..."
    conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow -y
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================================================"
        echo "INSTALACION COMPLETADA EXITOSAMENTE"
        echo "========================================================================"
        echo ""
        echo "Puedes ejecutar el script ahora:"
        echo "python requerimiento5_completo.py"
    else
        echo ""
        echo "========================================================================"
        echo "ERROR EN LA INSTALACION"
        echo "========================================================================"
        echo ""
        echo "Por favor, instala las dependencias manualmente:"
        echo "conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow"
    fi
else
    echo "[ADVERTENCIA] Conda no encontrado"
    echo ""
    echo "========================================================================"
    echo "CONDA NO ESTA INSTALADO"
    echo "========================================================================"
    echo ""
    echo "Intentando instalar con pip..."
    echo ""
    
    pip install bibtexparser matplotlib pycountry wordcloud pandas numpy Pillow
    
    echo ""
    echo "Intentando instalar geopandas (puede requerir dependencias del sistema)..."
    pip install geopandas
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================================================"
        echo "INSTALACION COMPLETADA"
        echo "========================================================================"
    else
        echo ""
        echo "========================================================================"
        echo "ERROR AL INSTALAR geopandas"
        echo "========================================================================"
        echo ""
        echo "Si geopandas falló, instala las dependencias del sistema primero:"
        echo "  - En Ubuntu/Debian: sudo apt-get install gdal-bin libgdal-dev"
        echo "  - En macOS: brew install gdal"
        echo "  - En Windows: Usa conda (recomendado)"
        echo ""
        echo "Luego intenta: pip install geopandas"
    fi
fi

