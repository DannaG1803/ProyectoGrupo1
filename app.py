"""....
Aplicación principal del proyecto: Análisis exploratorio de nacimientos
en Bucaramanga (datos.gov.co).

Para ejecutar en local:
    python app.py
y abrir http://127.0.0.1:5000
"""

from flask import Flask, render_template

from routes import BLUEPRINTS
from utils.datos import FUENTE, VARIABLES, resumen_general

app = Flask(__name__)

for blueprint in BLUEPRINTS:
    app.register_blueprint(blueprint)

# Menú de "Análisis de datos". Si se agrega una dimensión nueva basta con
# ponerla aquí y aparece en el menú lateral y en las tarjetas del inicio.
DIMENSIONES = [
    {
        "endpoint": "poblacional.index",
        "nombre": "Dimensión poblacional",
        "icono": "bi-people",
        "descripcion": "Composición y distribución de los nacimientos según sus principales características.",
        "integrante": "Integrante 1",
    },
    {
        "endpoint": "territorial.index",
        "nombre": "Dimensión territorial",
        "icono": "bi-geo-alt",
        "descripcion": "Distribución de los nacimientos por municipio, comuna y área de residencia.",
        "integrante": "Integrante 2",
    },
    {
        "endpoint": "temporal.index",
        "nombre": "Dimensión temporal",
        "icono": "bi-calendar3",
        "descripcion": "Evolución de los nacimientos por año y mes entre 2020 y 2026.",
        "integrante": "Integrante 3",
    },
    {
        "endpoint": "multivariada.index",
        "nombre": "Dimensión relacional y multivariada",
        "icono": "bi-diagram-3",
        "descripcion": "Relaciones y diferencias al cruzar tres o más variables.",
        "integrante": "Integrante 4",
    },
]


@app.context_processor
def datos_globales():
    # Queda disponible en todas las plantillas (menú lateral y footer)
    return {"dimensiones": DIMENSIONES, "fuente": FUENTE}


@app.template_filter("miles")
def formato_miles(valor):
    # 7016 -> "7.016" (separador de miles como se usa en Colombia)
    return f"{valor:,.0f}".replace(",", ".")


@app.route("/")
def inicio():
    return render_template("index.html", resumen=resumen_general(), variables=VARIABLES)


@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
