"""
Dimensión relacional y multivariada - Integrante 4.

Pregunta de análisis:
    ¿Qué diferencias o relaciones evidentes pueden identificarse al analizar
    conjuntamente tres o más variables?

Eje del tablero: aseguramiento, edad de la madre, controles prenatales,
tipo de parto y condiciones del recién nacido (peso y semanas de gestación).
Todo se calcula con pandas a partir de data/nacimientos.csv (cargar_datos())
y se envía a templates/dimensiones/multivariada.html
"""

import pandas as pd
from flask import Blueprint, render_template, request

from utils.datos import VARIABLES, cargar_datos, opciones

bp = Blueprint("multivariada", __name__)

# Variables que usa este tablero (se describen en "Variables utilizadas")
COLUMNAS_USADAS = [
    "anio", "institucion", "area_residencia", "regimen_seguridad",
    "curso_vida_madre", "consultas_prenatales", "tipo_parto",
    "peso_gramos", "semanas_gestacion",
]

CURSOS = ["ADOLESCENCIA", "JUVENTUD", "ADULTEZ"]
NOMBRE_CURSO = {"ADOLESCENCIA": "Adolescencia", "JUVENTUD": "Juventud", "ADULTEZ": "Adultez"}

# Grupos de régimen: contributivo y especial son muy pocos, se agrupan.
GRUPOS_REGIMEN = ["SUBSIDIADO", "NO ASEGURADO", "CONTRIBUTIVO / ESPECIAL"]
NOMBRE_REGIMEN = {
    "SUBSIDIADO": "Subsidiado",
    "NO ASEGURADO": "No asegurado",
    "CONTRIBUTIVO / ESPECIAL": "Contributivo / especial",
}

# Grupos de controles prenatales para la tercera gráfica
GRUPOS_CONTROLES = ["Sin controles", "1 a 3", "4 a 6", "7 o más"]
LIMITES_CONTROLES = [-1, 0, 3, 6, 100]

UMBRAL_CONTROLES = 4        # referencia mínima de controles prenatales
UMBRAL_BAJO_PESO = 2500     # gramos
UMBRAL_PREMATURO = 37       # semanas


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def porcentaje(parte, total):
    return round(parte * 100 / total, 1) if total else 0.0


def miles(numero):
    return f"{numero:,}".replace(",", ".")


def coma(numero):
    return f"{numero:.1f}".replace(".", ",")


def nombre_propio(valor):
    return str(valor).title().replace(" Del ", " del ")


def leer_filtros(df):
    """Lee los dos filtros de la URL (?institucion=...&area=...). Valores inválidos se ignoran."""
    institucion = request.args.get("institucion", "")
    area = request.args.get("area", "")
    if institucion not in opciones(df, "institucion"):
        institucion = ""
    if area not in opciones(df, "area_residencia"):
        area = ""
    return institucion, area


def aplicar_filtros(df, institucion, area):
    if institucion:
        df = df[df["institucion"] == institucion]
    if area:
        df = df[df["area_residencia"] == area]
    return df


def preparar(df):
    """Agrega las columnas derivadas que usan los indicadores y las gráficas."""
    df = df.copy()
    df["grupo_regimen"] = df["regimen_seguridad"].where(
        df["regimen_seguridad"].isin(["SUBSIDIADO", "NO ASEGURADO"]), "CONTRIBUTIVO / ESPECIAL")
    df["asegurada"] = df["regimen_seguridad"] != "NO ASEGURADO"
    df["cesarea"] = df["tipo_parto"] == "CESÁREA"
    df["bajo_peso"] = df["peso_gramos"] < UMBRAL_BAJO_PESO
    # Semanas = 0 o vacías son datos faltantes, no embarazos de 0 semanas
    semanas = df["semanas_gestacion"].where(df["semanas_gestacion"] > 0)
    df["semanas_validas"] = semanas
    df["prematuro"] = semanas < UMBRAL_PREMATURO
    df["grupo_controles"] = pd.cut(df["consultas_prenatales"], bins=LIMITES_CONTROLES,
                                   labels=GRUPOS_CONTROLES)
    return df


# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------
def calcular_indicadores(df):
    total = len(df)
    if total == 0:
        return {"total": 0}
    aseg = df[df["asegurada"]]
    no_aseg = df[~df["asegurada"]]
    return {
        "total": total,
        "pct_cesarea": coma(porcentaje(int(df["cesarea"].sum()), total)),
        "controles_no_aseg": coma(no_aseg["consultas_prenatales"].mean()) if len(no_aseg) else "—",
        "controles_aseg": coma(aseg["consultas_prenatales"].mean()) if len(aseg) else "—",
        "pct_pocos_controles": coma(porcentaje(int((df["consultas_prenatales"] < UMBRAL_CONTROLES).sum()), total)),
        "n_pocos_controles": int((df["consultas_prenatales"] < UMBRAL_CONTROLES).sum()),
    }


# ---------------------------------------------------------------------------
# Datos de las tres visualizaciones
# ---------------------------------------------------------------------------
def grafica_controles(df):
    """
    1. Promedio de controles prenatales por régimen (eje x) y curso de vida
       (una serie por curso de vida). Variables: consultas_prenatales,
       regimen_seguridad, curso_vida_madre.
    """
    series = []
    for curso in CURSOS:
        sub = df[df["curso_vida_madre"] == curso]
        valores, n = [], []
        for grupo in GRUPOS_REGIMEN:
            s = sub[sub["grupo_regimen"] == grupo]["consultas_prenatales"]
            valores.append(round(float(s.mean()), 2) if len(s) else None)
            n.append(int(len(s)))
        series.append({"nombre": NOMBRE_CURSO[curso], "valores": valores, "n": n})
    return {"etiquetas": [NOMBRE_REGIMEN[g] for g in GRUPOS_REGIMEN], "series": series}


def grafica_cesareas(df):
    """
    2. Porcentaje de cesáreas por año (eje x) y curso de vida (una línea por
       curso de vida). Variables: tipo_parto, anio, curso_vida_madre.
    """
    anios = sorted(df["anio"].unique().tolist())
    series = []
    for curso in CURSOS:
        sub = df[df["curso_vida_madre"] == curso]
        valores, n = [], []
        for a in anios:
            s = sub[sub["anio"] == a]
            valores.append(porcentaje(int(s["cesarea"].sum()), len(s)) if len(s) else None)
            n.append(int(len(s)))
        series.append({"nombre": NOMBRE_CURSO[curso], "valores": valores, "n": n})
    return {"etiquetas": [str(a) for a in anios], "series": series}


def grafica_resultados(df):
    """
    3. Porcentaje de bajo peso (<2.500 g) y de prematuridad (<37 semanas)
       según el número de controles prenatales.
       Variables: consultas_prenatales, peso_gramos, semanas_gestacion.
    """
    bajo, prem, n = [], [], []
    for g in GRUPOS_CONTROLES:
        s = df[df["grupo_controles"] == g]
        n.append(int(len(s)))
        bajo.append(porcentaje(int(s["bajo_peso"].sum()), len(s)) if len(s) else None)
        validas = s["semanas_validas"].notna().sum()
        prem.append(porcentaje(int(s["prematuro"].sum()), int(validas)) if validas else None)
    return {"etiquetas": GRUPOS_CONTROLES, "bajo_peso": bajo, "prematuro": prem, "n": n}


# ---------------------------------------------------------------------------
# Textos del análisis. Las cifras se calculan con los datos filtrados para que
# siempre coincidan con lo que muestran las gráficas.
# ---------------------------------------------------------------------------
LIMITACION = (
    "El análisis muestra asociaciones, no causas: que las madres no aseguradas tengan menos controles "
    "o que los nacimientos sin controles tengan más bajo peso no demuestra que una variable provoque la otra. "
    "Además, la Unidad Materno Infantil Santa Teresita no registra ninguna cesárea y casi deja de reportar desde "
    "2023, por lo que la tendencia anual de cesáreas mezcla cambios reales con cambios en la composición de las "
    "instituciones (el filtro por institución permite aislar el Hospital Local del Norte). Por último, algunos "
    "grupos son pequeños (por ejemplo, madres sin controles prenatales o adolescentes con régimen contributivo) y "
    "el dato cuenta cuántos controles hubo, no su calidad ni el riesgo clínico de cada embarazo."
)


def promedio_texto(valor):
    return coma(valor) if valor is not None else "—"


def redactar(df, ind, g_controles, g_cesareas, g_resultados):
    total = len(df)
    if total == 0:
        return {}, [{}, {}, {}], "No hay registros con los filtros seleccionados."

    # ----- cifras base -----
    aseg = df[df["asegurada"]]["consultas_prenatales"]
    no_aseg = df[~df["asegurada"]]["consultas_prenatales"]
    n_no_aseg = int(len(no_aseg))
    pct_no_aseg = coma(porcentaje(n_no_aseg, total))
    dif = (aseg.mean() - no_aseg.mean()) if len(aseg) and len(no_aseg) else None

    # ¿la brecha de controles existe en cada curso de vida con datos de ambos grupos?
    brecha_cursos = []
    for c in CURSOS:
        sub = df[df["curso_vida_madre"] == c]
        a, n = sub[sub["asegurada"]]["consultas_prenatales"], sub[~sub["asegurada"]]["consultas_prenatales"]
        if len(a) and len(n):
            brecha_cursos.append(a.mean() > n.mean())
    brecha_todas = bool(brecha_cursos) and all(brecha_cursos)

    # cesáreas por curso de vida
    ces_curso = {c: porcentaje(int(df[df["curso_vida_madre"] == c]["cesarea"].sum()),
                               int((df["curso_vida_madre"] == c).sum()))
                 for c in CURSOS if (df["curso_vida_madre"] == c).any()}
    ces_alto = max(ces_curso, key=ces_curso.get) if ces_curso else None
    ces_bajo = min(ces_curso, key=ces_curso.get) if ces_curso else None

    # cesáreas primer y último año disponibles
    anios = g_cesareas["etiquetas"]
    pct_anio = {}
    for a in anios:
        s = df[df["anio"] == int(a)]
        pct_anio[a] = porcentaje(int(s["cesarea"].sum()), len(s))

    # resultados según controles
    sin_ctrl = df[df["grupo_controles"] == "Sin controles"]
    con_ctrl = df[df["grupo_controles"] != "Sin controles"]
    pct_bajo_sin = porcentaje(int(sin_ctrl["bajo_peso"].sum()), len(sin_ctrl)) if len(sin_ctrl) else None
    pct_bajo_con = porcentaje(int(con_ctrl["bajo_peso"].sum()), len(con_ctrl)) if len(con_ctrl) else None
    v_sin = sin_ctrl["semanas_validas"].notna().sum()
    v_con = con_ctrl["semanas_validas"].notna().sum()
    pct_prem_sin = porcentaje(int(sin_ctrl["prematuro"].sum()), int(v_sin)) if v_sin else None
    pct_prem_con = porcentaje(int(con_ctrl["prematuro"].sum()), int(v_con)) if v_con else None

    # ----- interpretación de cada visualización -----
    if dif is not None:
        i1 = (f"Las madres no aseguradas tienen en promedio {coma(no_aseg.mean())} controles prenatales frente a "
              f"{coma(aseg.mean())} de las aseguradas ({coma(dif)} menos). "
              + ("La brecha aparece en todas las etapas de vida con datos. " if brecha_todas else "")
              + "Las barras de contributivo/especial se basan en pocos casos (ver detalle al pasar el cursor).")
    else:
        i1 = "Con los filtros seleccionados no hay madres de ambos grupos (aseguradas y no aseguradas) para compararlos."

    if ces_alto and ces_bajo and ces_alto != ces_bajo:
        i2 = (f"La adultez es la etapa con más cesáreas ({coma(ces_curso.get('ADULTEZ', 0))} %) y la adolescencia la que menos "
              f"({coma(ces_curso.get('ADOLESCENCIA', 0))} %)" if "ADULTEZ" in ces_curso and "ADOLESCENCIA" in ces_curso
              else f"Entre los cursos de vida con datos, {NOMBRE_CURSO[ces_alto].lower()} tiene el mayor porcentaje de cesáreas y "
                   f"{NOMBRE_CURSO[ces_bajo].lower()} el menor")
        if len(anios) > 1:
            i2 += (f". En el total, el porcentaje pasó de {coma(pct_anio[anios[0]])} % en {anios[0]} a "
                   f"{coma(pct_anio[anios[-1]])} % en {anios[-1]} (el año 2026 llega solo hasta julio)"
                    + ("; parte del aumento se debe a que Santa Teresita, que no registra cesáreas, casi deja de reportar desde 2023." if not df["institucion"].nunique() == 1 else ".")) 
        else:
            i2 += "."
    else:
        i2 = "Con los filtros seleccionados no hay suficientes grupos de edad para compararlos."

    if pct_bajo_sin is not None and pct_bajo_con is not None:
        i3 = (f"Entre los nacimientos sin ningún control prenatal el {coma(pct_bajo_sin)} % tuvo bajo peso (menos de 2.500 g), "
              f"frente a {coma(pct_bajo_con)} % entre quienes tuvieron al menos un control.")
        if pct_prem_sin is not None and pct_prem_con is not None:
            i3 += f" La prematuridad sigue el mismo patrón: {coma(pct_prem_sin)} % frente a {coma(pct_prem_con)} %."
        i3 += f" El grupo sin controles es pequeño ({miles(len(sin_ctrl))} nacimientos)."
    else:
        i3 = "Con los filtros seleccionados no hay nacimientos sin controles prenatales para comparar."

    interpretaciones = {"controles": i1, "cesareas": i2, "resultados": i3}

    # ----- conocimientos evidentes (estructura de la guía) -----
    conocimientos = [
        {
            "pregunta": "¿Tienen las madres no aseguradas el mismo número de controles prenatales que las aseguradas, en todas las edades?",
            "variables": "consultas_prenatales, regimen_seguridad, curso_vida_madre",
            "procedimiento": "Se calculó el promedio de consultas_prenatales para cada combinación de régimen (subsidiado, no asegurado, contributivo/especial) y curso de vida.",
            "evidencia": f"Gráfica 1 e indicador 2: no aseguradas {promedio_texto(no_aseg.mean() if len(no_aseg) else None)} controles y aseguradas {promedio_texto(aseg.mean() if len(aseg) else None)} ({miles(n_no_aseg)} madres no aseguradas, {pct_no_aseg} %).",
            "hallazgo": (f"Las madres no aseguradas tienen {coma(dif)} controles prenatales menos que las aseguradas." if dif is not None
                         else "No hay madres de ambos grupos con los filtros seleccionados."),
            "interpretacion": ("La falta de aseguramiento se asocia con una atención prenatal más escasa en cada etapa de vida, así que la brecha no depende de la edad de la madre."
                               if brecha_todas else "La falta de aseguramiento se asocia con una atención prenatal más escasa."),
            "utilidad": "Señala a las madres no aseguradas como el grupo al que más conviene llegar antes del parto con afiliación y controles.",
            "limitacion": "El régimen corresponde al momento del parto: no se sabe si la madre estuvo asegurada durante la gestación ni por qué faltó a sus controles.",
        },
        {
            "pregunta": "¿Cambia el porcentaje de cesáreas según la etapa de vida de la madre y a lo largo de los años?",
            "variables": "tipo_parto, curso_vida_madre, anio",
            "procedimiento": "Se calculó, para cada año y curso de vida, el porcentaje de nacimientos con tipo_parto = cesárea.",
            "evidencia": (f"Gráfica 2: adolescencia {coma(ces_curso.get('ADOLESCENCIA', 0))} %, juventud {coma(ces_curso.get('JUVENTUD', 0))} %, "
                          f"adultez {coma(ces_curso.get('ADULTEZ', 0))} %; total {coma(pct_anio[anios[0]])} % en {anios[0]} y {coma(pct_anio[anios[-1]])} % en {anios[-1]}."),
            "hallazgo": ("El porcentaje de cesáreas es mayor en la adultez que en la adolescencia." if ces_alto == "ADULTEZ" and ces_bajo == "ADOLESCENCIA"
                         else "Con los filtros seleccionados no se observa una diferencia clara de cesáreas entre etapas de vida."),
            "interpretacion": ("A mayor edad de la madre, más partos terminan en cesárea; en el Hospital Local del Norte la diferencia es de 33 %, 41 % y 47 % entre adolescencia, juventud y adultez."
                               if ces_alto == "ADULTEZ" and ces_bajo == "ADOLESCENCIA" else "No hay suficientes datos para comparar etapas de vida."),
            "utilidad": "Ayuda a anticipar la demanda de quirófano y de cuidado posoperatorio según el perfil de edad de las gestantes.",
            "limitacion": "Santa Teresita no registra cesáreas y su peso en los datos cae con los años, así que la tendencia anual total no se debe leer como un cambio de práctica sin filtrar por institución.",
        },
        {
            "pregunta": "¿Se asocian los controles prenatales con el peso y la duración del embarazo del recién nacido?",
            "variables": "consultas_prenatales, peso_gramos, semanas_gestacion",
            "procedimiento": "Se agruparon los nacimientos por número de controles (0, 1-3, 4-6, 7 o más) y se calculó el % con peso menor de 2.500 g y el % con menos de 37 semanas.",
            "evidencia": (f"Gráfica 3: bajo peso {promedio_texto(pct_bajo_sin)} % sin controles y {promedio_texto(pct_bajo_con)} % con controles; "
                          f"prematuridad {promedio_texto(pct_prem_sin)} % y {promedio_texto(pct_prem_con)} %."),
            "hallazgo": "Los nacimientos sin ningún control prenatal presentan más bajo peso y más prematuridad que los que tuvieron controles.",
            "interpretacion": "Haber tenido al menos un control prenatal va de la mano con mejores condiciones al nacer; después del primer control la diferencia entre grupos es pequeña.",
            "utilidad": "Respalda que el esfuerzo debe centrarse en que ninguna gestante llegue al parto sin haber sido atendida al menos una vez.",
            "limitacion": "El grupo sin controles es pequeño y no se controla por otros factores (por ejemplo, embarazos de alto riesgo que se atienden distinto).",
        },
    ]

    # ----- decisión sustentada en los datos -----
    decision = (
        f"El {pct_no_aseg} % de los nacimientos ({miles(n_no_aseg)} de {miles(total)}) corresponde a madres no aseguradas, que "
        f"tienen {promedio_texto(no_aseg.mean() if len(no_aseg) else None)} controles prenatales en promedio frente a "
        f"{promedio_texto(aseg.mean() if len(aseg) else None)} de las aseguradas, y el {ind['pct_pocos_controles']} % del total tuvo menos de "
        f"{UMBRAL_CONTROLES} controles. Con estas cifras, la Secretaría de Salud podría crear una ruta de captación temprana en el "
        "Hospital Local del Norte (afiliación inmediata y agendamiento de controles desde el primer contacto con una gestante no asegurada), "
        "con la meta de que ninguna madre llegue al parto sin controles, y medir cada año el promedio de controles y el porcentaje de "
        "madres con menos de 4 controles."
    )
    return interpretaciones, conocimientos, decision


# ---------------------------------------------------------------------------
# Ruta
# ---------------------------------------------------------------------------
@bp.route("/dimension/multivariada")
def index():
    completo = cargar_datos()
    institucion, area = leer_filtros(completo)
    df = preparar(aplicar_filtros(completo, institucion, area))

    contexto = {
        "titulo": "Dimensión relacional y multivariada",
        "pregunta": "¿Qué diferencias o relaciones evidentes pueden identificarse al analizar conjuntamente tres o más variables?",
        "total_registros": len(df),
        # Variables utilizadas
        "variables": [v for v in VARIABLES if v["columna"] in COLUMNAS_USADAS],
        # Filtros interactivos
        "institucion_sel": institucion,
        "area_sel": area,
        "instituciones": opciones(completo, "institucion"),
        "areas": opciones(completo, "area_residencia"),
    }

    if len(df) == 0:
        contexto.update({
            "indicadores": {"total": 0}, "g_controles": None, "g_cesareas": None, "g_resultados": None,
            "interpretaciones": {}, "conocimientos": [{}, {}, {}],
            "limitacion": LIMITACION, "decision": "No hay registros con los filtros seleccionados.",
        })
        return render_template("dimensiones/multivariada.html", **contexto)

    indicadores = calcular_indicadores(df)
    g_controles = grafica_controles(df)
    g_cesareas = grafica_cesareas(df)
    g_resultados = grafica_resultados(df)
    interpretaciones, conocimientos, decision = redactar(df, indicadores, g_controles, g_cesareas, g_resultados)

    contexto.update({
        "indicadores": indicadores,
        "g_controles": g_controles,
        "g_cesareas": g_cesareas,
        "g_resultados": g_resultados,
        "interpretaciones": interpretaciones,
        "conocimientos": conocimientos,
        "limitacion": LIMITACION,
        "decision": decision,
    })
    return render_template("dimensiones/multivariada.html", **contexto)
