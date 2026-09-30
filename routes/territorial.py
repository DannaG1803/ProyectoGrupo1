"""
Dimensión territorial - Integrante 2.

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Leer los datos con cargar_datos() y pasar todo a la plantilla
templates/dimensiones/territorial.html
"""

from flask import Blueprint, render_template

from utils.datos import cargar_datos

bp = Blueprint("territorial", __name__)


@bp.route("/dimension/territorial")
def index():
    df = cargar_datos()

    contexto = {
        "titulo": "Dimensión territorial",
        "pregunta": "¿Cómo se distribuye la población y sus principales características entre los territorios disponibles?",
        "total_registros": len(df),
    }
    return render_template("dimensiones/territorial.html", **contexto)
