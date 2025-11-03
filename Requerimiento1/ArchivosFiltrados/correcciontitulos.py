import re
from pathlib import Path

# --- CONFIGURACIONES ---
BASE_DIR = Path(__file__).resolve().parent
IN_FILE = BASE_DIR / "articulosOptimos.bib"
OUT_FILE = BASE_DIR / "articulosOptimos_limpio.bib"

def limpiar_etiquetas_html(texto: str) -> str:
    """Elimina cualquier etiqueta HTML o MathML (por ejemplo <mml:math ...>)."""
    # Elimina cualquier cosa entre < >
    texto = re.sub(r'<[^>]+>', '', texto)
    # Quita espacios duplicados
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def limpiar_titulos_bibtex(ruta_entrada: Path, ruta_salida: Path):
    """Lee un archivo .bib y limpia etiquetas en los títulos."""
    with open(ruta_entrada, 'r', encoding='utf-8', errors='ignore') as f:
        lineas = f.readlines()

    nuevas_lineas = []
    dentro_titulo = False
    titulo_acumulado = ""

    for linea in lineas:
        if re.match(r'\s*title\s*=\s*[{"]', linea, re.IGNORECASE):
            # Inicia captura de título
            dentro_titulo = True
            titulo_acumulado = linea
        elif dentro_titulo:
            titulo_acumulado += linea
            # Detectar fin del campo title
            if re.search(r'[}"],?\s*$', linea):
                dentro_titulo = False
                # Extraer contenido entre { } o " "
                match = re.search(r'title\s*=\s*[{"](.*)[}"],?', titulo_acumulado, re.IGNORECASE | re.DOTALL)
                if match:
                    titulo_original = match.group(1)
                    titulo_limpio = limpiar_etiquetas_html(titulo_original)
                    # Reconstruir línea limpia
                    linea_limpia = re.sub(re.escape(titulo_original), titulo_limpio, titulo_acumulado)
                    nuevas_lineas.append(linea_limpia)
                else:
                    nuevas_lineas.append(titulo_acumulado)
                titulo_acumulado = ""
            # Si aún no terminó, seguimos acumulando
            continue
        else:
            nuevas_lineas.append(linea)

    # Guardar nuevo archivo limpio
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.writelines(nuevas_lineas)

    print(f"✅ Limpieza completada. Archivo guardado en:\n   {ruta_salida}")

if __name__ == "__main__":
    print(f"📘 Limpiando títulos del archivo:\n   {IN_FILE}")
    limpiar_titulos_bibtex(IN_FILE, OUT_FILE)
