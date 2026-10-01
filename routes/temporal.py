"""
Dimensión temporal - Integrante 3.

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Leer los datos con cargar_datos() y pasar todo a la plantilla
templates/dimensiones/temporal.html
"""

from flask import Blueprint, render_template
import pandas as pd

from utils.datos import cargar_datos

bp = Blueprint("temporal", __name__)


@bp.route("/dimension/temporal")
def index():
    df = cargar_datos()
    fechas = df["fecha_nacimiento"]
    anual = df.groupby(fechas.dt.year).size().sort_index()
    mensual = df.groupby(fechas.dt.to_period("M")).size().sort_index()
    anios_numero = [int(anio) for anio in anual.index]
    anio_actual = anios_numero[-1]
    anios_completos = [
        anio for anio in anios_numero
        if sum(periodo.year == anio for periodo in mensual.index) == 12
    ]
    nombres_meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    cambios_anuales = []
    promedios_mensuales = []
    for anio in anios_numero:
        if anio in anios_completos and anio - 1 in anual.index:
            cambios_anuales.append(round((anual[anio] / anual[anio - 1] - 1) * 100, 1))
        else:
            cambios_anuales.append(None)
        promedios_mensuales.append(round(anual[anio] / 12) if anio in anios_completos else None)

    periodos_por_anio = {}
    for anio in anios_numero:
        conteos_meses = [
            int(mensual.get(pd.Period(f"{anio}-{mes:02d}", freq="M"), 0))
            for mes in range(1, 13)
        ]
        periodos_por_anio[str(anio)] = [sum(conteos_meses[:3]), sum(conteos_meses[:7])]

    indices_estacionales = []
    for mes in range(1, 13):
        indices_por_anio = [
            mensual.get(pd.Period(f"{anio}-{mes:02d}", freq="M"), 0) / (anual[anio] / 12)
            for anio in anios_completos
        ]
        indices_estacionales.append(round(sum(indices_por_anio) / len(indices_por_anio), 2))

    meses_completos = mensual[
        [periodo.year in anios_completos for periodo in mensual.index]
    ]
    trimestres_completos = df.loc[fechas.dt.year.isin(anios_completos)].groupby(
        fechas[fechas.dt.year.isin(anios_completos)].dt.to_period("Q")
    ).size()
    meses_altos = meses_completos.sort_values(ascending=False).head(3)
    meses_bajos = meses_completos.sort_values().head(3)

    diario = df.groupby(fechas.dt.normalize()).size()
    dias_calendario = pd.date_range(
        start=f"{anios_completos[0]}-01-01",
        end=f"{anios_completos[-1]}-12-31",
        freq="D",
    )
    diario_completo = diario.reindex(dias_calendario, fill_value=0)
    total_por_dia_semana = df.loc[fechas.dt.year.isin(anios_completos)].groupby(
        fechas[fechas.dt.year.isin(anios_completos)].dt.dayofweek
    ).size()
    dias_por_dia_semana = pd.Series(dias_calendario.dayofweek).value_counts().sort_index()
    promedio_dia_semana = [
        round(total_por_dia_semana.get(dia, 0) / dias_por_dia_semana.get(dia, 1), 1)
        for dia in range(7)
    ]
    nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    partos_completos = df.loc[fechas.dt.year.isin(anios_completos)].copy()
    partos_completos["dia_semana_num"] = fechas[fechas.dt.year.isin(anios_completos)].dt.dayofweek
    partos_completos["es_cesarea"] = partos_completos["tipo_parto"].str.contains("CES", case=False, na=False)
    porcentaje_cesarea = partos_completos.groupby("dia_semana_num")["es_cesarea"].mean() * 100

    ultimo_periodo = mensual.index.max()
    dia_pico = diario.idxmax()
    mes_nombre = lambda periodo: f"{nombres_meses[periodo.month - 1].lower()} de {periodo.year}"
    q1_2025 = periodos_por_anio.get("2025", [0, 0])[0]
    q1_actual = periodos_por_anio[str(anio_actual)][0]
    variacion_q1 = round((q1_actual / q1_2025 - 1) * 100, 1) if q1_2025 else None
    ene_jul_2025 = periodos_por_anio.get("2025", [0, 0])[1]
    ene_jul_actual = periodos_por_anio[str(anio_actual)][1]
    variacion_ene_jul = round((ene_jul_actual / ene_jul_2025 - 1) * 100, 1) if ene_jul_2025 else None
    variacion_2020_2025 = round((anual[2025] / anual[2020] - 1) * 100, 1)
    meses_2026_unicos = [
        int(mensual.get(pd.Period(f"{anio_actual}-{mes:02d}", freq="M"), 0))
        for mes in range(4, ultimo_periodo.month + 1)
    ]

    curso = pd.crosstab(df["anio"], df["curso_vida_madre"], normalize="index") * 100
    porcentaje_curso = {
        str(anio): {
            categoria: round(float(curso.loc[anio].get(categoria, 0)), 1)
            for categoria in ["ADOLESCENCIA", "JUVENTUD", "ADULTEZ"]
        }
        for anio in [2022, 2023, 2024, 2025]
        if anio in curso.index
    }

    contexto = {
        "titulo": "Dimensión temporal",
        "pregunta": "¿Cómo evolucionaron los nacimientos registrados en Bucaramanga entre 2020 y 2026?",
        "total_registros": len(df),
        "registros_unicos": len(df),
        "filas_fuente": 34309,
        "duplicados_exactos": 34309 - len(df),
        "fecha_inicio": fechas.min().strftime("%d/%m/%Y"),
        "fecha_fin": fechas.max().strftime("%d/%m/%Y"),
        "anios": [
            f"{anio} (ene-{nombres_meses[ultimo_periodo.month - 1].lower()})"
            if anio == anio_actual and ultimo_periodo.month < 12 else str(anio)
            for anio in anios_numero
        ],
        "registros_anuales": [int(anual[anio]) for anio in anios_numero],
        "cambios_anuales": cambios_anuales,
        "promedio_mensual": promedios_mensuales,
        "periodos": ["Ene-Mar", "Ene-Jul"],
        "periodos_por_anio": periodos_por_anio,
        "q1_actual": q1_actual,
        "variacion_q1": variacion_q1,
        "ene_jul_actual": ene_jul_actual,
        "variacion_ene_jul": variacion_ene_jul,
        "variacion_2020_2025": variacion_2020_2025,
        "cambio_2023": cambios_anuales[anios_numero.index(2023)],
        "meses_2026_unicos": meses_2026_unicos,
        "meses": nombres_meses,
        "indice_estacional": indices_estacionales,
        "dias_semana": nombres_dias,
        "promedio_dia_semana": promedio_dia_semana,
        "meses_altos": [(mes_nombre(periodo), int(valor)) for periodo, valor in meses_altos.items()],
        "meses_bajos": [(mes_nombre(periodo), int(valor)) for periodo, valor in meses_bajos.items()],
        "trimestre_alto": (str(trimestres_completos.idxmax()).replace("Q", "-T"), int(trimestres_completos.max())),
        "trimestre_bajo": (str(trimestres_completos.idxmin()).replace("Q", "-T"), int(trimestres_completos.min())),
        "dia_pico": f"{dia_pico.day} de {nombres_meses[dia_pico.month - 1].lower()} de {dia_pico.year}",
        "registros_dia_pico": int(diario.max()),
        "mediana_diaria": float(diario_completo.median()),
        "dia_semana_alto": nombres_dias[max(range(7), key=promedio_dia_semana.__getitem__)],
        "dia_semana_bajo": nombres_dias[min(range(7), key=promedio_dia_semana.__getitem__)],
        "promedio_viernes": promedio_dia_semana[4],
        "promedio_martes": promedio_dia_semana[1],
        "promedio_domingo": promedio_dia_semana[6],
        "cesarea_viernes": round(float(porcentaje_cesarea.get(4, 0)), 1),
        "cesarea_martes": round(float(porcentaje_cesarea.get(1, 0)), 1),
        "cesarea_sabado": round(float(porcentaje_cesarea.get(5, 0)), 1),
        "cesarea_domingo": round(float(porcentaje_cesarea.get(6, 0)), 1),
        "curso_por_anio": porcentaje_curso,
        "q3_2022": int(trimestres_completos.get(pd.Period("2022Q3", freq="Q"), 0)),
        "q4_2022": int(trimestres_completos.get(pd.Period("2022Q4", freq="Q"), 0)),
        "registros_2022": int(anual.get(2022, 0)),
        "registros_2023": int(anual.get(2023, 0)),
    }
    return render_template("dimensiones/temporal.html", **contexto)
