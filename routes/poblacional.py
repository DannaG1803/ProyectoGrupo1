"""
Dimensión poblacional - Integrante 1.

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Leer los datos con cargar_datos() y pasar todo a la plantilla
templates/dimensiones/poblacional.html
"""

from flask import Blueprint, render_template

from utils.datos import cargar_datos

bp = Blueprint("poblacional", __name__)


@bp.route("/dimension/poblacional")
def index():
    df = cargar_datos()

    contexto = {
        "titulo": "Dimensión poblacional",
        "pregunta": "¿Cómo está compuesta y distribuida la población analizada según sus principales características?",
        "total_registros": len(df),
    }
    return render_template("dimensiones/poblacional.html", **contexto)
