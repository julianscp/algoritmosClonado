@echo off
REM Script de instalación de dependencias para Requerimiento 5
REM Este script ayuda a instalar las dependencias necesarias

echo ========================================================================
echo INSTALACION DE DEPENDENCIAS - REQUERIMIENTO 5
echo ========================================================================
echo.

echo Verificando si conda está disponible...
where conda >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Conda encontrado
    echo.
    echo Instalando dependencias con conda...
    conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow -y
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================================================
        echo INSTALACION COMPLETADA EXITOSAMENTE
        echo ========================================================================
        echo.
        echo Puedes ejecutar el script ahora:
        echo python requerimiento5_completo.py
    ) else (
        echo.
        echo ========================================================================
        echo ERROR EN LA INSTALACION
        echo ========================================================================
        echo.
        echo Por favor, instala las dependencias manualmente:
        echo conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow
    )
) else (
    echo [ADVERTENCIA] Conda no encontrado
    echo.
    echo ========================================================================
    echo CONDA NO ESTA INSTALADO
    echo ========================================================================
    echo.
    echo Para instalar las dependencias, necesitas Conda o Miniconda.
    echo.
    echo OPCION 1: Instalar Miniconda (recomendado)
    echo   1. Descarga desde: https://docs.conda.io/en/latest/miniconda.html
    echo   2. Instala Miniconda
    echo   3. Abre "Anaconda Prompt" o "Miniconda Prompt"
    echo   4. Ejecuta: conda install -c conda-forge geopandas bibtexparser matplotlib pycountry wordcloud pandas numpy pillow
    echo.
    echo OPCION 2: Intentar con pip (puede fallar en Windows)
    echo   pip install bibtexparser matplotlib pycountry wordcloud pandas numpy Pillow
    echo   pip install geopandas
    echo.
    echo NOTA: geopandas es dificil de instalar con pip en Windows.
    echo       Se recomienda usar conda.
    echo.
)

pause

