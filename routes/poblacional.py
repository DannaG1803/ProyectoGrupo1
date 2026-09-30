"""
Dimensión poblacional : Integrante 1.

Pregunta de análisis:
    ¿Cómo está compuesta y distribuida la población analizada según sus
    principales características?

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Todo se calcula con pandas a partir de data/nacimientos.csv (cargar_datos())
y se envía a templates/dimensiones/poblacional.html
"""

import pandas as pd
from flask import Blueprint, render_template, request

from utils.datos import VARIABLES, cargar_datos, opciones

bp = Blueprint("poblacional", __name__)

# Variables que usa este tablero (se describen en la sección "Variables utilizadas")
COLUMNAS_USADAS = [
    "anio", "institucion", "regimen_seguridad", "nivel_educativo_madre",
    "edad_madre", "curso_vida_madre", "sexo", "tipo_parto",
    "estado_conyugal_madre", "tipo_documento_madre",
]

# Variables categóricas que se resumen en la tabla de perfil general
PERFIL = [
    ("sexo", "Sexo del recién nacido"),
    ("tipo_parto", "Tipo de parto"),
    ("curso_vida_madre", "Curso de vida de la madre"),
    ("estado_conyugal_madre", "Estado conyugal de la madre"),
    ("tipo_documento_madre", "Documento de la madre"),
    ("institucion", "Institución"),
]

SIN_INFORMACION = "SIN INFORMACIÓN"

# Rangos de edad de 5 años para el histograma (10-14, 15-19 ... 50-54)
LIMITES_EDAD = list(range(10, 60, 5))
ETIQUETAS_EDAD = [f"{i}-{i + 4}" for i in LIMITES_EDAD[:-1]]


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def texto(valor):
    """'UNIÓN LIBRE (2 AÑOS O MÁS)' -> 'Unión libre (2 años o más)'."""
    return str(valor).capitalize()


def nombre_propio(valor):
    """'HOSPITAL LOCAL DEL NORTE' -> 'Hospital Local del Norte'."""
    return str(valor).title().replace(" Del ", " del ")


def porcentaje(parte, total):
    return round(parte * 100 / total, 1) if total else 0.0


def miles(numero):
    """7016 -> '7.016' (punto como separador de miles)."""
    return f"{numero:,}".replace(",", ".")


def coma(numero):
    """24.6 -> '24,6' (coma decimal como se usa en Colombia)."""
    return f"{numero:.1f}".replace(".", ",")


def leer_filtros(df):
    """
    Lee los dos filtros interactivos de la URL (?anio=2024&institucion=...).
    Si el valor no existe en los datos se ignora.
    """
    anio = request.args.get("anio", "")
    institucion = request.args.get("institucion", "")

    if not anio.isdigit() or int(anio) not in opciones(df, "anio"):
        anio = ""
    if institucion not in opciones(df, "institucion"):
        institucion = ""
    return anio, institucion


def aplicar_filtros(df, anio, institucion):
    if anio:
        df = df[df["anio"] == int(anio)]
    if institucion:
        df = df[df["institucion"] == institucion]
    return df


def distribucion(serie):
    """Conteo y porcentaje de cada categoría, de mayor a menor."""
    conteo = serie.value_counts()
    total = int(conteo.sum())
    return {
        "etiquetas": [texto(c) for c in conteo.index],
        "valores": [int(v) for v in conteo],
        "porcentajes": [porcentaje(int(v), total) for v in conteo],
    }


def histograma_edad(df):
    """Nacimientos por rango de edad de la madre (cada 5 años)."""
    rangos = pd.cut(df["edad_madre"].astype(float), bins=LIMITES_EDAD,
                    right=False, labels=ETIQUETAS_EDAD)
    conteo = rangos.value_counts(sort=False)
    total = int(conteo.sum())
    return {
        "etiquetas": ETIQUETAS_EDAD,
        "valores": [int(v) for v in conteo],
        "porcentajes": [porcentaje(int(v), total) for v in conteo],
    }


def calcular_indicadores(df):
    """Los tres indicadores del tablero."""
    total = len(df)
    if total == 0:
        return {"total": 0, "edad_media": "—", "pct_subsidiado": "—"}
    subsidiado = int((df["regimen_seguridad"] == "SUBSIDIADO").sum())
    return {
        "total": total,
        "edad_media": coma(df["edad_madre"].mean()),
        "pct_subsidiado": coma(porcentaje(subsidiado, total)),
    }


def calcular_perfil(df):
    """
    Para cada variable del perfil: categoría predominante y minoritaria con su
    porcentaje sobre el total de registros (se omite 'SIN INFORMACIÓN').
    """
    total = len(df)
    filas = []
    for columna, nombre in PERFIL:
        conteo = df[columna].value_counts()
        conteo = conteo[conteo.index != SIN_INFORMACION]
        formato = nombre_propio if columna == "institucion" else texto
        if conteo.empty:
            continue
        filas.append({
            "variable": nombre,
            "categorias": len(conteo),
            "predominante": formato(conteo.index[0]),
            "pct_predominante": coma(porcentaje(int(conteo.iloc[0]), total)),
            "minoritaria": formato(conteo.index[-1]) if len(conteo) > 1 else "—",
            "pct_minoritaria": coma(porcentaje(int(conteo.iloc[-1]), total)) if len(conteo) > 1 else "—",
        })
    return filas


# ---------------------------------------------------------------------------
# Textos del análisis (interpretaciones, conocimientos, limitación y decisión)
# Las cifras se calculan con los datos filtrados, así el texto siempre coincide
# con lo que muestran las gráficas.
# ---------------------------------------------------------------------------
EDUCACION_SUPERIOR = ["TÉCNICA PROFESIONAL", "TECNOLÓGICA", "PROFESIONAL", "ESPECIALIZACIÓN"]

LIMITACION = (
    "Los datos describen solo los nacimientos registrados en dos instituciones públicas "
    "(Hospital Local del Norte y Unidad Materno Infantil Santa Teresita), no toda la natalidad "
    "de Bucaramanga. El Hospital Local del Norte concentra el 88 % de los registros, la Santa "
    "Teresita casi deja de reportar desde 2023 (no tiene registros en 2026) y 2026 llega solo "
    "hasta el 31 de julio; por eso la disminución de registros por año no debe leerse como una "
    "baja de la natalidad. Además, el análisis describe cómo está compuesta la población, no "
    "explica las causas de esa composición."
)


def redactar(df, regimen, educacion, edad):
    """
    Devuelve las interpretaciones de las tres gráficas, los tres conocimientos
    evidentes y la decisión sustentada, calculados con los datos filtrados.
    """
    total = len(df)
    if total == 0:
        return {}, [{}, {}, {}], "No hay registros con los filtros seleccionados."

    # ----- cifras base -----
    r_top, r_top_pct = regimen["etiquetas"][0], coma(regimen["porcentajes"][0])
    r_seg, r_seg_pct = regimen["etiquetas"][1], coma(regimen["porcentajes"][1])
    suma_regimen = regimen["porcentajes"][0] + regimen["porcentajes"][1]
    no_aseg = int((df["regimen_seguridad"] == "NO ASEGURADO").sum())
    pct_no_aseg = coma(porcentaje(no_aseg, total))

    e_top, e_top_pct = educacion["etiquetas"][0], coma(educacion["porcentajes"][0])
    superior = int(df["nivel_educativo_madre"].isin(EDUCACION_SUPERIOR).sum())
    pct_superior = coma(porcentaje(superior, total))

    mediana = int(df["edad_madre"].median())
    i_modal = edad["valores"].index(max(edad["valores"]))
    rango_modal, pct_modal = edad["etiquetas"][i_modal], coma(edad["porcentajes"][i_modal])
    pct_menor_30 = coma(porcentaje(int((df["edad_madre"] < 30).sum()), total))
    pct_35 = coma(porcentaje(int((df["edad_madre"] >= 35).sum()), total))
    adolescentes = int((df["curso_vida_madre"] == "ADOLESCENCIA").sum())
    pct_adolescentes = coma(porcentaje(adolescentes, total))

    # ----- interpretación de cada visualización -----
    interpretaciones = {
        "regimen": (
            f"El régimen «{r_top}» es el grupo predominante ({r_top_pct} %) y «{r_seg}» es el segundo "
            f"({r_seg_pct} %); entre los dos suman {coma(suma_regimen)} %. Los demás regímenes son grupos minoritarios."
        ),
        "educacion": (
            f"«{e_top}» es el nivel más frecuente ({e_top_pct} %). Los niveles de formación superior "
            f"(técnica profesional, tecnológica y universitaria) suman {pct_superior} %; el resto de las "
            "madres tiene estudios escolares, ninguno o no reportó información."
        ),
        "edad": (
            f"El rango de edad más frecuente es {rango_modal} años ({pct_modal} %) y la mediana es de "
            f"{mediana} años. El {pct_menor_30} % de las madres tiene menos de 30 años y solo el "
            f"{pct_35} % tiene 35 años o más."
        ),
    }

    # ----- conocimientos evidentes (estructura de la guía) -----
    conocimientos = [
        {
            "pregunta": "¿Qué régimen de salud predomina entre las madres y qué parte de ellas no tiene cobertura?",
            "variables": "regimen_seguridad",
            "procedimiento": "Se contaron los nacimientos por categoría de régimen y se dividió cada conteo entre el total de registros filtrados.",
            "evidencia": f"Gráfica 1 e indicador 3: {r_top} {r_top_pct} %, {r_seg} {r_seg_pct} % ({miles(no_aseg)} nacimientos sin aseguramiento).",
            "hallazgo": f"«{r_top}» predomina con {r_top_pct} % y «{r_seg}» es el segundo grupo con {r_seg_pct} %.",
            "interpretacion": f"«{r_top}» es el grupo más numeroso entre las madres atendidas, y el {pct_no_aseg} % llega al parto sin aseguramiento.",
            "utilidad": "Permite dimensionar la demanda de servicios financiados con recursos públicos y priorizar la afiliación de las madres no aseguradas.",
            "limitacion": "El régimen corresponde al momento del parto; no indica si la madre estuvo afiliada durante la gestación ni cómo fue su atención.",
        },
        {
            "pregunta": "¿En qué edades se concentran las madres y qué peso tiene la adolescencia?",
            "variables": "edad_madre, curso_vida_madre",
            "procedimiento": "Se agrupó edad_madre en rangos de 5 años, se calculó la mediana y el porcentaje de registros en el curso de vida «adolescencia».",
            "evidencia": f"Gráfica 3 y tabla de perfil: rango más frecuente {rango_modal} años ({pct_modal} %), mediana {mediana} años, adolescentes {pct_adolescentes} %.",
            "hallazgo": f"La mitad de las madres tiene {mediana} años o menos y el {pct_adolescentes} % son adolescentes (menores de 18 años).",
            "interpretacion": f"La maternidad en esta población ocurre a edades jóvenes: el {pct_menor_30} % tiene menos de 30 años.",
            "utilidad": "Orienta los programas de planificación familiar y educación sexual hacia los rangos donde se concentran los nacimientos, con atención especial a las adolescentes.",
            "limitacion": "Es la edad al momento del parto; sin la población femenina de cada edad no se puede calcular la tasa de fecundidad ni comparar riesgos entre edades.",
        },
        {
            "pregunta": "¿Qué nivel educativo tienen las madres?",
            "variables": "nivel_educativo_madre",
            "procedimiento": "Se contaron los nacimientos por nivel educativo y se sumaron las categorías de formación superior (técnica profesional, tecnológica, profesional y especialización).",
            "evidencia": f"Gráfica 2: {e_top} {e_top_pct} %; formación superior {pct_superior} %.",
            "hallazgo": f"«{e_top}» es el nivel más común ({e_top_pct} %) y solo el {pct_superior} % de las madres alcanzó formación superior.",
            "interpretacion": f"La formación superior es un grupo minoritario ({pct_superior} %); el perfil educativo de la población se concentra en los niveles escolares.",
            "utilidad": "Ayuda a adaptar la educación prenatal y las campañas de salud a un público con formación escolar, con mensajes claros y canales accesibles.",
            "limitacion": "El nivel educativo no mide ingresos ni condiciones socioeconómicas, y no puede concluirse que explique por sí solo el régimen de salud ni la edad de la maternidad.",
        },
    ]

    # ----- decisión sustentada en los datos -----
    decision = (
        f"El {pct_no_aseg} % de los nacimientos ({miles(no_aseg)} de {miles(total)}) corresponde a madres sin aseguramiento "
        f"y el {pct_adolescentes} % a madres adolescentes. Con estas cifras, la Secretaría de Salud podría habilitar un "
        "punto de afiliación y asesoría en planificación familiar durante la atención prenatal y el parto en la red "
        "pública (con prioridad en el Hospital Local del Norte, que concentra el 88 % de los registros) y medir cada "
        "año si baja el porcentaje de madres no aseguradas."
    )
    return interpretaciones, conocimientos, decision


# ---------------------------------------------------------------------------
# Ruta
# ---------------------------------------------------------------------------
@bp.route("/dimension/poblacional")
def index():
    completo = cargar_datos()
    anio, institucion = leer_filtros(completo)
    df = aplicar_filtros(completo, anio, institucion)

    g_regimen = distribucion(df["regimen_seguridad"])
    g_educacion = distribucion(df["nivel_educativo_madre"])
    g_edad = histograma_edad(df)
    interpretaciones, conocimientos, decision = redactar(df, g_regimen, g_educacion, g_edad)

    contexto = {
        "titulo": "Dimensión poblacional",
        "pregunta": "¿Cómo está compuesta y distribuida la población analizada según sus principales características?",
        "total_registros": len(df),
        # Descripción de las variables utilizadas
        "variables": [v for v in VARIABLES if v["columna"] in COLUMNAS_USADAS],
        # Filtros interactivos
        "anio_sel": anio,
        "institucion_sel": institucion,
        "anios": opciones(completo, "anio"),
        "instituciones": opciones(completo, "institucion"),
        # Indicadores
        "indicadores": calcular_indicadores(df),
        # Datos de las tres visualizaciones
        "g_regimen": g_regimen,
        "g_educacion": g_educacion,
        "g_edad": g_edad,
        "interpretaciones": interpretaciones,
        # Características generales de la población
        "perfil": calcular_perfil(df),
        # Conocimientos evidentes, limitación y decisión
        "conocimientos": conocimientos,
        "limitacion": LIMITACION,
        "decision": decision,
    }
    return render_template("dimensiones/poblacional.html", **contexto)
