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
    "El análisis es descriptivo: muestra asociaciones entre variables, no causas. Que las madres no aseguradas tengan "
    "menos controles, o que los nacimientos sin controles tengan más bajo peso, no demuestra que una variable provoque la otra, "
    "porque no se controlan otros factores como el riesgo clínico del embarazo. A esto se suma que algunos grupos son pequeños "
    "y que hay registros con valores imposibles (por ejemplo, edades del padre de -4 o 99 años) y una institución, Santa Teresita, "
    "que no registra cesáreas y casi deja de reportar desde 2023, lo que distorsiona las tendencias anuales si no se filtra por institución."
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
            "procedimiento": "Se calculó el promedio de consultas_prenatales para cada combinación de régimen (subsidiado, no asegurado, contributivo/especial) y curso de vida. Corresponde a los puntos 2 y 3 (diferencias entre grupos y cruce de variables).",
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
            "procedimiento": "Se calculó, para cada año y curso de vida, el porcentaje de nacimientos con tipo_parto = cesárea. Corresponde a los puntos 3 y 5 (cruce de variables y comportamiento por periodo).",
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
            "procedimiento": "Se agruparon los nacimientos por número de controles (0, 1-3, 4-6, 7 o más) y se calculó el % con peso menor de 2.500 g y el % con menos de 37 semanas. Corresponde al punto 1 (relaciones entre variables).",
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
# Análisis relacional complementario
# Seis secciones que responden a lo que debe analizar la dimensión:
#   1. Relaciones entre variables          4. Combinaciones con más registros
#   2. Diferencias entre grupos            5. Comportamientos por territorio y periodo
#   3. Cruce de tres o más variables       6. Posibles casos inusuales
# Cada sección es un diccionario con tablas calculadas con los datos filtrados.
# ---------------------------------------------------------------------------
N_MINIMO = 30            # grupos con menos nacimientos se muestran atenuados y no se interpretan
UMBRAL_PP = 5.0          # diferencia (puntos porcentuales) para resaltar un valor frente al total
UMBRAL_CONTROLES_DIF = 0.5

VARIABLES_CORRELACION = [
    ("edad_madre", "Edad de la madre"),
    ("edad_padre", "Edad del padre"),
    ("numero_embarazos", "N.º de embarazos"),
    ("consultas_prenatales", "Controles prenatales"),
    ("semanas_validas", "Semanas de gestación"),
    ("peso_gramos", "Peso al nacer"),
]


def coma2(numero):
    return f"{numero:.2f}".replace(".", ",")


def celda(texto, clase="text-end", estilo="", badge=""):
    return {"t": texto, "c": clase, "s": estilo, "b": badge}


def fila(celdas, tenue=False, fuerte=False):
    return {"celdas": celdas, "tenue": tenue, "fuerte": fuerte}


def nombre_area(valor):
    return str(valor).split(" (")[0].capitalize()


def resumen_grupo(sub):
    """Métricas comunes para describir un grupo de nacimientos."""
    n = len(sub)
    if n == 0:
        return None
    return {
        "n": n,
        "edad": float(sub["edad_madre"].mean()),
        "controles": float(sub["consultas_prenatales"].mean()),
        "peso": float(sub["peso_gramos"].mean()),
        "pct_bajo": porcentaje(int(sub["bajo_peso"].sum()), n),
        "pct_ces": porcentaje(int(sub["cesarea"].sum()), n),
        "pct_pocos": porcentaje(int((sub["consultas_prenatales"] < UMBRAL_CONTROLES).sum()), n),
        "pct_no_aseg": porcentaje(int((~sub["asegurada"]).sum()), n),
    }


def etiqueta_fuerza(r):
    r = abs(r)
    if r < 0.2:
        return "muy débil"
    if r < 0.4:
        return "débil"
    if r < 0.6:
        return "moderada"
    return "fuerte"


# ----- 1. Relaciones entre variables -----------------------------------------
def seccion_relaciones(df):
    d = df.copy()
    # Edades del padre imposibles (negativas, 99...) se tratan como dato faltante
    d["edad_padre"] = d["edad_padre"].where(d["edad_padre"].between(15, 80))
    columnas = [c for c, _ in VARIABLES_CORRELACION]
    etiquetas = [e for _, e in VARIABLES_CORRELACION]
    corr = d[columnas].corr() if len(d) > 2 else pd.DataFrame(index=columnas, columns=columnas, dtype=float)

    filas, pares = [], []
    for i, ci in enumerate(columnas):
        celdas = [celda(etiquetas[i], "fw-semibold")]
        for j, cj in enumerate(columnas):
            r = corr.loc[ci, cj]
            if pd.isna(r):
                celdas.append(celda("—", "text-center text-muted"))
            elif i == j:
                celdas.append(celda("1,00", "text-center text-muted"))
            else:
                color = "15,110,122" if r >= 0 else "224,122,95"
                estilo = f"background: rgba({color},{min(abs(r), 1) * 0.85:.2f});"
                if abs(r) >= 0.45:
                    estilo += " color: #fff;"
                celdas.append(celda(coma2(r), "text-center", estilo))
                if j > i:
                    pares.append((abs(r), r, etiquetas[i], etiquetas[j]))
        filas.append(fila(celdas))

    pares.sort(reverse=True)
    if pares:
        fuertes = "; ".join(f"{a} y {b} (r = {coma2(r)}, {etiqueta_fuerza(r)})" for _, r, a, b in pares[:3])
        lectura = f"Las relaciones más marcadas son: {fuertes}. "
        r_cp = corr.loc["consultas_prenatales", "peso_gramos"]
        r_sp = corr.loc["semanas_validas", "peso_gramos"]
        if not pd.isna(r_cp) and not pd.isna(r_sp):
            lectura += (f"El peso se relaciona más con las semanas de gestación (r = {coma2(r_sp)}) que con los controles "
                        f"prenatales (r = {coma2(r_cp)}). ")
        lectura += ("Los valores cercanos a 0 indican poca relación lineal; una correlación no demuestra que una variable cause la otra. "
                    "La edad del padre se calcula solo con valores entre 15 y 80 años.")
    else:
        lectura = "No hay suficientes datos con los filtros seleccionados."

    return {
        "numero": 1, "icono": "bi-diagram-2", "titulo": "Relaciones entre variables",
        "que_analiza": "Correlación de Pearson (r) entre las variables numéricas: va de -1 a 1; teal = relación positiva, coral = negativa.",
        "tablas": [{"subtitulo": "", "columnas": [""] + etiquetas, "filas": filas}],
        "lectura": lectura,
    }


# ----- 2. Diferencias entre grupos -------------------------------------------
def seccion_diferencias(df):
    definiciones = [
        ("Régimen de salud", "grupo_regimen", lambda g: NOMBRE_REGIMEN[g], GRUPOS_REGIMEN),
        ("Etapa de vida de la madre", "curso_vida_madre", lambda g: NOMBRE_CURSO[g], CURSOS),
        ("Institución", "institucion", nombre_propio, sorted(df["institucion"].unique())),
        ("Área de residencia", "area_residencia", nombre_area, sorted(df["area_residencia"].dropna().unique())),
    ]
    filas, grupos = [], []
    for variable, columna, formato, orden in definiciones:
        for g in orden:
            r = resumen_grupo(df[df[columna] == g])
            if r is None:
                continue
            tenue = r["n"] < N_MINIMO
            grupos.append((variable, formato(g), r, tenue))
            filas.append(fila([
                celda(variable, "text-muted small"), celda(formato(g) + (" *" if tenue else ""), "fw-semibold"),
                celda(miles(r["n"])), celda(coma(r["edad"])), celda(coma(r["controles"])),
                celda(miles(round(r["peso"]))), celda(coma(r["pct_bajo"]) + " %"), celda(coma(r["pct_ces"]) + " %"),
            ], tenue=tenue))

    validos = [(v, g, r) for v, g, r, t in grupos if not t]
    frases = []
    reg = [(g, r) for v, g, r in validos if v == "Régimen de salud"]
    if len(reg) >= 2:
        mayor, menor = max(reg, key=lambda x: x[1]["controles"]), min(reg, key=lambda x: x[1]["controles"])
        frases.append(f"El mayor contraste está en los controles prenatales: {mayor[0].lower()} {coma(mayor[1]['controles'])} frente a "
                      f"{menor[0].lower()} {coma(menor[1]['controles'])}.")
    cur = [(g, r) for v, g, r in validos if v == "Etapa de vida de la madre"]
    if len(cur) >= 2:
        mayor, menor = max(cur, key=lambda x: x[1]["pct_ces"]), min(cur, key=lambda x: x[1]["pct_ces"])
        if mayor[1]["pct_ces"] != menor[1]["pct_ces"]:
            frases.append(f"El porcentaje de cesáreas va de {coma(menor[1]['pct_ces'])} % ({menor[0].lower()}) a "
                          f"{coma(mayor[1]['pct_ces'])} % ({mayor[0].lower()}).")
    if len(validos) >= 2:
        pesos = [r["peso"] for _, _, r in validos]
        frases.append(f"El peso medio al nacer casi no cambia entre grupos (diferencia máxima de {miles(round(max(pesos) - min(pesos)))} g): "
                      "las diferencias entre grupos están en la atención y el tipo de parto, no en el peso promedio.")
    return {
        "numero": 2, "icono": "bi-bar-chart-steps", "titulo": "Diferencias entre grupos",
        "que_analiza": "Compara seis medidas entre las categorías de régimen, etapa de vida, institución y área de residencia.",
        "tablas": [{"subtitulo": "", "columnas": ["Variable", "Grupo", "Nacimientos", "Edad media madre", "Controles medios",
                                                   "Peso medio (g)", "% bajo peso", "% cesárea"], "filas": filas}],
        "lectura": " ".join(frases) if frases else "No hay suficientes grupos para comparar con los filtros seleccionados.",
        "nota": f"* Grupos con menos de {N_MINIMO} nacimientos: se muestran atenuados y no se interpretan.",
    }


# ----- 3. Cruce de tres o más variables --------------------------------------
def seccion_cruce(df):
    filas, combos = [], []
    for reg in GRUPOS_REGIMEN:
        for cur in CURSOS:
            r = resumen_grupo(df[(df["grupo_regimen"] == reg) & (df["curso_vida_madre"] == cur)])
            if r is None:
                continue
            tenue = r["n"] < N_MINIMO
            combos.append((reg, cur, r, tenue))
            filas.append(fila([
                celda(NOMBRE_REGIMEN[reg], "fw-semibold"), celda(NOMBRE_CURSO[cur] + (" *" if tenue else "")),
                celda(miles(r["n"])), celda(coma(r["pct_ces"]) + " %"), celda(coma(r["controles"])),
                celda(coma(r["pct_pocos"]) + " %"), celda(coma(r["pct_bajo"]) + " %"),
            ], tenue=tenue))

    validos = [(reg, cur, r) for reg, cur, r, t in combos if not t]
    if len(validos) >= 2:
        alto = max(validos, key=lambda x: x[2]["pct_pocos"])
        bajo = min(validos, key=lambda x: x[2]["pct_pocos"])
        ces_alto = max(validos, key=lambda x: x[2]["pct_ces"])
        ces_bajo = min(validos, key=lambda x: x[2]["pct_ces"])
        lectura = (f"Al cruzar régimen, etapa de vida, tipo de parto, controles y peso aparecen perfiles distintos: el grupo con más madres con menos de "
                   f"{UMBRAL_CONTROLES} controles es «{NOMBRE_REGIMEN[alto[0]].lower()} · {NOMBRE_CURSO[alto[1]].lower()}» "
                   f"({coma(alto[2]['pct_pocos'])} %) y el que menos, «{NOMBRE_REGIMEN[bajo[0]].lower()} · {NOMBRE_CURSO[bajo[1]].lower()}» "
                   f"({coma(bajo[2]['pct_pocos'])} %). Las cesáreas son más frecuentes en «{NOMBRE_REGIMEN[ces_alto[0]].lower()} · "
                   f"{NOMBRE_CURSO[ces_alto[1]].lower()}» ({coma(ces_alto[2]['pct_ces'])} %) y menos en «{NOMBRE_REGIMEN[ces_bajo[0]].lower()} · "
                   f"{NOMBRE_CURSO[ces_bajo[1]].lower()}» ({coma(ces_bajo[2]['pct_ces'])} %).")
    else:
        lectura = "No hay suficientes combinaciones con datos para comparar con los filtros seleccionados."
    return {
        "numero": 3, "icono": "bi-layers", "titulo": "Cruce de tres o más variables",
        "que_analiza": "Cada fila es una combinación de régimen de salud y etapa de vida; para cada una se miden tipo de parto, controles prenatales y peso.",
        "tablas": [{"subtitulo": "", "columnas": ["Régimen de salud", "Etapa de vida", "Nacimientos", "% cesárea", "Controles medios",
                                                   f"% con menos de {UMBRAL_CONTROLES} controles", "% bajo peso"], "filas": filas}],
        "lectura": lectura,
        "nota": f"* Combinaciones con menos de {N_MINIMO} nacimientos: se muestran atenuadas y no se interpretan.",
    }


# ----- 4. Combinaciones con mayor cantidad de registros ----------------------
def seccion_combinaciones(df):
    columnas = ["grupo_regimen", "curso_vida_madre", "tipo_parto", "area_residencia"]
    conteo = df.groupby(columnas, observed=True).size().sort_values(ascending=False)
    total = int(conteo.sum())
    filas, acumulado = [], 0
    for i, (clave, n) in enumerate(conteo.head(10).items(), start=1):
        reg, cur, parto, area = clave
        acumulado += int(n)
        filas.append(fila([
            celda(str(i), "text-center text-muted"), celda(NOMBRE_REGIMEN[reg], "fw-semibold"), celda(NOMBRE_CURSO[cur], ""),
            celda(str(parto).capitalize(), ""), celda(nombre_area(area), ""),
            celda(miles(int(n))), celda(coma(porcentaje(int(n), total)) + " %"), celda(coma(porcentaje(acumulado, total)) + " %"),
        ]))
    if len(conteo):
        top = conteo.index[0]
        lectura = (f"Existen {miles(len(conteo))} combinaciones distintas de régimen, etapa de vida, tipo de parto y área, pero las 10 primeras "
                   f"reúnen el {coma(porcentaje(acumulado, total))} % de los nacimientos. La más frecuente es «{NOMBRE_REGIMEN[top[0]].lower()} · "
                   f"{NOMBRE_CURSO[top[1]].lower()} · parto {str(top[2]).lower()} · {nombre_area(top[3]).lower()}» con {miles(int(conteo.iloc[0]))} "
                   f"nacimientos ({coma(porcentaje(int(conteo.iloc[0]), total))} %). La población se concentra en pocos perfiles.")
    else:
        lectura = "No hay datos con los filtros seleccionados."
    return {
        "numero": 4, "icono": "bi-trophy", "titulo": "Combinaciones con mayor cantidad de registros",
        "que_analiza": "Las 10 combinaciones más frecuentes de cuatro variables: régimen de salud, etapa de vida, tipo de parto y área de residencia.",
        "tablas": [{"subtitulo": "", "columnas": ["#", "Régimen de salud", "Etapa de vida", "Tipo de parto", "Área de residencia",
                                                   "Nacimientos", "% del total", "% acumulado"], "filas": filas}],
        "lectura": lectura,
    }


# ----- 5. Comportamientos particulares por territorio y periodo --------------
def _marca(valor, referencia, umbral, n, sufijo=""):
    """Texto de la celda con flecha si se aleja de la referencia (solo grupos con n suficiente)."""
    texto = coma(valor) + sufijo
    if n < N_MINIMO or abs(valor - referencia) < umbral:
        return texto, ""
    return (texto + (" ▲" if valor > referencia else " ▼")), "fw-bold"


def _tabla_comportamiento(df, columna, formato, valores, nombre_primera):
    general = resumen_grupo(df)
    filas = [fila([celda("Total (referencia)", "fw-semibold"), celda(miles(general["n"])),
                   celda(coma(general["pct_no_aseg"]) + " %"), celda(coma(general["controles"])),
                   celda(coma(general["pct_pocos"]) + " %"), celda(coma(general["pct_ces"]) + " %")], fuerte=True)]
    detalle = []
    for v in valores:
        r = resumen_grupo(df[df[columna] == v])
        if r is None:
            continue
        detalle.append((v, r))
        t1, c1 = _marca(r["pct_no_aseg"], general["pct_no_aseg"], UMBRAL_PP, r["n"], " %")
        t2, c2 = _marca(r["controles"], general["controles"], UMBRAL_CONTROLES_DIF, r["n"])
        t3, c3 = _marca(r["pct_pocos"], general["pct_pocos"], UMBRAL_PP, r["n"], " %")
        t4, c4 = _marca(r["pct_ces"], general["pct_ces"], UMBRAL_PP, r["n"], " %")
        filas.append(fila([celda(formato(v), "fw-semibold"), celda(miles(r["n"])),
                           celda(t1, "text-end " + c1), celda(t2, "text-end " + c2),
                           celda(t3, "text-end " + c3), celda(t4, "text-end " + c4)],
                          tenue=r["n"] < N_MINIMO))
    columnas = [nombre_primera, "Nacimientos", "% madres no aseguradas", "Controles medios",
                f"% con menos de {UMBRAL_CONTROLES} controles", "% cesárea"]
    return columnas, filas, detalle, general


def seccion_territorio_periodo(df):
    # Territorio: los municipios de residencia con más nacimientos
    conteo = df["municipio_residencia"].value_counts()
    municipios = [m for m in conteo.index if conteo[m] >= N_MINIMO][:8]
    col_t, filas_t, det_t, general = _tabla_comportamiento(
        df, "municipio_residencia", nombre_propio, municipios, "Municipio de residencia")
    otros = df[~df["municipio_residencia"].isin(municipios)]
    r = resumen_grupo(otros)
    if r is not None and municipios:
        filas_t.append(fila([celda("Otros municipios", "fw-semibold"), celda(miles(r["n"])),
                             celda(coma(r["pct_no_aseg"]) + " %"), celda(coma(r["controles"])),
                             celda(coma(r["pct_pocos"]) + " %"), celda(coma(r["pct_ces"]) + " %")]))

    # Periodo: año de reporte
    col_p, filas_p, det_p, _ = _tabla_comportamiento(
        df, "anio", lambda a: str(a), sorted(df["anio"].unique().tolist()), "Año de reporte")

    frases = []
    grandes = [(v, r) for v, r in det_t if r["n"] >= N_MINIMO]
    if len(grandes) >= 2:
        # Se destacan los municipios que más se alejan del total, no el simple máximo
        d_cesarea = max(grandes, key=lambda x: abs(x[1]["pct_ces"] - general["pct_ces"]))
        d_aseg = max(grandes, key=lambda x: abs(x[1]["pct_no_aseg"] - general["pct_no_aseg"]))
        if abs(d_cesarea[1]["pct_ces"] - general["pct_ces"]) >= UMBRAL_PP:
            frases.append(f"Por territorio, {nombre_propio(d_cesarea[0])} es el más distinto en cesáreas "
                          f"({coma(d_cesarea[1]['pct_ces'])} % frente a {coma(general['pct_ces'])} % en el total).")
        if abs(d_aseg[1]["pct_no_aseg"] - general["pct_no_aseg"]) >= UMBRAL_PP:
            frases.append(f"{nombre_propio(d_aseg[0])} se aparta más en madres no aseguradas "
                          f"({coma(d_aseg[1]['pct_no_aseg'])} % frente a {coma(general['pct_no_aseg'])} %).")
        if not frases:
            frases.append("Por territorio, los municipios con más nacimientos se parecen al total en las medidas analizadas.")
    anios = [(v, r) for v, r in det_p if r["n"] >= N_MINIMO]
    if len(anios) >= 2:
        a_alto = max(anios, key=lambda x: x[1]["pct_pocos"])
        a_bajo = min(anios, key=lambda x: x[1]["pct_pocos"])
        frases.append(f"Por periodo, el porcentaje de madres con menos de {UMBRAL_CONTROLES} controles fue más alto en {a_alto[0]} "
                      f"({coma(a_alto[1]['pct_pocos'])} %) y más bajo en {a_bajo[0]} ({coma(a_bajo[1]['pct_pocos'])} %).")
    return {
        "numero": 5, "icono": "bi-geo-alt", "titulo": "Comportamientos particulares por territorio y periodo",
        "que_analiza": "Detecta categorías que se alejan del total: municipios de residencia (territorio) y años de reporte (periodo).",
        "tablas": [{"subtitulo": "Territorio: municipio de residencia de la madre", "columnas": col_t, "filas": filas_t},
                   {"subtitulo": "Periodo: año de reporte", "columnas": col_p, "filas": filas_p}],
        "lectura": " ".join(frases) if frases else "No hay suficientes categorías para comparar con los filtros seleccionados.",
        "nota": (f"▲ / ▼ = al menos {coma(UMBRAL_PP)} puntos porcentuales por encima o por debajo del total "
                 f"(0,5 controles en el promedio de controles). Solo se resaltan grupos con {N_MINIMO} o más nacimientos. "
                 "El año 2026 llega solo hasta julio y Santa Teresita casi deja de reportar desde 2023."),
    }


# ----- 6. Posibles casos inusuales -------------------------------------------
def seccion_inusuales(df):
    padre = df["edad_padre"]
    semanas = df["semanas_validas"]
    diferencia = padre - df["edad_madre"]
    criterios = [
        ("Muy bajo peso al nacer", "Peso menor de 1.500 g", df["peso_gramos"] < 1500, "Clínico",
         "Recién nacidos de riesgo alto que requieren cuidado neonatal especializado."),
        ("Peso muy alto", "Peso mayor de 4.500 g", df["peso_gramos"] > 4500, "Clínico",
         "Peso muy superior al promedio (3.264 g); puede asociarse a mayor riesgo en el parto."),
        ("Prematuridad extrema", "Menos de 28 semanas de gestación", semanas < 28, "Clínico",
         "Nacimientos con la mayor necesidad de atención neonatal."),
        ("Madre menor de 15 años", "Edad de la madre menor de 15", df["edad_madre"] < 15, "Clínico / social",
         "Grupo de atención prioritaria dentro de la adolescencia."),
        ("Madre de 45 años o más", "Edad de la madre de 45 o más", df["edad_madre"] >= 45, "Clínico",
         "Edad materna muy avanzada; embarazo de mayor riesgo."),
        ("Muchos controles prenatales", "11 o más controles", df["consultas_prenatales"] >= 11, "Atípico",
         "Muy por encima de lo habitual (la mediana es de 5 controles); sugiere seguimiento de alto riesgo o error de digitación."),
        ("Parto a término sin controles", "37 o más semanas y 0 controles", (semanas >= 37) & (df["consultas_prenatales"] == 0), "Atípico",
         "Embarazos completos que llegaron al parto sin ninguna atención prenatal."),
        ("Alta paridad", "8 o más embarazos", df["numero_embarazos"] >= 8, "Clínico / social",
         "Madres con muchos embarazos previos."),
        ("Embarazo múltiple", "Doble o triple", df["multiplicidad_embarazo"].isin(["DOBLE", "TRIPLE"]), "Clínico",
         "Solo se registra desde 2023, por lo que el conteo es parcial."),
        ("Peso incoherente con las semanas", "Menos de 34 semanas y más de 3.000 g, o 37 o más semanas y menos de 1.800 g",
         ((semanas < 34) & (df["peso_gramos"] > 3000)) | ((semanas >= 37) & (df["peso_gramos"] < 1800)), "Posible error",
         "Combinación poco probable; conviene verificar el registro."),
        ("Semanas de gestación sin dato", "Semanas igual a 0 o vacías", df["semanas_gestacion"].fillna(0) <= 0, "Posible error",
         "Dato faltante registrado como 0; se excluye del cálculo de prematuridad."),
        ("Edad del padre imposible", "Menor de 15 o mayor de 70 años", (padre < 15) | (padre > 70), "Posible error",
         "Valores como -4 o 99 años indican errores de digitación."),
        ("Más hijos vivos que embarazos", "Hijos nacidos vivos mayor que número de embarazos", df["hijos_nacidos_vivos"] > df["numero_embarazos"], "Posible error",
         "Inconsistencia entre dos variables del mismo registro."),
        ("Gran diferencia de edad en la pareja", "Padre 25 años o más mayor que la madre", (diferencia >= 25) & (padre <= 70), "Atípico",
         "Diferencia poco frecuente; puede reflejar un registro de la edad equivocado."),
    ]
    total = len(df)
    estilo = {"Clínico": "text-bg-info", "Clínico / social": "text-bg-info", "Atípico": "text-bg-warning",
              "Posible error": "text-bg-danger"}
    filas, marcados = [], pd.Series(False, index=df.index)
    for nombre, regla, mascara, tipo, lectura in criterios:
        mascara = mascara.fillna(False)
        n = int(mascara.sum())
        if n == 0:
            continue
        marcados |= mascara
        ids = ", ".join(str(i) for i in df.loc[mascara, "id"].head(3))
        filas.append((n, fila([celda(nombre, "fw-semibold"), celda(regla, "small"), celda(miles(n)),
                               celda(coma(porcentaje(n, total)) + " %"), celda(tipo, "", "", estilo[tipo]),
                               celda(lectura, "small"), celda(ids, "small text-muted")])))
    filas.sort(key=lambda x: -x[0])
    n_marcados = int(marcados.sum())
    errores = sum(1 for nombre, _, m, tipo, _ in criterios if tipo == "Posible error" and int(m.fillna(False).sum()) > 0)
    lectura = (f"{miles(n_marcados)} nacimientos ({coma(porcentaje(n_marcados, total))} %) cumplen al menos un criterio inusual; "
               "son una minoría del total y conviene revisarlos por separado." if n_marcados else
               "Con los filtros seleccionados ningún nacimiento cumple los criterios de caso inusual.")
    if filas:
        lectura += (f" El caso más numeroso es «{filas[0][1]['celdas'][0]['t'].lower()}» ({miles(filas[0][0])} nacimientos). "
                    f"{errores} de los criterios con casos apuntan a posibles errores de registro, que conviene depurar antes de usar esos campos.")
    return {
        "numero": 6, "icono": "bi-exclamation-diamond", "titulo": "Posibles casos inusuales",
        "que_analiza": "Busca registros que se salen de lo esperado con criterios fijos. Que un caso sea inusual no significa que sea un error: puede ser clínicamente real.",
        "tablas": [{"subtitulo": "", "columnas": ["Caso", "Criterio", "Nacimientos", "% del total", "Tipo", "Posible lectura", "Ejemplos (id)"],
                    "filas": [f for _, f in filas]}],
        "lectura": lectura,
    }


def calcular_secciones(df):
    return [
        seccion_relaciones(df), seccion_diferencias(df), seccion_cruce(df),
        seccion_combinaciones(df), seccion_territorio_periodo(df), seccion_inusuales(df),
    ]


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
            "interpretaciones": {}, "conocimientos": [{}, {}, {}], "secciones": [],
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
        "secciones": calcular_secciones(df),
        "conocimientos": conocimientos,
        "limitacion": LIMITACION,
        "decision": decision,
    })
    return render_template("dimensiones/multivariada.html", **contexto)
