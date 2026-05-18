"""
Extracción de texto de PDF de ficha técnica.
Usa pdfplumber para extraer el contenido textual del PDF en inglés del
fabricante, conservando el orden y la estructura tabular básica.
"""
import pdfplumber
import io


def extraer_texto_pdf(file_input):
    """Extrae el texto completo del PDF.

    Args:
        file_input: puede ser una ruta (str), un objeto file-like (e.g.
                    UploadedFile de Streamlit) o bytes.

    Returns:
        str: texto extraído de todas las páginas, con saltos entre páginas.
    """
    # pdfplumber acepta path o file-like
    if isinstance(file_input, bytes):
        file_input = io.BytesIO(file_input)

    partes = []
    with pdfplumber.open(file_input) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text() or ""
            if texto.strip():
                partes.append(f"--- PÁGINA {i + 1} ---\n{texto.strip()}")

    return "\n\n".join(partes)


def estadisticas_texto(texto):
    """Devuelve estadísticas básicas del texto para mostrar en la UI."""
    return {
        "caracteres": len(texto),
        "palabras": len(texto.split()),
        "lineas": len(texto.splitlines()),
        "paginas": texto.count("--- PÁGINA"),
    }
