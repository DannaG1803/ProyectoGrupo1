"""
Funciones para cargar el dataset limpio desde cualquier parte de la app.

Todas las dimensiones deben leer los datos con cargar_datos() en vez de
abrir el CSV por su cuenta, así todos trabajamos con la misma versión.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "nacimientos.csv"

# Información del conjunto de datos (se muestra en la página de inicio)
FUENTE = {
    "nombre": "Nacimientos",
    "entidad": "Alcaldía de Bucaramanga - Secretaría de Salud y Ambiente",
    "portal": "Portal Nacional de Datos Abiertos de Colombia",
    "url": "https://www.datos.gov.co/",
    "poblacion": "Nacidos vivos atendidos en la red pública de Bucaramanga (Hospital Local del Norte y "
                 "Unidad Materno Infantil Santa Teresita) entre 2020 y 2026.",
}

# Descripción de las variables que más se usan en el análisis
VARIABLES = [
    {"columna": "anio", "nombre": "Año de reporte", "tipo": "Temporal", "descripcion": "Año en que se reportó el nacimiento."},
    {"columna": "fecha_nacimiento", "nombre": "Fecha de nacimiento", "tipo": "Temporal", "descripcion": "Día del nacimiento (AAAA-MM-DD)."},
    {"columna": "mes", "nombre": "Mes", "tipo": "Temporal", "descripcion": "Mes del nacimiento."},
    {"columna": "municipio_residencia", "nombre": "Municipio de residencia", "tipo": "Territorial", "descripcion": "Municipio donde vive la madre."},
    {"columna": "departamento_residencia", "nombre": "Departamento de residencia", "tipo": "Territorial", "descripcion": "Departamento donde vive la madre."},
    {"columna": "area_residencia", "nombre": "Área de residencia", "tipo": "Territorial", "descripcion": "Cabecera municipal, centro poblado o rural disperso."},
    {"columna": "comuna", "nombre": "Comuna", "tipo": "Territorial", "descripcion": "Comuna o zona de residencia de la madre."},
    {"columna": "institucion", "nombre": "Institución", "tipo": "Categórica", "descripcion": "Hospital donde ocurrió el nacimiento."},
    {"columna": "sexo", "nombre": "Sexo", "tipo": "Categórica", "descripcion": "Sexo del recién nacido."},
    {"columna": "tipo_parto", "nombre": "Tipo de parto", "tipo": "Categórica", "descripcion": "Espontáneo, cesárea o instrumentado."},
    {"columna": "regimen_seguridad", "nombre": "Régimen de salud", "tipo": "Categórica", "descripcion": "Subsidiado, contributivo, especial o no asegurado."},
    {"columna": "nivel_educativo_madre", "nombre": "Nivel educativo de la madre", "tipo": "Categórica", "descripcion": "Último nivel educativo alcanzado por la madre."},
    {"columna": "estado_conyugal_madre", "nombre": "Estado conyugal de la madre", "tipo": "Categórica", "descripcion": "Situación de pareja de la madre."},
    {"columna": "curso_vida_madre", "nombre": "Curso de vida de la madre", "tipo": "Categórica", "descripcion": "Adolescencia, juventud o adultez."},
    {"columna": "tipo_documento_madre", "nombre": "Documento de la madre", "tipo": "Categórica", "descripcion": "Tipo de documento (permite ver madres extranjeras)."},
    {"columna": "peso_gramos", "nombre": "Peso", "tipo": "Numérica", "descripcion": "Peso al nacer en gramos."},
    {"columna": "talla_cm", "nombre": "Talla", "tipo": "Numérica", "descripcion": "Talla al nacer en centímetros."},
    {"columna": "semanas_gestacion", "nombre": "Semanas de gestación", "tipo": "Numérica", "descripcion": "Duración del embarazo en semanas."},
    {"columna": "consultas_prenatales", "nombre": "Consultas prenatales", "tipo": "Numérica", "descripcion": "Número de controles prenatales."},
    {"columna": "edad_madre", "nombre": "Edad de la madre", "tipo": "Numérica", "descripcion": "Edad de la madre en años."},
    {"columna": "edad_padre", "nombre": "Edad del padre", "tipo": "Numérica", "descripcion": "Edad del padre en años."},
    {"columna": "numero_embarazos", "nombre": "Número de embarazos", "tipo": "Numérica", "descripcion": "Embarazos que ha tenido la madre."},
]


@lru_cache(maxsize=1)
def _leer_csv():
    return pd.read_csv(RUTA_DATOS, parse_dates=["fecha_nacimiento"])


def cargar_datos():
    """
    Devuelve el DataFrame de nacimientos.
    El CSV se lee una sola vez; cada llamada entrega una copia para que
    los filtros de una página no afecten a las demás.
    """
    return _leer_csv().copy()


def opciones(df, columna):
    """Valores únicos y ordenados de una columna, útil para llenar los <select> de los filtros."""
    return sorted(df[columna].dropna().unique().tolist())


def resumen_general():
    """Cifras generales del dataset para la página de inicio."""
    df = cargar_datos()
    return {
        "registros": len(df),
        "variables": df.shape[1],
        "anio_min": int(df["anio"].min()),
        "anio_max": int(df["anio"].max()),
        "fecha_min": df["fecha_nacimiento"].min().strftime("%d/%m/%Y"),
        "fecha_max": df["fecha_nacimiento"].max().strftime("%d/%m/%Y"),
        "municipios": df["municipio_residencia"].nunique(),
        "comunas": df["comuna"].nunique(),
        "instituciones": df["institucion"].nunique(),
    }
