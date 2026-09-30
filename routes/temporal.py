"""
Dimensión temporal - Integrante 3.

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Leer los datos con cargar_datos() y pasar todo a la plantilla
templates/dimensiones/temporal.html
"""

from flask import Blueprint, render_template

from utils.datos import cargar_datos

bp = Blueprint("temporal", __name__)


@bp.route("/dimension/temporal")
def index():
    df = cargar_datos()

    contexto = {
        "titulo": "Dimensión temporal",
        "pregunta": "¿Cómo ha cambiado el comportamiento de la población durante el periodo disponible?",
        "total_registros": len(df),
    }
    return render_template("dimensiones/temporal.html", **contexto)
