"""
Generador de ficha técnica MGO - Renderer
Refactor del script v8 aprobado. El diseño NO se ha tocado: las únicas
diferencias respecto a generar_ficha_v8.py son:
  1) `DATOS` deja de ser una constante global y pasa como parámetro
  2) Las rutas de fuentes son relativas al directorio del módulo
  3) Las funciones de página reciben `datos` como argumento
Toda la lógica visual (colores, márgenes, fuentes, secciones, bandas,
overlays, pildora WhatsApp, etc.) es idéntica al v8.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import os

# ============================================================
# FUENTES OFICIALES (Manual de marca MGO)
# Títulos: Futura | Cuerpo: Open Sans
# ============================================================
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(_BASE_DIR, "assets", "fonts")


def _reg(name, path):
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            return True
        except Exception as e:
            print(f"Error registrando {name}: {e}")
    return False


_reg("FuturaBold", f"{FONTS}/FuturaBoldReal.ttf")
_reg("FuturaBook", f"{FONTS}/FuturaBookReal.ttf")
_reg("FuturaMedium", f"{FONTS}/FuturaMediumReal.ttf")
_reg("FuturaLight", f"{FONTS}/FuturaLightReal.ttf")
_reg("OpenSans-Regular", f"{FONTS}/OpenSans-Regular.ttf")
_reg("OpenSans-Bold", f"{FONTS}/OpenSans-Bold.ttf")
_reg("OpenSans-SemiBold", f"{FONTS}/OpenSans-SemiBold.ttf")
_reg("OpenSans-Light", f"{FONTS}/OpenSans-Light.ttf")

F_TITLE = "FuturaBold"
F_TITLE_BOOK = "FuturaBook"
F_BODY = "OpenSans-Regular"
F_BOLD = "OpenSans-Bold"
F_MED = "OpenSans-SemiBold"
F_LIGHT = "OpenSans-Light"

# ============================================================
# COLORES OFICIALES (del Manual de Marca)
# ============================================================
COL_AZUL_MARINO = HexColor("#15214B")
COL_AZUL_OSCURO = HexColor("#092238")
COL_CIAN = HexColor("#13C5DF")
COL_CIAN_BRILL = HexColor("#00F0FF")
COL_AZUL_MEDIO = HexColor("#0C5687")
COL_BLANCO = white
COL_NEGRO = HexColor("#1A1A1A")
COL_GRIS = HexColor("#5F5E5A")
COL_GRIS_CLARO = HexColor("#E8EBF0")
COL_FONDO_SUAVE = HexColor("#F8FAFC")
COL_VERDE_WHATSAPP = HexColor("#25D366")
COL_SUBTITULO = COL_AZUL_MEDIO
COL_SPECS_BG = HexColor("#D8DDE5")


# ============================================================
# DATOS POR DEFECTO (mismos que la v8 - sirven como referencia
# para los keys esperados; en producción se sobreescriben)
# ============================================================
DEFAULT_DATOS = {
    "marca": "Volkswagen",
    "modelo": "ID.3",
    "anio": "2025",
    "version": "Smart Excellent Edition",
    "datos_clave": [
        ("ELÉCTRICO", "MOTOR"),
        ("451 KM", "AUTONOMÍA"),
        ("AUTOMÁTICA", "TRANSMISIÓN"),
        ("170 HP", "POTENCIA"),
    ],
    "tren_motriz": [],
    "bateria_carga": [],
    "exterior": [],
    "interior": [],
    "seguridad": [],
    "asistencias_adas": [],
    "tecnologia_conectividad": [],
    "dimensiones_capacidades": [],
    "precio": "30,000",
    "moneda": "USD",
    "whatsapp": "73017677",
    "ciudad": "La Paz, Bolivia",
}


# ============================================================
# UTILIDADES
# ============================================================
def _img_cover(c, img_path, x, y, w, h):
    """Dibuja imagen ocupando el rect completo (cover, recorta si sobra)."""
    img = Image.open(img_path).convert("RGB")
    ir = img.width / img.height
    br = w / h
    if ir > br:
        cw = int(img.height * br)
        l = (img.width - cw) // 2
        cropped = img.crop((l, 0, l + cw, img.height))
    else:
        ch = int(img.width / br)
        t = (img.height - ch) // 2
        cropped = img.crop((0, t, img.width, t + ch))
    temp = f"/tmp/_cv_{abs(hash(img_path))}.jpg"
    cropped.save(temp, "JPEG", quality=92)
    c.drawImage(ImageReader(temp), x, y, width=w, height=h, mask='auto')


def _img_smart(c, img_path, x, y, w, h):
    """Siempre usa cover (recorta para llenar) - sin márgenes blancos."""
    _img_cover(c, img_path, x, y, w, h)


def _render_items_2cols(c, items, text_x, text_w, y_top, y_bottom,
                        truncados_log=None, seccion_nombre=""):
    """Renderiza la lista de items en 2 columnas con línea separadora vertical.
    Si se pasa `truncados_log`, registra los items que fueron truncados.
    """
    n_items = len(items)
    if n_items == 0:
        return
    n_col1 = (n_items + 1) // 2
    col_items_1 = items[:n_col1]
    col_items_2 = items[n_col1:]

    sep_gap = 4 * mm
    col_w = (text_w - sep_gap) / 2

    available_h = y_top - y_bottom
    max_items_col = max(len(col_items_1), len(col_items_2)) if col_items_2 else len(col_items_1)
    line_h = max(4.0 * mm, min(5.5 * mm, available_h / max_items_col))
    font_size = max(8.0, min(9.5, line_h / mm * 1.55))

    sep_x = text_x + col_w + sep_gap / 2
    c.setStrokeColor(HexColor("#B8C0CC"))
    c.setLineWidth(0.5)
    c.line(sep_x, y_bottom + 1 * mm, sep_x, y_top + 1 * mm)

    for col_idx, col_items in enumerate([col_items_1, col_items_2]):
        col_x = text_x + col_idx * (col_w + sep_gap)
        item_y = y_top
        for item in col_items:
            if item_y < y_bottom:
                if truncados_log is not None:
                    truncados_log.append({
                        "seccion": seccion_nombre,
                        "item": item,
                        "tipo": "no_dibujado"
                    })
                break
            c.setFillColor(COL_CIAN)
            c.circle(col_x + 1 * mm, item_y + 0.6 * mm, 0.6 * mm,
                     fill=1, stroke=0)
            c.setFillColor(COL_NEGRO)
            c.setFont(F_BODY, font_size)
            txt = item
            max_w = col_w - 4 * mm
            while c.stringWidth(txt, F_BODY, font_size) > max_w and len(txt) > 5:
                txt = txt[:-1]
            if txt != item:
                txt = txt.rstrip() + "..."
                if truncados_log is not None:
                    truncados_log.append({
                        "seccion": seccion_nombre,
                        "item_original": item,
                        "item_truncado": txt,
                        "tipo": "truncado"
                    })
            c.drawString(col_x + 3 * mm, item_y, txt)
            item_y -= line_h


def _rrect(c, x, y, w, h, r=4 * mm):
    c.roundRect(x, y, w, h, r, fill=1, stroke=0)


# ============================================================
# LOGO MARCA DEL VEHÍCULO (placeholder o imagen real)
# ============================================================
def dibujar_logo_marca(c, cx, cy, size, logo_path=None, color_main=COL_AZUL_MARINO,
                      marca_iniciales="VW"):
    if logo_path and os.path.exists(logo_path):
        radius = size / 2
        c.setFillColor(COL_BLANCO)
        c.circle(cx, cy, radius, fill=1, stroke=0)
        img_size = size * 0.85
        c.drawImage(ImageReader(logo_path),
                    cx - img_size / 2, cy - img_size / 2,
                    width=img_size, height=img_size,
                    preserveAspectRatio=True, mask='auto')
    else:
        radius = size / 2
        c.setFillColor(COL_BLANCO)
        c.circle(cx, cy, radius, fill=1, stroke=0)
        c.setStrokeColor(color_main)
        c.setLineWidth(size * 0.06)
        c.circle(cx, cy, radius, fill=0, stroke=1)
        c.setFillColor(color_main)
        text_size = size * 0.55
        c.setFont(F_TITLE, text_size)
        c.drawCentredString(cx, cy - text_size * 0.32, marca_iniciales)


# ============================================================
# BANDAS DECORATIVAS
# ============================================================
def bandas_decorativas(c, W, H, posiciones=("sup_der", "inf_izq", "inf_der")):
    if "sup_der" in posiciones:
        c.setFillColor(COL_AZUL_MARINO)
        p = c.beginPath()
        p.moveTo(W, H); p.lineTo(W - 80*mm, H)
        p.curveTo(W - 60*mm, H - 6*mm, W - 35*mm, H - 14*mm,
                  W - 10*mm, H - 9*mm)
        p.lineTo(W, H - 7*mm); p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(COL_CIAN)
        p = c.beginPath()
        p.moveTo(W, H - 7*mm); p.lineTo(W - 10*mm, H - 9*mm)
        p.curveTo(W - 35*mm, H - 14*mm, W - 60*mm, H - 6*mm,
                  W - 80*mm, H)
        p.lineTo(W - 90*mm, H)
        p.curveTo(W - 70*mm, H - 9*mm, W - 35*mm, H - 19*mm,
                  W - 10*mm, H - 14*mm)
        p.lineTo(W, H - 12*mm); p.close()
        c.drawPath(p, fill=1, stroke=0)

    if "inf_izq" in posiciones:
        c.setFillColor(COL_CIAN)
        p = c.beginPath()
        p.moveTo(0, 0); p.lineTo(80*mm, 0)
        p.curveTo(60*mm, 6*mm, 35*mm, 14*mm, 10*mm, 9*mm)
        p.lineTo(0, 7*mm); p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(COL_AZUL_MARINO)
        p = c.beginPath()
        p.moveTo(0, 7*mm); p.lineTo(10*mm, 9*mm)
        p.curveTo(35*mm, 14*mm, 60*mm, 6*mm, 80*mm, 0)
        p.lineTo(95*mm, 0)
        p.curveTo(70*mm, 11*mm, 40*mm, 19*mm, 10*mm, 15*mm)
        p.lineTo(0, 13*mm); p.close()
        c.drawPath(p, fill=1, stroke=0)

    if "inf_der" in posiciones:
        c.setFillColor(COL_AZUL_MARINO)
        p = c.beginPath()
        p.moveTo(W, 0); p.lineTo(W - 75*mm, 0)
        p.curveTo(W - 55*mm, 6*mm, W - 30*mm, 13*mm, W - 5*mm, 9*mm)
        p.lineTo(W, 7*mm); p.close()
        c.drawPath(p, fill=1, stroke=0)


def marca_agua_logo(c, W, H, watermark_path):
    if not watermark_path or not os.path.exists(watermark_path):
        return
    wm_w = 110 * mm
    wm_h = 150 * mm
    c.drawImage(ImageReader(watermark_path),
                (W - wm_w) / 2, (H - wm_h) / 2 - 5 * mm,
                width=wm_w, height=wm_h,
                preserveAspectRatio=True, mask='auto')


# ============================================================
# PILDORA WHATSAPP - SIN ÍCONO, COMPACTA
# ============================================================
def footer_whatsapp(c, W, datos, footer_y=6 * mm):
    texto = f"WhatsApp  {datos['whatsapp']}"
    font_size = 12
    text_w = c.stringWidth(texto, F_BOLD, font_size)

    pill_w = text_w + 12 * mm
    pill_h = 8.5 * mm
    pill_x = (W - pill_w) / 2

    c.setFillColor(COL_VERDE_WHATSAPP)
    _rrect(c, pill_x, footer_y, pill_w, pill_h, r=4.2 * mm)

    c.setFillColor(COL_BLANCO)
    c.setFont(F_BOLD, font_size)
    c.drawCentredString(W / 2, footer_y + pill_h / 2 - 1.6 * mm, texto)


# ============================================================
# PÁGINA 1
# ============================================================
def pagina_1(c, W, H, datos, foto_hero_path, logo_mgo_path, logo_marca_path=None):
    M = 12 * mm

    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    hero_h = H * 0.62
    hero_y_bot = H - hero_h

    c.setFillColor(COL_AZUL_MARINO)
    c.rect(0, hero_y_bot, W, hero_h, fill=1, stroke=0)

    foto_margin = 8 * mm
    foto_x = foto_margin
    foto_y = hero_y_bot + foto_margin
    foto_w = W - 2 * foto_margin
    foto_h = hero_h - 2 * foto_margin

    img = Image.open(foto_hero_path).convert("RGB")
    ir = img.width / img.height
    br = foto_w / foto_h
    if ir > br:
        cw = int(img.height * br)
        l = (img.width - cw) // 2
        cropped = img.crop((l, 0, l + cw, img.height))
    else:
        ch = int(img.width / br)
        t = (img.height - ch) // 2
        cropped = img.crop((0, t, img.width, t + ch))
    temp = f"/tmp/_hero_{abs(hash(foto_hero_path))}.jpg"
    cropped.save(temp, "JPEG", quality=92)
    c.drawImage(ImageReader(temp), foto_x, foto_y,
                width=foto_w, height=foto_h, mask='auto')

    bandas_decorativas(c, W, H,
                       posiciones=("sup_der", "inf_izq", "inf_der"))

    logo_w = 26 * mm
    logo_h = 36 * mm
    if logo_mgo_path and os.path.exists(logo_mgo_path):
        c.drawImage(ImageReader(logo_mgo_path),
                    M, H - 6 * mm - logo_h,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask='auto')

    # === LOGO DE LA MARCA DEL VEHÍCULO (esquina inferior derecha de la foto) ===
    if logo_marca_path and os.path.exists(logo_marca_path):
        brand_logo_size = 18 * mm
        bl_x = foto_x + foto_w - brand_logo_size - 4 * mm
        bl_y = foto_y + 4 * mm
        c.drawImage(ImageReader(logo_marca_path),
                    bl_x, bl_y,
                    width=brand_logo_size, height=brand_logo_size,
                    preserveAspectRatio=True, mask='auto')

    # === TEXTO OVERLAY SOBRE LA FOTO ===
    overlay_h = 36 * mm
    overlay_y = foto_y
    c.saveState()
    c.setFillColorRGB(0.06, 0.13, 0.29, alpha=0.78)
    c.rect(foto_x, overlay_y, foto_w, overlay_h, fill=1, stroke=0)
    c.restoreState()

    text_x = foto_x + 8 * mm

    c.setFillColor(COL_CIAN)
    c.setFont(F_BOLD, 11)
    c.drawString(text_x, overlay_y + overlay_h - 8 * mm,
                 f"{datos['marca'].upper()}     |     MODELO {datos['anio']}")

    c.setFillColor(white)
    c.setFont(F_TITLE, 42)
    c.drawString(text_x, overlay_y + overlay_h - 22 * mm, datos["modelo"])

    c.setStrokeColor(COL_CIAN)
    c.setLineWidth(2)
    c.line(text_x, overlay_y + overlay_h - 25 * mm,
           text_x + 80 * mm, overlay_y + overlay_h - 25 * mm)
    p = c.beginPath()
    p.moveTo(text_x + 80 * mm, overlay_y + overlay_h - 25 * mm)
    p.lineTo(text_x + 76 * mm, overlay_y + overlay_h - 23 * mm)
    p.moveTo(text_x + 80 * mm, overlay_y + overlay_h - 25 * mm)
    p.lineTo(text_x + 76 * mm, overlay_y + overlay_h - 27 * mm)
    c.drawPath(p, stroke=1)

    c.setFillColor(white)
    c.setFont(F_LIGHT, 10)
    c.drawString(text_x, overlay_y + overlay_h - 31 * mm,
                 "1 0 0 %   E L É C T R I C O   /   " + datos["version"].upper())

    zona_y_top = hero_y_bot - 6 * mm

    p_value = datos["precio"]
    if p_value not in ("Consultar precio", "Consultar"):
        if datos["moneda"] == "BOB":
            p_str = f"Bs. {p_value}"
        elif datos["moneda"] == "USD":
            p_str = f"$ {p_value} USD"
        else:
            p_str = f"{p_value} {datos['moneda']}"
        precio_font_size = 22
    else:
        p_str = "Consultar"
        precio_font_size = 18

    label_text = "PRECIO:"
    label_size = 14
    label_w = c.stringWidth(label_text, F_BOLD, label_size)
    precio_w = c.stringWidth(p_str, F_TITLE, precio_font_size)
    pad_h = 8 * mm
    gap_label_precio = 4 * mm
    box_w = label_w + gap_label_precio + precio_w + 2 * pad_h
    box_h = 14 * mm

    box_x = (W - box_w) / 2
    box_y = zona_y_top - box_h

    c.setFillColor(COL_AZUL_MARINO)
    _rrect(c, box_x, box_y, box_w, box_h, r=3 * mm)

    c.setFillColor(COL_CIAN)
    c.setFont(F_BOLD, label_size)
    c.drawString(box_x + pad_h, box_y + box_h / 2 - 1.5 * mm, label_text)

    c.setFillColor(white)
    c.setFont(F_TITLE, precio_font_size)
    c.drawString(box_x + pad_h + label_w + gap_label_precio,
                 box_y + box_h / 2 - 2.5 * mm, p_str)

    ref_y = box_y - 4 * mm
    c.setFillColor(COL_GRIS)
    c.setFont(F_LIGHT, 8)
    c.drawCentredString(W / 2, ref_y,
                        "* o su equivalente en bolivianos al tipo de cambio referencial")

    specs_y_top = ref_y - 4 * mm
    specs_h = 30 * mm
    specs_y = specs_y_top - specs_h

    c.setFillColor(COL_SPECS_BG)
    _rrect(c, M, specs_y, W - 2 * M, specs_h, r=4 * mm)

    cols = 4
    col_w = (W - 2 * M) / cols

    for i, (valor, label) in enumerate(datos["datos_clave"]):
        cx = M + i * col_w + col_w / 2

        c.setFillColor(COL_AZUL_MEDIO)
        c.setFont(F_BOLD, 9)
        c.drawCentredString(cx, specs_y_top - 9 * mm, label)

        c.setFillColor(COL_AZUL_MARINO)
        valor_size = 18
        if c.stringWidth(valor, F_TITLE, valor_size) > col_w - 6 * mm:
            valor_size = 14
        c.setFont(F_TITLE, valor_size)
        c.drawCentredString(cx, specs_y_top - 21 * mm, valor)

        if i < cols - 1:
            c.setStrokeColor(HexColor("#B8C0CC"))
            c.setLineWidth(0.6)
            c.line(M + (i + 1) * col_w, specs_y + 5 * mm,
                   M + (i + 1) * col_w, specs_y + specs_h - 5 * mm)

    entrega_y_top = specs_y - 5 * mm
    entrega_h = 13 * mm
    entrega_y = entrega_y_top - entrega_h

    c.setFillColor(COL_CIAN)
    _rrect(c, M, entrega_y, W - 2 * M, entrega_h, r=3 * mm)

    c.setFillColor(COL_AZUL_MARINO)
    c.setFont(F_TITLE, 14)
    c.drawCentredString(W / 2, entrega_y + entrega_h / 2 - 1.8 * mm,
                        "ENTREGA INMEDIATA  ·  LA PAZ, BOLIVIA")

    footer_whatsapp(c, W, datos)


# ============================================================
# PÁGINA 2
# ============================================================
def pagina_2(c, W, H, datos, fotos_secciones, logo_mgo_path, watermark_path,
             truncados_log=None):
    M = 12 * mm

    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    marca_agua_logo(c, W, H, watermark_path)
    bandas_decorativas(c, W, H, posiciones=("sup_der", "inf_izq", "inf_der"))

    logo_w = 14 * mm
    logo_h = 19 * mm
    if logo_mgo_path and os.path.exists(logo_mgo_path):
        c.drawImage(ImageReader(logo_mgo_path),
                    M, H - 6 * mm - logo_h,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask='auto')

    c.setFillColor(COL_AZUL_MARINO)
    c.setFont(F_TITLE, 20)
    c.drawCentredString(W / 2, H - 14 * mm, "Especificaciones Técnicas")

    c.setFillColor(COL_SUBTITULO)
    c.setFont(F_BOLD, 9)
    c.drawCentredString(W / 2, H - 20 * mm,
                        f"{datos['modelo']}  -  Modelo {datos['anio']}  -  {datos['version']}")

    sec_y_top = H - 26 * mm
    sec_y_bottom = 22 * mm
    sec_total_h = sec_y_top - sec_y_bottom

    secciones = [
        ("TREN MOTRIZ Y RENDIMIENTO", datos["tren_motriz"], "left",
         fotos_secciones.get("tren_motriz")),
        ("BATERÍA Y CARGA", datos["bateria_carga"], "right",
         fotos_secciones.get("bateria_carga")),
        ("EXTERIOR Y DISEÑO", datos["exterior"], "left",
         fotos_secciones.get("exterior")),
        ("INTERIOR Y CONFORT", datos["interior"], "right",
         fotos_secciones.get("interior")),
        ("SEGURIDAD Y ASISTENCIAS", datos["seguridad"], "left",
         fotos_secciones.get("seguridad")),
    ]

    sec_h = sec_total_h / len(secciones)
    sec_gap = 2 * mm

    for idx, (titulo, items, orientacion, foto) in enumerate(secciones):
        sy_top = sec_y_top - idx * sec_h
        sy_bottom = sy_top - sec_h + sec_gap

        if orientacion == "left":
            text_x = M
            text_w = (W - 2 * M) * 0.72 - 3 * mm
            foto_x = M + text_w + 3 * mm
            foto_w = (W - 2 * M) - text_w - 3 * mm
        else:
            foto_x = M
            foto_w = (W - 2 * M) * 0.28 - 3 * mm
            text_x = foto_x + foto_w + 3 * mm
            text_w = (W - 2 * M) - foto_w - 3 * mm

        foto_y = sy_bottom + 1 * mm
        foto_h = sec_h - sec_gap - 2 * mm

        if foto and os.path.exists(foto):
            try:
                _img_smart(c, foto, foto_x, foto_y, foto_w, foto_h)
                c.setStrokeColor(COL_GRIS_CLARO)
                c.setLineWidth(0.5)
                c.rect(foto_x, foto_y, foto_w, foto_h, fill=0, stroke=1)
            except Exception:
                c.setFillColor(COL_GRIS_CLARO)
                c.rect(foto_x, foto_y, foto_w, foto_h, fill=1, stroke=0)

        c.setFillColor(COL_AZUL_MARINO)
        c.setFont(F_TITLE, 11)
        c.drawString(text_x, sy_top - 4 * mm, titulo)

        c.setStrokeColor(COL_CIAN)
        c.setLineWidth(1.5)
        c.line(text_x, sy_top - 6 * mm, text_x + 25 * mm, sy_top - 6 * mm)

        _render_items_2cols(c, items, text_x, text_w,
                            sy_top - 10 * mm, sy_bottom + 1 * mm,
                            truncados_log=truncados_log,
                            seccion_nombre=titulo)

    footer_whatsapp(c, W, datos)


# ============================================================
# PÁGINA 3
# ============================================================
def pagina_3(c, W, H, datos, fotos_secciones, logo_mgo_path, watermark_path,
             truncados_log=None):
    M = 12 * mm

    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    marca_agua_logo(c, W, H, watermark_path)
    bandas_decorativas(c, W, H, posiciones=("sup_der", "inf_izq", "inf_der"))

    logo_w = 14 * mm
    logo_h = 19 * mm
    if logo_mgo_path and os.path.exists(logo_mgo_path):
        c.drawImage(ImageReader(logo_mgo_path),
                    M, H - 6 * mm - logo_h,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask='auto')

    c.setFillColor(COL_AZUL_MARINO)
    c.setFont(F_TITLE, 20)
    c.drawCentredString(W / 2, H - 14 * mm, "Información Complementaria")

    c.setFillColor(COL_SUBTITULO)
    c.setFont(F_BOLD, 9)
    c.drawCentredString(W / 2, H - 20 * mm,
                        f"{datos['modelo']}  -  Modelo {datos['anio']}  -  {datos['version']}")

    sec_y_top = H - 26 * mm
    sec_y_bottom = 22 * mm
    sec_total_h = sec_y_top - sec_y_bottom

    secciones = [
        ("ASISTENCIAS A LA CONDUCCIÓN (ADAS)", datos["asistencias_adas"], "right",
         fotos_secciones.get("adas")),
        ("TECNOLOGÍA Y CONECTIVIDAD", datos["tecnologia_conectividad"], "left",
         fotos_secciones.get("tecnologia")),
        ("DIMENSIONES Y CAPACIDADES", datos["dimensiones_capacidades"], "right",
         fotos_secciones.get("dimensiones")),
    ]

    sec_h = sec_total_h / len(secciones)
    sec_gap = 2 * mm

    for idx, (titulo, items, orientacion, foto) in enumerate(secciones):
        sy_top = sec_y_top - idx * sec_h
        sy_bottom = sy_top - sec_h + sec_gap

        if orientacion == "left":
            text_x = M
            text_w = (W - 2 * M) * 0.72 - 3 * mm
            foto_x = M + text_w + 3 * mm
            foto_w = (W - 2 * M) - text_w - 3 * mm
        else:
            foto_x = M
            foto_w = (W - 2 * M) * 0.28 - 3 * mm
            text_x = foto_x + foto_w + 3 * mm
            text_w = (W - 2 * M) - foto_w - 3 * mm

        foto_y = sy_bottom + 1 * mm
        foto_h = sec_h - sec_gap - 2 * mm

        if foto and os.path.exists(foto):
            try:
                _img_smart(c, foto, foto_x, foto_y, foto_w, foto_h)
                c.setStrokeColor(COL_GRIS_CLARO)
                c.setLineWidth(0.5)
                c.rect(foto_x, foto_y, foto_w, foto_h, fill=0, stroke=1)
            except Exception:
                c.setFillColor(COL_GRIS_CLARO)
                c.rect(foto_x, foto_y, foto_w, foto_h, fill=1, stroke=0)

        c.setFillColor(COL_AZUL_MARINO)
        c.setFont(F_TITLE, 11)
        c.drawString(text_x, sy_top - 4 * mm, titulo)

        c.setStrokeColor(COL_CIAN)
        c.setLineWidth(1.5)
        c.line(text_x, sy_top - 6 * mm, text_x + 25 * mm, sy_top - 6 * mm)

        _render_items_2cols(c, items, text_x, text_w,
                            sy_top - 10 * mm, sy_bottom + 1 * mm,
                            truncados_log=truncados_log,
                            seccion_nombre=titulo)

    footer_whatsapp(c, W, datos)


# ============================================================
# API PRINCIPAL
# ============================================================
def generar_ficha(output_path, datos, foto_principal, fotos_secciones,
                  logo_mgo_path=None, watermark_path=None, logo_marca_path=None):
    """Genera el PDF de ficha técnica MGO con el diseño v8.

    Args:
        output_path: ruta donde se guarda el PDF
        datos: dict con todos los campos (ver DEFAULT_DATOS)
        foto_principal: ruta a la foto hero (pagina 1)
        fotos_secciones: dict con claves: tren_motriz, bateria_carga, exterior,
                         interior, seguridad, adas, tecnologia, dimensiones
        logo_mgo_path: ruta al logo MGO
        watermark_path: ruta a la marca de agua MGO
        logo_marca_path: ruta al logo de la marca del vehículo (opcional)

    Returns:
        list: log de items truncados (cada entry tiene seccion, item,
        item_truncado, tipo)
    """
    if logo_mgo_path is None:
        logo_mgo_path = os.path.join(_BASE_DIR, "assets", "logo_mgo_clean.png")
    if watermark_path is None:
        watermark_path = os.path.join(_BASE_DIR, "assets", "logo_mgo_watermark.png")

    truncados_log = []
    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4
    pagina_1(c, W, H, datos, foto_principal, logo_mgo_path, logo_marca_path)
    c.showPage()
    pagina_2(c, W, H, datos, fotos_secciones, logo_mgo_path, watermark_path,
             truncados_log=truncados_log)
    c.showPage()
    pagina_3(c, W, H, datos, fotos_secciones, logo_mgo_path, watermark_path,
             truncados_log=truncados_log)
    c.showPage()
    c.save()
    return truncados_log
