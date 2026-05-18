# 🚗 MGO - Generador de Fichas Técnicas

App web para Merch and Go (La Paz, Bolivia) que genera fichas técnicas PDF
de vehículos eléctricos con el diseño v8 oficial, partiendo de un PDF en
inglés del fabricante.

---

## 📑 Tabla de contenidos
1. [Cómo desplegar la app en Streamlit Cloud (gratis)](#1-cómo-desplegar)
2. [Cómo usar la app día a día](#2-cómo-usar)
3. [Cómo actualizar la app después](#3-cómo-actualizar)
4. [Solución de problemas comunes](#4-troubleshooting)

---

## 1. Cómo desplegar

> **Costo total: $0**. Solo necesitás una cuenta de Google o GitHub.
> **Tiempo: ~10 minutos** la primera vez.

### Paso 1 · Crear cuenta de GitHub
1. Andá a https://github.com/signup
2. Registrate con tu correo. Verificalo.
3. Cuando te pida "username" usá algo como `merchandgo` o `mgo-app`.

### Paso 2 · Crear el repositorio del código
1. Una vez logueado en GitHub, hacé clic en el **+** arriba a la derecha
   → **New repository**
2. **Repository name**: `mgo-fichas-app`
3. **Description**: "Generador de fichas técnicas MGO"
4. Dejá **Public** seleccionado (es gratis y necesario para Streamlit Cloud
   sin pagar)
5. Marcá ✅ **Add a README file**
6. Hacé clic en **Create repository**

### Paso 3 · Subir los archivos de la app
En la página de tu nuevo repo, hacé clic en **Add file → Upload files**.
Arrastrá **TODO** el contenido de la carpeta `mgo_app/` (la que te entregamos)
**incluyendo la subcarpeta `assets/`**.

> **Importante**: el archivo `.gitignore` y la carpeta `.streamlit/` empiezan
> con punto y están "ocultos" en algunos sistemas. Asegurate de subirlos
> también, sino la app no se va a ver con los colores correctos.

Estructura final esperada en GitHub:

```
mgo-fichas-app/
├── app.py
├── ficha_renderer.py
├── extraccion.py
├── prompt_template.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── assets/
    ├── logo_mgo_clean.png
    ├── logo_mgo_watermark.png
    └── fonts/
        ├── FuturaBoldReal.ttf
        ├── FuturaBookReal.ttf
        ├── FuturaLightReal.ttf
        ├── FuturaMediumReal.ttf
        ├── OpenSans-Bold.ttf
        ├── OpenSans-Light.ttf
        ├── OpenSans-Regular.ttf
        └── OpenSans-SemiBold.ttf
```

Al final hacé clic en **Commit changes** (verde, abajo).

### Paso 4 · Conectar Streamlit Cloud
1. Andá a https://share.streamlit.io
2. Hacé clic en **Sign up** → **Continue with GitHub**
3. Autorizá la conexión cuando GitHub te lo pida
4. Una vez dentro, hacé clic en **Create app** (arriba a la derecha)
5. Elegí **Deploy a public app from GitHub**
6. Completá:
   - **Repository**: `tu-usuario/mgo-fichas-app`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (opcional): `mgo-fichas` → quedará `https://mgo-fichas.streamlit.app`
7. Hacé clic en **Deploy**

La primera vez tarda **2-5 minutos** en instalar todo. Cuando termine, vas
a ver la app funcionando.

> **Guardá la URL** (algo tipo `https://mgo-fichas.streamlit.app`) — esa es
> la dirección a la que vos y tu equipo van a entrar siempre.

---

## 2. Cómo usar

Una vez desplegada, el flujo de generar una ficha es así (5-10 minutos):

### Paso 1 · Subir el PDF en inglés
- Hacé clic en **"PDF del fabricante (inglés)"**
- Subí el PDF oficial de especificaciones técnicas
- La app extrae el texto automáticamente y te muestra estadísticas

### Paso 2 · Traducir con Claude.ai (la parte que usa tu suscripción)
1. En la sección **"PASO 2"** verás un bloque grande con instrucciones + texto
2. **Pasá el mouse sobre el bloque** y hacé clic en el ícono de copiar
   (esquina superior derecha del bloque)
3. Abrí **https://claude.ai** en otra pestaña
4. Asegurate de tener seleccionado **Claude Sonnet** o **Claude Opus**
   (no Haiku — querés la mejor calidad para esto)
5. Pegá lo que copiaste (Ctrl+V) y presioná Enter
6. Claude te va a devolver un bloque JSON grande
7. Hacé clic en el ícono **"Copy"** que aparece al pasar el mouse sobre
   el JSON en la respuesta de Claude
8. Volvé a la pestaña de la app MGO
9. Pegá el JSON en el cuadro **"Pegá aquí el JSON..."**
10. Hacé clic en **"Procesar JSON"**

### Paso 3 · Revisar y editar los datos
- Vas a ver todos los campos editables: marca, modelo, año, versión,
  los 4 datos clave, y las 8 secciones de items
- Las secciones están en pestañas (Tren motriz, Batería, etc.)
- **Borrá cualquier item que no esté confirmado en la ficha oficial**.
  Mejor menos items reales que más items inventados.
- Si algún item es muy largo (>70 caracteres) la app te avisa arriba
- Podés agregar ítems escribiéndolos directamente

### Paso 4 · Subir las fotos y precio
- **Fotos**: subí 8 a 12 fotos del vehículo. La app las asigna automáticamente
  por orden de subida: la primera será la HERO (portada), las demás van a
  cada sección.
- **Reasignar**: si querés que una foto específica vaya a otra sección, usá
  los desplegables que aparecen debajo.
- **Logo de marca** (opcional): PNG con fondo transparente del logo de
  la marca del auto. Va en la esquina inferior derecha de la foto hero.
- **Precio**: en USD, sin signo de dólar. Ejemplo: `30,000` o `28,500`. Si
  ponés `Consultar`, aparece "Consultar" en la ficha en vez del precio.

### Paso 5 · Generar y descargar
- Hacé clic en **"🚀 Generar PDF"**
- En ~5 segundos aparece el preview embebido + botón de descarga
- Si algún ítem se truncó con "..." te aparece un aviso con el detalle

---

## 3. Cómo actualizar

Si en el futuro queremos cambiar algo (agregar una sección, cambiar un color,
arreglar un bug), el flujo es:

1. Le pedís a Claude que te dé los archivos modificados
2. Andás a tu repo en GitHub
3. Hacés clic en el archivo a modificar → ícono del lápiz → pegás el nuevo
   contenido → **Commit changes**
4. Streamlit Cloud detecta el cambio y **redespliega la app automáticamente**
   (~1 minuto)

---

## 4. Troubleshooting

### "La app dice que no encuentra los archivos de fuentes"
Asegurate de haber subido a GitHub **toda** la carpeta `assets/fonts/` con
los 8 archivos .ttf adentro.

### "La página se ve sin colores ni estilos correctos"
Probablemente no subiste la carpeta `.streamlit/` con el `config.toml`.
Esa carpeta empieza con un punto y a veces los sistemas la ocultan.

### "Streamlit Cloud me dice que la app está dormida"
Streamlit Cloud apaga las apps gratuitas si no se usan por unos días.
Es normal. La primera persona que la abre la "despierta" en ~30 segundos.

### "Claude.ai me devuelve algo que no se ve como JSON"
- Asegurate de estar usando Sonnet u Opus, no Haiku
- Si Claude se distrae, mandale otro mensaje pidiéndole que **solo devuelva
  el JSON entre triple backtick**
- Verificá que en la app pegaste todo desde la `{` inicial hasta la `}` final

### "El PDF se genera pero algunos items aparecen con '...'"
Eso significa que algún ítem es demasiado largo para el espacio disponible
en la página. Volvé al Paso 3 y acortá ese ítem manualmente.

### "El PDF se genera pero faltan items en alguna sección"
Significa que metiste demasiados items y no entraban todos. La app te lo
avisa en el panel "🚫 X items NO se dibujaron". Reducí la cantidad de items
en esa sección.

### "Necesito generar muchas fichas seguidas"
Cada ficha es una sesión independiente. Si querés empezar de cero, usá el
botón **"🔄 Empezar de cero (resetear)"** en la barra lateral izquierda.

---

## 📞 Datos fijos del proyecto

- **WhatsApp MGO**: 73017677
- **Ciudad**: La Paz, Bolivia
- **Colores oficiales**:
  - Azul marino: `#15214B`
  - Cian: `#13C5DF`
  - Verde WhatsApp: `#25D366`
- **Fuentes**: Futura Bold (títulos) + Open Sans (cuerpo)
- **Tamaño de página**: A4
