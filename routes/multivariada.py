"""
Dimensión relacional y multivariada - Integrante 4.

Aquí va la lógica del tablero: filtros, indicadores y datos de las gráficas.
Leer los datos con cargar_datos() y pasar todo a la plantilla
templates/dimensiones/multivariada.html
"""

from flask import Blueprint, render_template

from utils.datos import cargar_datos

bp = Blueprint("multivariada", __name__)


@bp.route("/dimension/multivariada")
def index():
    df = cargar_datos()

    contexto = {
        "titulo": "Dimensión relacional y multivariada",
        "pregunta": "¿Qué diferencias o relaciones evidentes pueden identificarse al analizar conjuntamente tres o más variables?",
        "total_registros": len(df),
    }
    return render_template("dimensiones/multivariada.html", **contexto)
