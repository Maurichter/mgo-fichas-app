"""
Generador del prompt para Claude.ai (flujo copy-paste manual).
El usuario abre claude.ai, pega este texto, y recibe de vuelta un JSON
que después pega en la app.
"""

# Estructura JSON que Claude.ai debe devolver. Es la misma que espera
# ficha_renderer.generar_ficha().
ESTRUCTURA_JSON_ESPERADA = '''{
  "marca": "string  // ej: Volkswagen, BYD, Geely",
  "modelo": "string  // ej: ID.3, Atto 3 (sin la marca)",
  "anio": "string  // ej: 2025",
  "version": "string  // versión/trim, ej: Smart Excellent Edition",
  "datos_clave": [
    ["ELÉCTRICO", "MOTOR"],
    ["451 KM", "AUTONOMÍA"],
    ["AUTOMÁTICA", "TRANSMISIÓN"],
    ["170 HP", "POTENCIA"]
  ],
  "tren_motriz": ["item1", "item2", "..."],
  "bateria_carga": ["item1", "item2", "..."],
  "exterior": ["item1", "item2", "..."],
  "interior": ["item1", "item2", "..."],
  "seguridad": ["item1", "item2", "..."],
  "asistencias_adas": ["item1", "item2", "..."],
  "tecnologia_conectividad": ["item1", "item2", "..."],
  "dimensiones_capacidades": ["item1", "item2", "..."]
}'''


PROMPT_BASE = """Eres un experto en automoción y traducción técnica español-inglés. Vas a procesar la ficha técnica oficial (en inglés) de un vehículo eléctrico para un concesionario boliviano (Merch and Go, MGO) en La Paz. Tu trabajo es extraer la información en formato JSON estructurado en español, listo para ir a un PDF comercial.

## REGLAS FUNDAMENTALES (críticas - leer dos veces)

1. **PROHIBIDO INVENTAR.** Si un dato no aparece literalmente en el texto fuente, NO lo incluyas. No infieras "probablemente tiene tal característica porque otros modelos similares lo tienen". Solo lo que está explícitamente escrito.

2. **Traducción inteligente, NO literal.** El PDF fuente suele venir de un fabricante chino con traducción tosca al inglés. Tu trabajo es:
   - Normalizar nombres: "Ningde era" → "CATL (Ningde)", "Volkswagens" → "Volkswagen"
   - Usar terminología automotriz estándar en español rioplatense/latinoamericano neutro
   - Convertir formatos: "5-door 5 seat hatchback" → "Hatchback 5 puertas, 5 plazas"
   - "Permanent magnet/synchronous" → "Motor síncrono de imán permanente"
   - "Lithium iron phosphate" → "Litio Ferrofosfato (LFP)"

3. **Items concisos.** Cada ítem debe ser una línea corta (idealmente 30-55 caracteres). Tienen que entrar en 2 columnas de un PDF A4. Si un dato es muy largo, condénsalo (ej: "Pure electric cruising range CLTC 451 km" → "Autonomía CLTC: 451 km").

4. **Cantidad de items por sección.** Apunta a estos rangos (no son rígidos, pero úsalos de referencia):
   - tren_motriz: 8-12 items
   - bateria_carga: 8-12 items
   - exterior: 14-20 items
   - interior: 14-20 items
   - seguridad: 14-20 items
   - asistencias_adas: 10-18 items
   - tecnologia_conectividad: 14-24 items
   - dimensiones_capacidades: 14-20 items
   Si la ficha original tiene MENOS información, NO inventes para llenar. Mejor menos items reales que más items falsos.

5. **Símbolos ▲/△ del texto fuente.** En muchas fichas chinas:
   - ▲ = característica de serie (incluir)
   - △ = opcional (incluir solo si la versión específica la trae; si dice "opcional" general, omitir)
   - "-" o "None" = NO incluir
   Si tienes duda, **es mejor omitir** que incluir información incorrecta.

## DATOS CLAVE (página 1, los 4 destacados)

El campo `datos_clave` son 4 pares [VALOR, LABEL] para la página hero. Siempre exactamente estos 4 LABELS en este orden:

1. ["TIPO DE MOTOR (1-2 palabras)", "MOTOR"] → típicamente "ELÉCTRICO" para puros, "HÍBRIDO" si aplica
2. ["AUTONOMÍA en km", "AUTONOMÍA"] → ej: "451 KM" (usar CLTC si está disponible, sino WLTP)
3. ["TIPO DE TRANSMISIÓN (1 palabra)", "TRANSMISIÓN"] → ej: "AUTOMÁTICA"
4. ["POTENCIA en hp", "POTENCIA"] → ej: "170 HP"

Los valores en MAYÚSCULAS y muy cortos (max ~9 caracteres).

## DISTRIBUCIÓN DE CONTENIDO POR SECCIÓN

- **tren_motriz**: tipo de motor, potencia, torque, tracción, transmisión, modos de conducción, velocidad máx, aceleración
- **bateria_carga**: tipo y química de batería, marca, capacidad kWh, autonomía CLTC/WLTP/NEDC, consumo, tiempos de carga AC y DC, puerto, refrigeración
- **exterior**: tipo de carrocería, dimensiones GENERALES en una línea, peso, maletero, faros, llantas, espejos, limpiaparabrisas, techo
- **interior**: capacidad pasajeros, tapicería, volante, tablero, pantalla, climatización, asientos, audio
- **seguridad**: airbags, frenos (ABS, EBD, etc.), control de estabilidad, anclajes, freno de mano
- **asistencias_adas**: nivel L2/L3 si aplica, LDW, LKA, AEB, ACC, cámaras, sensores, radar
- **tecnologia_conectividad**: pantallas (repetidas OK), CarPlay/Android Auto, Bluetooth, WiFi, OTA, app móvil, voz, USBs, llave
- **dimensiones_capacidades**: largo, ancho, alto, distancia entre ejes, peso, maletero (en detalle), batería kWh, suspensión, dirección

## FORMATO DE SALIDA

Devuelve EXCLUSIVAMENTE un bloque JSON válido entre tres backticks, sin explicaciones antes ni después. Esquema exacto:

```json
{ESTRUCTURA_JSON}
```

## TEXTO FUENTE A PROCESAR

```
{TEXTO_PDF}
```

Procesa ahora. Devuelve sólo el JSON.
"""


def construir_prompt(texto_pdf):
    """Construye el prompt completo para Claude.ai.

    Args:
        texto_pdf: texto extraído del PDF en inglés

    Returns:
        str: prompt listo para copiar a claude.ai
    """
    return PROMPT_BASE.replace("{ESTRUCTURA_JSON}", ESTRUCTURA_JSON_ESPERADA) \
                      .replace("{TEXTO_PDF}", texto_pdf)


def validar_json_respuesta(json_str):
    """Valida que el JSON recibido tenga la estructura correcta.

    Args:
        json_str: el JSON crudo que el usuario pegó (puede tener ```json
                  envolturas, comentarios, etc.)

    Returns:
        tuple: (datos_dict, errores_list)
               - datos_dict: el dict ya normalizado, listo para
                 ficha_renderer.generar_ficha (None si hay errores fatales)
               - errores_list: lista de strings con problemas detectados
    """
    import json
    import re

    errores = []

    # 1) Limpiar envolturas tipo ```json ... ```
    texto = json_str.strip()
    # Quitar bloque markdown si existe
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texto, flags=re.DOTALL)
    if m:
        texto = m.group(1)

    # 2) Parsear
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as e:
        errores.append(f"JSON inválido: {e}. Verifica que copiaste el bloque completo.")
        return None, errores

    # 3) Validar claves obligatorias
    obligatorias_simples = ["marca", "modelo", "anio", "version"]
    obligatorias_listas = [
        "tren_motriz", "bateria_carga", "exterior", "interior",
        "seguridad", "asistencias_adas", "tecnologia_conectividad",
        "dimensiones_capacidades",
    ]

    for k in obligatorias_simples:
        if k not in datos:
            errores.append(f"Falta el campo '{k}'")
        elif not isinstance(datos[k], str):
            errores.append(f"'{k}' debe ser texto (string)")
            datos[k] = str(datos[k])

    for k in obligatorias_listas:
        if k not in datos:
            errores.append(f"Falta la sección '{k}'")
            datos[k] = []
        elif not isinstance(datos[k], list):
            errores.append(f"'{k}' debe ser una lista de items")
            datos[k] = []
        else:
            # Convertir cualquier elemento no-str a str
            datos[k] = [str(item) for item in datos[k]]

    # 4) Validar datos_clave (4 pares)
    if "datos_clave" not in datos:
        errores.append("Falta 'datos_clave'")
        datos["datos_clave"] = [
            ("ELÉCTRICO", "MOTOR"), ("- KM", "AUTONOMÍA"),
            ("AUTOMÁTICA", "TRANSMISIÓN"), ("- HP", "POTENCIA"),
        ]
    else:
        dc = datos["datos_clave"]
        if not isinstance(dc, list) or len(dc) != 4:
            errores.append("'datos_clave' debe ser una lista de 4 pares")
        else:
            # Cada par debe tener 2 elementos
            normalizado = []
            for i, par in enumerate(dc):
                if isinstance(par, (list, tuple)) and len(par) == 2:
                    normalizado.append((str(par[0]), str(par[1])))
                else:
                    errores.append(f"datos_clave[{i}] debe ser [VALOR, LABEL]")
                    normalizado.append(("--", "--"))
            datos["datos_clave"] = normalizado

    # 5) Asegurar campos fijos MGO (siempre presentes)
    datos.setdefault("precio", "Consultar")
    datos.setdefault("moneda", "USD")
    datos.setdefault("whatsapp", "73017677")
    datos.setdefault("ciudad", "La Paz, Bolivia")

    return datos, errores
