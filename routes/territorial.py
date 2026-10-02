"""
Dimensión territorial - Integrante 2.

Pregunta de análisis:
    ¿Cómo se distribuye la población y sus principales características entre
    los territorios disponibles?

Se trabaja con el lugar de residencia de la madre (departamento, municipio,
área y comuna). Todo se calcula con pandas a partir de cargar_datos() y se
envía a templates/dimensiones/territorial.html
"""

from flask import Blueprint, render_template, request

from utils.datos import VARIABLES, cargar_datos, opciones

bp = Blueprint("territorial", __name__)

COLUMNAS_USADAS = [
    "departamento_residencia", "municipio_residencia", "area_residencia",
    "comuna", "anio", "tipo_parto", "regimen_seguridad",
]

# Municipios que se muestran en la gráfica de barras; el resto se agrupa en "Otros"
TOP_MUNICIPIOS = 10

# Para comparar características entre municipios se exige un mínimo de
# registros; con menos casos los porcentajes cambian demasiado.
MINIMO_COMPARACION = 30

SIN_IDENTIFICAR = "SIN IDENTIFICAR"
ZONA_RURAL = "ZONA RURAL (CORREGIMIENTOS)"
OTROS_BARRIOS = "OTROS BARRIOS SIN COMUNA"

# Las 17 comunas oficiales de Bucaramanga
COMUNAS_OFICIALES = [
    "NORTE", "NORORIENTAL", "SAN FRANCISCO", "OCCIDENTAL", "GARCIA ROVIRA",
    "LA CONCORDIA", "LA CIUDADELA", "SUR OCCIDENTE", "LA PEDREGOSA", "PROVENZA",
    "SUR", "CABECERA DEL LLANO", "ORIENTAL", "MORRORICO", "CENTRO",
    "LAGOS DEL CACIQUE", "MUTIS",
]

# El campo comuna se digita a mano y trae la misma comuna escrita de varias formas
VARIANTES_COMUNA = {
    "MORRORRICO": "MORRORICO",
    "MORORRICO": "MORRORICO",
    "OCCIDENTE": "OCCIDENTAL",
    "ORIENTE": "ORIENTAL",
    "NORORIENTE": "NORORIENTAL",
    "CONCORDIA": "LA CONCORDIA",
    "REAL DE MINAS": "LA CIUDADELA",
    "CIUDADELA REAL DE MINAS": "LA CIUDADELA",
    "SIN IENTIFICAR": SIN_IDENTIFICAR,
    "SIN INFORMACION": SIN_IDENTIFICAR,
}

VARIANTES_MUNICIPIO = {"CACHIRÁ": "CÁCHIRA"}

LIMITACION = (
    "El territorio corresponde al lugar de residencia de la madre y los datos provienen solo de dos "
    "instituciones públicas de Bucaramanga (Hospital Local del Norte y Unidad Materno Infantil Santa "
    "Teresita). Por eso las cifras muestran de dónde llegan las madres a esta red, no cuántos niños "
    "nacen en cada municipio: una madre de Girón o Floridablanca que dio a luz en otra clínica no aparece. "
    "Además, la comuna se digita a mano (hay varias formas de escribir la misma comuna y cerca del 10 % "
    "de los registros de Bucaramanga no la identifica) y los municipios con pocos registros generan "
    "porcentajes poco estables, por lo que no se comparan."
)


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def porcentaje(parte, total):
    return round(parte * 100 / total, 1) if total else 0.0


def miles(numero):
    """5394 -> '5.394'."""
    return f"{numero:,}".replace(",", ".")


def coma(numero):
    """76.9 -> '76,9'."""
    return f"{numero:.1f}".replace(".", ",")


def nombre_propio(valor):
    """'EL PLAYÓN' -> 'El Playón', 'NORTE DE SANTANDER' -> 'Norte de Santander'."""
    texto = str(valor).title()
    for palabra in (" De ", " Del ", " La ", " Los ", " Sin "):
        texto = texto.replace(palabra, palabra.lower())
    return texto


def normalizar_comuna(valor):
    if not isinstance(valor, str) or not valor.strip():
        return SIN_IDENTIFICAR
    valor = VARIANTES_COMUNA.get(valor.strip().upper(), valor.strip().upper())
    if valor in COMUNAS_OFICIALES or valor == SIN_IDENTIFICAR:
        return valor
    if valor.startswith(("RURAL", "CORREG", "VEREDA")):
        return ZONA_RURAL
    return OTROS_BARRIOS


def preparar(df):
    """Unifica nombres de municipio y comuna antes de agrupar."""
    df = df.copy()
    df["municipio_residencia"] = df["municipio_residencia"].replace(VARIANTES_MUNICIPIO).fillna(SIN_IDENTIFICAR)
    df["departamento_residencia"] = df["departamento_residencia"].fillna(SIN_IDENTIFICAR)
    df["comuna_bga"] = df["comuna"].map(normalizar_comuna)
    return df


def leer_filtros(df):
    """
    Filtros interactivos que llegan por la URL (?anio=2024&area=RURAL DISPERSO).
    Si el valor no existe en los datos se ignora.
    """
    anio = request.args.get("anio", "")
    area = request.args.get("area", "")
    if not anio.isdigit() or int(anio) not in opciones(df, "anio"):
        anio = ""
    if area not in opciones(df, "area_residencia"):
        area = ""
    return anio, area


def aplicar_filtros(df, anio, area):
    if anio:
        df = df[df["anio"] == int(anio)]
    if area:
        df = df[df["area_residencia"] == area]
    return df


# ---------------------------------------------------------------------------
# Cálculos del tablero
# ---------------------------------------------------------------------------
def tabla_municipios(df):
    """Participación de cada municipio con su departamento y porcentaje acumulado."""
    total = len(df)
    conteo = (df.groupby(["municipio_residencia", "departamento_residencia"]).size()
                .reset_index(name="n").sort_values("n", ascending=False))
    filas, acumulado = [], 0
    for fila in conteo.itertuples():
        acumulado += fila.n
        filas.append({
            "municipio": nombre_propio(fila.municipio_residencia),
            "departamento": nombre_propio(fila.departamento_residencia),
            "registros": miles(int(fila.n)),
            "pct": coma(porcentaje(fila.n, total)),
            "acumulado": coma(porcentaje(acumulado, total)),
        })
    return filas


def grafica_municipios(df):
    """Los municipios con más registros; el resto se suma en 'Otros'."""
    total = len(df)
    conteo = df["municipio_residencia"].value_counts()
    principales = conteo.head(TOP_MUNICIPIOS)
    etiquetas = [nombre_propio(m) for m in principales.index]
    valores = [int(v) for v in principales]
    resto = conteo.iloc[TOP_MUNICIPIOS:]
    if not resto.empty:
        etiquetas.append(f"Otros ({len(resto)} municipios)")
        valores.append(int(resto.sum()))
    return {
        "etiquetas": etiquetas,
        "valores": valores,
        "porcentajes": [porcentaje(v, total) for v in valores],
    }


def grafica_comunas(df):
    """Nacimientos por comuna, solo para madres que viven en Bucaramanga."""
    bga = df[df["municipio_residencia"] == "BUCARAMANGA"]
    total = len(bga)
    conteo = bga["comuna_bga"].value_counts()
    sin_dato = int(conteo.get(SIN_IDENTIFICAR, 0))
    conteo = conteo.drop(SIN_IDENTIFICAR, errors="ignore")
    return {
        "etiquetas": [nombre_propio(c) for c in conteo.index],
        "valores": [int(v) for v in conteo],
        "porcentajes": [porcentaje(int(v), total) for v in conteo],
        "total_bga": total,
        "sin_dato": sin_dato,
        "pct_sin_dato": porcentaje(sin_dato, total),
        "comunas_con_registros": int(conteo.index.isin(COMUNAS_OFICIALES).sum()),
    }


def grafica_comparacion(df):
    """
    % de cesárea, % de madres no aseguradas y % de residencia rural en los
    municipios que tienen al menos MINIMO_COMPARACION registros (máximo 6).
    """
    conteo = df["municipio_residencia"].value_counts()
    municipios = [m for m in conteo.index if conteo[m] >= MINIMO_COMPARACION and m != SIN_IDENTIFICAR][:6]
    datos = {"etiquetas": [], "cesarea": [], "no_asegurado": [], "rural": [], "registros": []}
    for m in municipios:
        grupo = df[df["municipio_residencia"] == m]
        n = len(grupo)
        datos["etiquetas"].append(nombre_propio(m))
        datos["registros"].append(n)
        datos["cesarea"].append(porcentaje(int((grupo["tipo_parto"] == "CESÁREA").sum()), n))
        datos["no_asegurado"].append(porcentaje(int((grupo["regimen_seguridad"] == "NO ASEGURADO").sum()), n))
        datos["rural"].append(porcentaje(int((grupo["area_residencia"] != "CABECERA MUNICIPAL").sum()), n))
    return datos


def calcular_indicadores(df):
    total = len(df)
    if total == 0:
        return {"municipios": 0, "departamentos": 0, "principal": "—", "pct_principal": "—",
                "pct_fuera": "—", "fuera": 0}
    conteo = df["municipio_residencia"].value_counts()
    fuera = int((df["departamento_residencia"] != "SANTANDER").sum())
    return {
        "municipios": int(conteo.index.drop(SIN_IDENTIFICAR, errors="ignore").size),
        "departamentos": int(df["departamento_residencia"].replace(SIN_IDENTIFICAR, None).nunique()),
        "principal": nombre_propio(conteo.index[0]),
        "pct_principal": coma(porcentaje(int(conteo.iloc[0]), total)),
        "pct_fuera": coma(porcentaje(fuera, total)),
        "fuera": fuera,
    }


# ---------------------------------------------------------------------------
# Textos del análisis. Las cifras salen de los datos filtrados para que el
# texto siempre coincida con las gráficas.
# ---------------------------------------------------------------------------
def redactar(df, municipios, comunas, comparacion):
    total = len(df)
    if total == 0:
        return {}, [{}, {}, {}], "No hay registros con los filtros seleccionados."

    conteo = df["municipio_residencia"].value_counts()
    m1, pct_m1 = nombre_propio(conteo.index[0]), coma(porcentaje(int(conteo.iloc[0]), total))
    pct_top3 = coma(porcentaje(int(conteo.head(3).sum()), total))
    nombres_top3 = [nombre_propio(m) for m in conteo.head(3).index]
    top3 = ", ".join(nombres_top3[:-1]) + " y " + nombres_top3[-1] if len(nombres_top3) > 1 else nombres_top3[0]
    identificados = conteo.drop(SIN_IDENTIFICAR, errors="ignore")
    pocos = int((identificados < 10).sum())
    n_municipios = int(identificados.size)

    fuera = df[df["departamento_residencia"] != "SANTANDER"]
    pct_fuera = coma(porcentaje(len(fuera), total))
    deptos_fuera = fuera["departamento_residencia"].replace(SIN_IDENTIFICAR, None).dropna().value_counts()
    depto_fuera = nombre_propio(deptos_fuera.index[0]) if not deptos_fuera.empty else "—"
    pct_depto_fuera = coma(porcentaje(int(deptos_fuera.iloc[0]), len(fuera))) if not deptos_fuera.empty else "0"

    # Comunas de Bucaramanga
    hay_comunas = bool(comunas["valores"])
    c1 = comunas["etiquetas"][0] if hay_comunas else "—"
    pct_c1 = coma(comunas["porcentajes"][0]) if hay_comunas else "0"
    c2 = comunas["etiquetas"][1] if len(comunas["etiquetas"]) > 1 else "—"
    pct_c2 = coma(comunas["porcentajes"][1]) if len(comunas["porcentajes"]) > 1 else "0"
    pct_sin = coma(comunas["pct_sin_dato"])

    def nombre_zona(etiqueta):
        if etiqueta.upper() in COMUNAS_OFICIALES:
            return f"la comuna {etiqueta}"
        if etiqueta.upper() == ZONA_RURAL:
            return "la zona rural (corregimientos)"
        return f"el grupo «{etiqueta.lower()}»"

    zona_c1 = nombre_zona(c1) if hay_comunas else "—"
    zona_c2 = nombre_zona(c2) if len(comunas["etiquetas"]) > 1 else "ninguna otra zona"

    # Comparación entre municipios
    hay_comparacion = len(comparacion["etiquetas"]) >= 2
    if hay_comparacion:
        ces = dict(zip(comparacion["etiquetas"], comparacion["cesarea"]))
        aseg = dict(zip(comparacion["etiquetas"], comparacion["no_asegurado"]))
        ces_max, ces_min = max(ces, key=ces.get), min(ces, key=ces.get)
        aseg_max, aseg_min = max(aseg, key=aseg.get), min(aseg, key=aseg.get)
        # ¿Bucaramanga tiene menos cesáreas que los demás municipios comparados?
        ces_bga = ces.get("Bucaramanga")
        otros = [v for k, v in ces.items() if k != "Bucaramanga"]
        bga_menos_cesarea = ces_bga is not None and otros and ces_bga < min(otros)
        texto_comparacion = (
            f"La cesárea va de {coma(ces[ces_min])} % en {ces_min} a {coma(ces[ces_max])} % en {ces_max}, "
            f"y las madres no aseguradas van de {coma(aseg[aseg_min])} % en {aseg_min} a "
            f"{coma(aseg[aseg_max])} % en {aseg_max}."
        )
    else:
        ces_max = aseg_max = "—"
        bga_menos_cesarea = False
        texto_comparacion = (f"Con los filtros actuales no hay al menos dos municipios con {MINIMO_COMPARACION} "
                             "o más registros para comparar.")

    interpretaciones = {
        "municipios": (
            f"{m1} concentra el {pct_m1} % de los nacimientos y los tres municipios principales "
            f"({top3}) suman el {pct_top3} %. Los registros vienen de {n_municipios} municipios, pero "
            f"{pocos} de ellos aportan menos de 10 nacimientos cada uno."
        ),
        "comunas": (
            f"Dentro de Bucaramanga {zona_c1} tiene la mayor participación ({pct_c1} % de los nacimientos "
            f"de la ciudad), seguida por {zona_c2} ({pct_c2} %). El {pct_sin} % de los registros de Bucaramanga "
            "no tiene la comuna identificada y no se muestra en la gráfica."
        ) if hay_comunas else "Con los filtros actuales no hay madres residentes en Bucaramanga.",
        "comparacion": (
            f"{texto_comparacion} Las barras de residencia rural muestran que algunos municipios llegan "
            "principalmente desde el campo, mientras que en el área metropolitana casi todas las madres viven en la cabecera."
        ),
    }

    conocimientos = [
        {
            "pregunta": "¿En qué territorios se concentra la población atendida y qué tan dispersa es?",
            "variables": "municipio_residencia, departamento_residencia",
            "procedimiento": "Se contaron los nacimientos por municipio de residencia, se ordenaron de mayor a menor y se calculó el porcentaje y el porcentaje acumulado sobre el total filtrado.",
            "evidencia": f"Gráfica 1 y tabla de participación: {m1} {pct_m1} %, tres municipios principales {pct_top3} %, {pocos} municipios con menos de 10 registros.",
            "hallazgo": f"{m1} concentra el {pct_m1} % de los nacimientos y tres municipios reúnen el {pct_top3} %.",
            "interpretacion": f"La red pública atiende sobre todo a madres de {m1} y su entorno inmediato, aunque recibe casos aislados de {n_municipios} municipios y el {pct_fuera} % viene de fuera de Santander (principalmente {depto_fuera}, {pct_depto_fuera} % de esos casos).",
            "utilidad": "Permite dimensionar la demanda que llega de otros municipios y orientar convenios de remisión con las alcaldías de donde más madres provienen.",
            "limitacion": "No se puede concluir que en los municipios con pocos registros nazcan pocos niños; solo que pocas madres de allí dieron a luz en estas dos instituciones.",
        },
        {
            "pregunta": "¿Cómo se reparten los nacimientos entre las comunas de Bucaramanga?",
            "variables": "municipio_residencia, comuna",
            "procedimiento": "Se filtraron las madres residentes en Bucaramanga, se unificaron los nombres de comuna escritos de distintas formas y se calculó el porcentaje de cada comuna sobre el total de la ciudad.",
            "evidencia": f"Gráfica 2: {zona_c1} {pct_c1} %, {zona_c2} {pct_c2} %, sin comuna identificada {pct_sin} %.",
            "hallazgo": (f"{zona_c1[0].upper() + zona_c1[1:]} tiene la mayor participación, con el {pct_c1} % de los nacimientos de la ciudad."
                         if hay_comunas else "Con los filtros actuales no hay madres residentes en Bucaramanga."),
            "interpretacion": (
                "La concentración en el norte de la ciudad coincide con la ubicación del Hospital Local del Norte, que "
                "atiende la mayoría de los partos del conjunto de datos; la cercanía al hospital parece pesar en la distribución."
                if c1 == "Norte" else
                f"Los nacimientos de la ciudad no se reparten de forma pareja: {zona_c1} tiene un peso mayor que las demás."
            ),
            "utilidad": "Ayuda a ubicar en las comunas con más nacimientos las jornadas de control prenatal, vacunación y afiliación al sistema de salud.",
            "limitacion": "La comuna se registra a mano y una parte no está identificada; además, sin la población de cada comuna no puede saberse en cuál nacen más niños por habitante.",
        },
        {
            "pregunta": "¿Las características de los nacimientos cambian según el municipio de residencia?",
            "variables": "municipio_residencia, tipo_parto, regimen_seguridad, area_residencia",
            "procedimiento": f"Para los municipios con {MINIMO_COMPARACION} o más registros se calculó el porcentaje de cesáreas, de madres no aseguradas y de madres que viven fuera de la cabecera municipal.",
            "evidencia": f"Gráfica 3: {texto_comparacion}",
            "hallazgo": (f"El porcentaje de cesárea más alto está en {ces_max} y el de madres no aseguradas en {aseg_max}."
                         if hay_comparacion else texto_comparacion),
            "interpretacion": (
                "Las madres que llegan desde otros municipios presentan más cesáreas que las de Bucaramanga, lo que "
                "podría reflejar que se remiten casos más complejos."
                if bga_menos_cesarea else
                "El tipo de parto y el aseguramiento no son iguales en todos los municipios, así que el lugar de "
                "residencia ayuda a diferenciar grupos de madres con necesidades distintas."
            ) + (f" La mayor proporción de madres no aseguradas se encuentra en {aseg_max}." if hay_comparacion else ""),
            "utilidad": "Sirve para revisar con los municipios vecinos los criterios de remisión de partos y para enfocar la afiliación de madres no aseguradas donde más se presenta.",
            "limitacion": "Los datos no indican el motivo de la cesárea ni si la madre fue remitida; la diferencia entre municipios no prueba una causa.",
        },
    ]

    partes = [f"{m1} aporta el {pct_m1} % de los nacimientos"]
    if hay_comunas:
        partes.append(f"dentro de Bucaramanga {zona_c1} reúne el {pct_c1} %")
    decision = (
        f"Como {' y '.join(partes)}, la Secretaría de Salud podría priorizar allí los puntos de control "
        "prenatal y de afiliación al sistema de salud."
    )
    if hay_comparacion:
        decision += (
            f" Además, como {ces_max} presenta el porcentaje de cesárea más alto entre los municipios comparados "
            f"y el {pct_fuera} % de las madres viene de otros departamentos, conviene coordinar con esas alcaldías "
            "la atención prenatal temprana para que las madres no lleguen remitidas solo en el momento del parto."
        )
    return interpretaciones, conocimientos, decision


# ---------------------------------------------------------------------------
# Ruta
# ---------------------------------------------------------------------------
@bp.route("/dimension/territorial")
def index():
    completo = preparar(cargar_datos())
    anio, area = leer_filtros(completo)
    df = aplicar_filtros(completo, anio, area)

    g_municipios = grafica_municipios(df)
    g_comunas = grafica_comunas(df)
    g_comparacion = grafica_comparacion(df)
    interpretaciones, conocimientos, decision = redactar(df, g_municipios, g_comunas, g_comparacion)

    contexto = {
        "titulo": "Dimensión territorial",
        "pregunta": "¿Cómo se distribuye la población y sus principales características entre los territorios disponibles?",
        "total_registros": len(df),
        # Descripción de las variables utilizadas
        "variables": [v for v in VARIABLES if v["columna"] in COLUMNAS_USADAS],
        # Filtros interactivos
        "anio_sel": anio,
        "area_sel": area,
        "anios": opciones(completo, "anio"),
        "areas": opciones(completo, "area_residencia"),
        # Indicadores
        "indicadores": calcular_indicadores(df),
        # Datos de las visualizaciones
        "g_municipios": g_municipios,
        "g_comunas": g_comunas,
        "g_comparacion": g_comparacion,
        "minimo_comparacion": MINIMO_COMPARACION,
        "interpretaciones": interpretaciones,
        # Participación porcentual de cada territorio
        "tabla_municipios": tabla_municipios(df),
        # Conocimientos evidentes, limitación y decisión
        "conocimientos": conocimientos,
        "limitacion": LIMITACION,
        "decision": decision,
    }
    return render_template("dimensiones/territorial.html", **contexto)
