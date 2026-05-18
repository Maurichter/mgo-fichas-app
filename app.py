"""
MGO - Generador de Fichas Técnicas
==================================
App Streamlit para generar fichas técnicas PDF de vehículos eléctricos
con el diseño v8 oficial de Merch and Go.

Flujo:
  1) Subir PDF en inglés del fabricante → extracción de texto
  2) Copiar prompt + texto a Claude.ai → recibir JSON traducido
  3) Pegar JSON en la app → revisar/editar todos los campos
  4) Subir fotos (8-12) + logo de marca (opcional)
  5) Generar PDF y descargar
"""
import streamlit as st
import os
import io
import tempfile
import zipfile
from pathlib import Path

from extraccion import extraer_texto_pdf, estadisticas_texto
from prompt_template import construir_prompt, validar_json_respuesta
from ficha_renderer import generar_ficha, DEFAULT_DATOS


# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================
st.set_page_config(
    page_title="MGO - Generador de Fichas",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS para acercarse al look MGO
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #15214B 0%, #0C5687 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .step-header {
        background: #15214B;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 1rem 0 0.5rem 0;
        font-weight: bold;
    }
    .info-box {
        background: #E8EBF0;
        border-left: 4px solid #13C5DF;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .warn-box {
        background: #FFF4E5;
        border-left: 4px solid #FF9800;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #E8F5E9;
        border-left: 4px solid #25D366;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    .stButton button {
        background-color: #15214B;
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #13C5DF;
        color: #15214B;
    }
    .stDownloadButton button {
        background-color: #25D366;
        color: white;
        font-weight: bold;
        padding: 0.75rem 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================
# ESTADO PERSISTENTE
# ==============================================================
def init_state():
    defaults = {
        "texto_extraido": None,
        "datos": None,
        "json_raw": "",
        "fotos_subidas": {},   # nombre_archivo -> bytes
        "asignaciones": {},    # seccion -> nombre_archivo
        "logo_marca": None,    # bytes
        "precio": "30,000",
        "pdf_generado": None,
        "truncados": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ==============================================================
# HEADER
# ==============================================================
st.markdown("""
<div class='main-header'>
    <h1 style='margin:0;'>🚗 MGO · Generador de Fichas Técnicas</h1>
    <p style='margin:0; opacity: 0.9;'>Merch and Go · La Paz, Bolivia · WhatsApp 73017677</p>
</div>
""", unsafe_allow_html=True)


# ==============================================================
# SIDEBAR — instrucciones generales
# ==============================================================
with st.sidebar:
    st.header("📋 Cómo usar la app")
    st.markdown("""
1. **Subir** la ficha técnica oficial en inglés del fabricante
2. **Copiar** el texto + prompt y pegarlo en Claude.ai
3. **Pegar** la respuesta JSON aquí
4. **Revisar y editar** todos los datos antes de generar
5. **Subir las fotos** del vehículo (8 a 12)
6. **Generar el PDF** y descargar

---

**Recomendación:** usa Claude.ai con el modelo más potente disponible (Opus o Sonnet) para la traducción. La calidad de la ficha depende de ese paso.
""")
    st.markdown("---")
    if st.button("🔄 Empezar de cero (resetear)", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ==============================================================
# PASO 1 — Subir PDF inglés y extraer texto
# ==============================================================
st.markdown("<div class='step-header'>PASO 1 · Subir la ficha técnica oficial en inglés</div>",
            unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    pdf_file = st.file_uploader(
        "PDF del fabricante (inglés)",
        type=["pdf"],
        help="Sube el PDF oficial de especificaciones técnicas del vehículo."
    )

    if pdf_file is not None:
        try:
            bytes_pdf = pdf_file.read()
            st.session_state.texto_extraido = extraer_texto_pdf(bytes_pdf)
            stats = estadisticas_texto(st.session_state.texto_extraido)
            st.markdown(f"""
<div class='success-box'>
✅ <b>Texto extraído correctamente</b><br>
{stats['paginas']} páginas · {stats['palabras']:,} palabras · {stats['caracteres']:,} caracteres
</div>
""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error procesando el PDF: {e}")

with col2:
    if st.session_state.texto_extraido:
        with st.expander("👁️ Ver el texto extraído", expanded=False):
            st.text_area("", st.session_state.texto_extraido, height=300, disabled=True,
                        label_visibility="collapsed")


# ==============================================================
# PASO 2 — Copy-paste a Claude.ai
# ==============================================================
if st.session_state.texto_extraido:
    st.markdown("<div class='step-header'>PASO 2 · Traducir con Claude.ai</div>",
                unsafe_allow_html=True)

    prompt_completo = construir_prompt(st.session_state.texto_extraido)

    st.markdown("""
<div class='info-box'>
<b>Cómo hacerlo:</b><br>
1. Hacé clic en <b>"Copiar al portapapeles"</b> abajo<br>
2. Abrí <b>claude.ai</b> en otra pestaña (usá Sonnet 4.6 u Opus 4.7 si los tenés disponibles)<br>
3. Pegá y enviá. Claude te devolverá un bloque JSON entre triple backtick.<br>
4. Copiá el JSON completo y pegalo en el cuadro de abajo.
</div>
""", unsafe_allow_html=True)

    with st.expander("📋 Ver el prompt completo (~"
                     f"{len(prompt_completo):,} caracteres)",
                     expanded=False):
        st.code(prompt_completo, language="markdown")

    # Botón copy: usamos st.code que tiene botón copy nativo
    st.markdown("**👇 Hacé clic en el ícono de copiar (esquina sup. der.):**")
    st.code(prompt_completo, language="markdown")

    st.markdown("---")

    json_input = st.text_area(
        "Pegá aquí el JSON que te devolvió Claude.ai:",
        value=st.session_state.json_raw,
        height=200,
        placeholder='```json\n{\n  "marca": "Volkswagen",\n  "modelo": "ID.3",\n  ...\n}\n```'
    )

    if json_input != st.session_state.json_raw:
        st.session_state.json_raw = json_input

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        procesar = st.button("✅ Procesar JSON", use_container_width=True)

    if procesar and json_input.strip():
        datos, errores = validar_json_respuesta(json_input)
        if datos is None:
            st.error(f"❌ {errores[0]}")
        else:
            st.session_state.datos = datos
            if errores:
                for e in errores:
                    st.warning(f"⚠️ {e}")
            else:
                st.success(f"✅ Datos validados: {datos['marca']} {datos['modelo']} {datos['anio']}")


# ==============================================================
# PASO 3 — Revisar/editar todos los datos
# ==============================================================
if st.session_state.datos is not None:
    st.markdown("<div class='step-header'>PASO 3 · Revisar y editar los datos</div>",
                unsafe_allow_html=True)

    st.markdown("""
<div class='info-box'>
Revisá cada campo. Borrá items que no estén confirmados en la ficha oficial.
Cada ítem que sea muy largo podría truncarse con "..." en el PDF — más
abajo te aviso cuáles.
</div>
""", unsafe_allow_html=True)

    datos = st.session_state.datos

    # --- Campos básicos
    st.subheader("📌 Información básica")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        datos["marca"] = st.text_input("Marca", value=datos.get("marca", ""))
    with c2:
        datos["modelo"] = st.text_input("Modelo", value=datos.get("modelo", ""))
    with c3:
        datos["anio"] = st.text_input("Año", value=datos.get("anio", ""))
    with c4:
        datos["version"] = st.text_input("Versión", value=datos.get("version", ""))

    # --- Datos clave (4 destacados)
    st.subheader("⭐ Datos clave (página 1)")
    st.caption("Los 4 destacados grandes en la página hero. Valor + label fijo.")

    dc = datos.get("datos_clave", [])
    while len(dc) < 4:
        dc.append(("--", "--"))

    nuevos_dc = []
    cols = st.columns(4)
    labels_fijos = ["MOTOR", "AUTONOMÍA", "TRANSMISIÓN", "POTENCIA"]
    for i, col in enumerate(cols):
        with col:
            label = labels_fijos[i]
            st.caption(f"**{label}**")
            valor = st.text_input(
                f"Valor", value=str(dc[i][0]) if i < len(dc) else "",
                key=f"dc_val_{i}",
                label_visibility="collapsed"
            )
            nuevos_dc.append((valor.upper(), label))
    datos["datos_clave"] = nuevos_dc

    # --- Las 8 secciones de items
    st.subheader("📝 Secciones de la ficha")

    secciones_meta = [
        ("tren_motriz", "🔧 Tren motriz y rendimiento", "(página 2 - ~11 items)", 11),
        ("bateria_carga", "🔋 Batería y carga", "(página 2 - ~11 items)", 11),
        ("exterior", "🚗 Exterior y diseño", "(página 2 - ~19 items)", 19),
        ("interior", "🛋️ Interior y confort", "(página 2 - ~20 items)", 20),
        ("seguridad", "🛡️ Seguridad y asistencias", "(página 2 - ~18 items)", 18),
        ("asistencias_adas", "🎯 Asistencias a la conducción (ADAS)", "(página 3 - ~17 items)", 17),
        ("tecnologia_conectividad", "📱 Tecnología y conectividad", "(página 3 - ~23 items)", 23),
        ("dimensiones_capacidades", "📐 Dimensiones y capacidades", "(página 3 - ~18 items)", 18),
    ]

    # Avisos de items muy largos
    items_largos = []
    for key, _, _, _ in secciones_meta:
        for item in datos.get(key, []):
            if len(item) > 70:
                items_largos.append((key, item))

    if items_largos:
        with st.expander(f"⚠️ {len(items_largos)} items podrían truncarse "
                         "(más de 70 caracteres)", expanded=True):
            for k, it in items_largos:
                st.warning(f"**{k}**: {it} ({len(it)} chars)")

    tabs = st.tabs([f"{lbl.split(' ', 1)[0]} {lbl.split(' ', 1)[1].split(' y ')[0]}"
                    for _, lbl, _, _ in secciones_meta])

    for tab, (key, label, ayuda, n_default) in zip(tabs, secciones_meta):
        with tab:
            st.markdown(f"**{label}** · {ayuda}")
            items_actuales = datos.get(key, [])
            texto_items = "\n".join(items_actuales)
            n_lineas = max(8, len(items_actuales) + 2)
            nuevo_texto = st.text_area(
                f"Un ítem por línea:",
                value=texto_items,
                height=min(450, 26 * n_lineas),
                key=f"items_{key}",
                help="Cada línea es un bullet en la ficha. Líneas vacías se ignoran."
            )
            # Parsear el text_area
            datos[key] = [line.strip() for line in nuevo_texto.split("\n") if line.strip()]
            st.caption(f"Total: **{len(datos[key])} items**")

    st.session_state.datos = datos


# ==============================================================
# PASO 4 — Fotos + logo + precio
# ==============================================================
if st.session_state.datos is not None:
    st.markdown("<div class='step-header'>PASO 4 · Fotos, logo y precio</div>",
                unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    # === FOTOS ===
    with col_left:
        st.subheader("📸 Fotos del vehículo")
        st.caption("Subí 8-12 fotos. La primera será la HERO (foto grande de portada).")

        fotos_files = st.file_uploader(
            "Fotos del vehículo (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="fotos_uploader"
        )

        if fotos_files:
            # Guardar bytes y nombres en estado
            nuevas = {}
            for f in fotos_files:
                nuevas[f.name] = f.read()
            st.session_state.fotos_subidas = nuevas

            # Asignación automática: orden de subida
            # Ranuras: hero, tren_motriz, bateria_carga, exterior, interior,
            #          seguridad, adas, tecnologia, dimensiones
            ranuras = ["hero", "tren_motriz", "bateria_carga", "exterior",
                       "interior", "seguridad", "adas", "tecnologia",
                       "dimensiones"]
            nombres = list(nuevas.keys())
            asign = {}
            for i, ranura in enumerate(ranuras):
                if i < len(nombres):
                    asign[ranura] = nombres[i]
                else:
                    # Reutilizar de forma sensata: rotar las que ya hay
                    asign[ranura] = nombres[i % len(nombres)] if nombres else None

            # Sólo aplicar la asignación auto si todavía no hay manual
            # o si el set de archivos cambió
            current_files = set(st.session_state.asignaciones.values())
            new_files = set(nombres)
            if not st.session_state.asignaciones or current_files != new_files:
                # Pero si las anteriores siguen presentes, conservar
                if current_files.issubset(new_files) and st.session_state.asignaciones:
                    pass  # mantener manual
                else:
                    st.session_state.asignaciones = asign

            st.success(f"📸 {len(fotos_files)} fotos cargadas")

            # Previews + reasignación
            st.markdown("**Asignación por sección** (reasignar si querés):")
            ranura_labels = {
                "hero": "🏁 HERO (portada)",
                "tren_motriz": "🔧 Tren motriz",
                "bateria_carga": "🔋 Batería",
                "exterior": "🚗 Exterior",
                "interior": "🛋️ Interior",
                "seguridad": "🛡️ Seguridad",
                "adas": "🎯 ADAS",
                "tecnologia": "📱 Tecnología",
                "dimensiones": "📐 Dimensiones",
            }
            for ranura in ranuras:
                cur = st.session_state.asignaciones.get(ranura)
                idx = nombres.index(cur) if cur in nombres else 0
                seleccion = st.selectbox(
                    ranura_labels[ranura],
                    nombres,
                    index=idx,
                    key=f"asig_{ranura}",
                )
                st.session_state.asignaciones[ranura] = seleccion

    # === LOGO + PRECIO ===
    with col_right:
        st.subheader("🏷️ Logo de la marca")
        st.caption("PNG con fondo transparente, opcional")
        logo_file = st.file_uploader(
            "Logo (opcional)",
            type=["png", "jpg", "jpeg"],
            key="logo_marca_uploader"
        )
        if logo_file:
            st.session_state.logo_marca = logo_file.read()
            st.image(st.session_state.logo_marca, width=120)
        elif st.session_state.logo_marca is not None:
            st.image(st.session_state.logo_marca, width=120)

        st.markdown("---")
        st.subheader("💵 Precio")
        precio_input = st.text_input(
            "Precio en USD",
            value=st.session_state.precio,
            help="Sin signo $ ni USD. Ejemplo: 30,000 · 28,500 · Consultar"
        )
        st.session_state.precio = precio_input


# ==============================================================
# PASO 5 — Generar PDF
# ==============================================================
if st.session_state.datos is not None and st.session_state.fotos_subidas:
    st.markdown("<div class='step-header'>PASO 5 · Generar la ficha PDF</div>",
                unsafe_allow_html=True)

    # Verificar que tenemos al menos la foto hero asignada
    hero_asignada = st.session_state.asignaciones.get("hero")
    if not hero_asignada:
        st.warning("⚠️ Falta asignar la foto HERO (portada)")
    else:
        col_gen, col_info = st.columns([1, 2])
        with col_gen:
            generar_btn = st.button("🚀 Generar PDF", type="primary", use_container_width=True)

        with col_info:
            n_fotos = len(st.session_state.fotos_subidas)
            n_items_total = sum(len(st.session_state.datos.get(k, [])) for k in [
                "tren_motriz", "bateria_carga", "exterior", "interior", "seguridad",
                "asistencias_adas", "tecnologia_conectividad", "dimensiones_capacidades"])
            st.info(f"📸 {n_fotos} fotos · 📝 {n_items_total} items · "
                   f"💵 USD {st.session_state.precio}")

        if generar_btn:
            with st.spinner("Generando PDF..."):
                # Volcar las fotos a archivos temporales
                tmpdir = tempfile.mkdtemp(prefix="mgo_")
                fotos_paths = {}
                for nombre, bytes_data in st.session_state.fotos_subidas.items():
                    path = os.path.join(tmpdir, nombre)
                    with open(path, "wb") as f:
                        f.write(bytes_data)
                    fotos_paths[nombre] = path

                # Logo de marca
                logo_marca_path = None
                if st.session_state.logo_marca:
                    logo_marca_path = os.path.join(tmpdir, "logo_marca.png")
                    with open(logo_marca_path, "wb") as f:
                        f.write(st.session_state.logo_marca)

                # Construir el dict de fotos por sección
                fotos_secciones = {}
                for ranura in ["tren_motriz", "bateria_carga", "exterior",
                              "interior", "seguridad", "adas", "tecnologia",
                              "dimensiones"]:
                    nombre = st.session_state.asignaciones.get(ranura)
                    fotos_secciones[ranura] = fotos_paths.get(nombre)

                foto_hero_path = fotos_paths.get(
                    st.session_state.asignaciones.get("hero")
                )

                # Aplicar precio
                datos_final = dict(st.session_state.datos)
                datos_final["precio"] = st.session_state.precio
                datos_final["moneda"] = "USD"
                datos_final["whatsapp"] = "73017677"
                datos_final["ciudad"] = "La Paz, Bolivia"

                # Generar
                output_path = os.path.join(tmpdir, "ficha_mgo.pdf")
                try:
                    truncados = generar_ficha(
                        output_path=output_path,
                        datos=datos_final,
                        foto_principal=foto_hero_path,
                        fotos_secciones=fotos_secciones,
                        logo_marca_path=logo_marca_path,
                    )
                    with open(output_path, "rb") as f:
                        st.session_state.pdf_generado = f.read()
                    st.session_state.truncados = truncados

                    nombre_pdf = (f"ficha_MGO_{datos_final['marca']}_"
                                 f"{datos_final['modelo']}.pdf"
                                 .replace(" ", "_").replace(".", ""))
                    st.session_state.nombre_pdf = nombre_pdf.replace("pdf", ".pdf")

                except Exception as e:
                    st.error(f"❌ Error al generar el PDF: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # === Si ya hay un PDF generado, mostrarlo ===
        if st.session_state.pdf_generado:
            st.markdown("""
<div class='success-box'>
✅ <b>PDF generado correctamente</b>
</div>
""", unsafe_allow_html=True)

            # Avisos de truncado
            truncados_real = [t for t in st.session_state.truncados
                             if t.get("tipo") == "truncado"]
            no_dibujados = [t for t in st.session_state.truncados
                           if t.get("tipo") == "no_dibujado"]

            if truncados_real:
                with st.expander(f"⚠️ {len(truncados_real)} items se truncaron con '...'",
                               expanded=True):
                    for t in truncados_real:
                        st.warning(f"**{t['seccion']}**: {t['item_original']} "
                                 f"→ se mostró como: *{t['item_truncado']}*")

            if no_dibujados:
                with st.expander(f"🚫 {len(no_dibujados)} items NO se dibujaron "
                               "(no entraban)", expanded=True):
                    for t in no_dibujados:
                        st.error(f"**{t['seccion']}**: {t['item']}")
                    st.caption("Sugerencia: reducí la cantidad de items en esa sección.")

            # Botón de descarga + preview
            nombre = st.session_state.get("nombre_pdf", "ficha_mgo.pdf")
            st.download_button(
                "📥 Descargar PDF",
                data=st.session_state.pdf_generado,
                file_name=nombre,
                mime="application/pdf",
                use_container_width=False,
            )

            # Preview embebido
            st.markdown("**Preview:**")
            import base64
            b64 = base64.b64encode(st.session_state.pdf_generado).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="900" style="border:1px solid #ddd; border-radius:8px;"></iframe>',
                unsafe_allow_html=True,
            )
