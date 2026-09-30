"""
Limpieza del archivo original de nacimientos descargado de datos.gov.co.

El Excel que se descarga del portal trae un problema: todo el CSV quedó
metido en una sola columna, con las tildes dañadas (UTF-8 leído como
Windows-1252) y cada registro repetido cinco veces. Este script lo deja
listo en data/nacimientos.csv para que toda la app trabaje con el mismo
archivo limpio.

Uso (desde la raíz del proyecto):
    python scripts/preparar_datos.py
"""

import csv
import io
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_ORIGINAL = RAIZ / "data" / "raw" / "NACIMIENTOS_20260930.xlsx"
ARCHIVO_LIMPIO = RAIZ / "data" / "nacimientos.csv"

# Nombres cortos para las columnas, así es más fácil usarlos en pandas
# y en las plantillas. El orden es el mismo del archivo original.
COLUMNAS = {
    "IDENTIFICADOR": "id",
    "DEPARTAMENTO": "departamento",
    "MUNICIPIO": "municipio",
    "AREA NACIMIENTO": "area_nacimiento",
    "SITIO NACIMIENTO": "sitio_nacimiento",
    "CÓDIGO INSTITUCIÓN": "codigo_institucion",
    "NOMBRE INSTITUCIÓN": "institucion",
    "SEXO": "sexo",
    "PESO (Gramos)": "peso_gramos",
    "TALLA (Centímetros)": "talla_cm",
    "FECHA NACIMIENTO": "fecha_nacimiento",
    "PARTO ATENDIDO POR": "parto_atendido_por",
    "TIEMPO DE GESTACIÓN": "semanas_gestacion",
    "NÚMERO CONSULTAS PRENATALES": "consultas_prenatales",
    "TIPO PARTO": "tipo_parto",
    "FACTOR RH": "factor_rh",
    "PERTENENCIA ÉTNICA": "pertenencia_etnica",
    "GRUPO INDIGENA": "grupo_indigena",
    "TIPO DOCUMENTO MADRE": "tipo_documento_madre",
    "EDAD MADRE": "edad_madre",
    "ESTADO CONYUGAL MADRE": "estado_conyugal_madre",
    "NIVEL EDUCATIVO MADRE": "nivel_educativo_madre",
    "ULTIMO AÑO APROBADO MADRE": "ultimo_anio_aprobado_madre",
    "PAÍS RESIDENCIA": "pais_residencia",
    "DEPARTAMENTO RESIDENCIA": "departamento_residencia",
    "MUNICIPIO RESIDENCIA": "municipio_residencia",
    "AREA RESIDENCIA": "area_residencia",
    "LOCALIDAD": "localidad",
    "NÚMERO HIJOS NACIDOS VIVOS": "hijos_nacidos_vivos",
    "NÚMERO EMBARAZOS": "numero_embarazos",
    "RÉGIMEN SEGURIDAD": "regimen_seguridad",
    "TIPO ADMINISTRADORA": "tipo_administradora",
    "NOMBRE ADMINISTRADORA": "administradora",
    "EDAD PADRE": "edad_padre",
    "NIVEL EDUCATIVO PADRE": "nivel_educativo_padre",
    "ULTIMO AÑO APROBADO PADRE": "ultimo_anio_aprobado_padre",
    "MES": "mes",
    "NOMBRE COMUNA": "comuna",
    "CURSO DE VIDA MADRE": "curso_vida_madre",
    "AÑO REPORTE": "anio",
}

COLUMNAS_NUMERICAS = [
    "id", "peso_gramos", "talla_cm", "semanas_gestacion", "consultas_prenatales",
    "edad_madre", "ultimo_anio_aprobado_madre", "hijos_nacidos_vivos",
    "numero_embarazos", "edad_padre", "ultimo_anio_aprobado_padre", "anio",
]

# Desde 2023 el formulario cambió y algunas respuestas vienen redactadas
# distinto ("ESTABA CASADO(A)" en vez de "ESTÁ CASADA"). Se dejan en una
# sola categoría para poder comparar años.
ESTADO_CONYUGAL = {
    "NO ESTABA CASADO(A) Y LLEVABA DOS AÑOS O MÁS VIVIENDO CON SU PAREJA": "UNIÓN LIBRE (2 AÑOS O MÁS)",
    "NO ESTÁ CASADA Y LLEVA DOS AÑOS O MÁS VIVIENDO CON SU PAREJA": "UNIÓN LIBRE (2 AÑOS O MÁS)",
    "NO ESTABA CASADO(A) Y LLEVABA MENOS DE DOS AÑOS VIVIENDO CON SU PAREJA": "UNIÓN LIBRE (MENOS DE 2 AÑOS)",
    "NO ESTÁ CASADA Y LLEVA MENOS DE DOS AÑOS VIVIENDO CON SU PAREJA": "UNIÓN LIBRE (MENOS DE 2 AÑOS)",
    "ESTABA SOLTERO(A)": "SOLTERA",
    "ESTÁ SOLTERA": "SOLTERA",
    "ESTABA CASADO(A)": "CASADA",
    "ESTÁ CASADA": "CASADA",
    "ESTÁ SEPARADA, DIVORCIADA": "SEPARADA / DIVORCIADA",
    "ESTABA VIUDO(A)": "VIUDA",
    "ESTÁ VIUDA": "VIUDA",
}

MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO",
         "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]


def reparar_tildes(texto):
    """Devuelve el texto a UTF-8 (ej: 'CÃ‰DULA' -> 'CÉDULA')."""
    bytes_originales = bytearray()
    for caracter in texto:
        try:
            bytes_originales += caracter.encode("cp1252")
        except UnicodeEncodeError:
            # Bytes que cp1252 no tiene definidos (0x81, 0x8D...) quedaron
            # como caracteres de control; se recuperan tal cual.
            bytes_originales.append(ord(caracter))
    return bytes_originales.decode("utf-8")


def reparar_identificador(linea):
    """
    Los ID mayores a 999 vienen con separador de miles y sin comillas
    (1,616,"SANTANDER"...), lo que parte la fila en una columna de más.
    """
    coincidencia = re.match(r'^([\d,]+?),"', linea)
    if not coincidencia:
        return linea
    return coincidencia.group(1).replace(",", "") + linea[coincidencia.end(1):]


def leer_archivo_original():
    lineas = pd.read_excel(ARCHIVO_ORIGINAL, header=None, dtype=str)[0]
    texto = "\n".join(reparar_tildes(reparar_identificador(l)) for l in lineas)
    return pd.read_csv(io.StringIO(texto), dtype=str)


def unificar_escritura(serie):
    """
    Algunas filas traen las categorías sin espacios ('CABECERAMUNICIPAL')
    o con punto al final ('CÉDULA DE CIUDADANÍA.'). Se agrupan por su forma
    "comprimida" y se reemplazan por la versión más frecuente.
    """
    serie = serie.str.strip().str.rstrip(".")
    clave = serie.str.replace(" ", "", regex=False)
    frecuencias = serie.value_counts()
    canonica = {}
    for valor in frecuencias.index:  # ya vienen ordenados de mayor a menor
        canonica.setdefault(valor.replace(" ", ""), valor)
    return clave.map(canonica)


def limpiar(df):
    df = df.rename(columns=COLUMNAS)

    # Cada nacimiento aparece 5 veces idéntico en la descarga
    df = df.drop_duplicates().copy()

    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False), errors="coerce").astype("Int64")

    categoricas = [c for c in df.columns if c not in COLUMNAS_NUMERICAS + ["fecha_nacimiento", "codigo_institucion"]]
    for col in categoricas:
        df[col] = unificar_escritura(df[col])

    df["sexo"] = df["sexo"].replace({"M": "MASCULINO", "F": "FEMENINO"})
    df["estado_conyugal_madre"] = df["estado_conyugal_madre"].replace(ESTADO_CONYUGAL)
    df["grupo_indigena"] = df["grupo_indigena"].replace({"WAYU": "WAYUU"})

    # A partir de 2023 la columna FACTOR RH empezó a traer la multiplicidad
    # del embarazo (SIMPLE, DOBLE, TRIPLE). Se separa en dos columnas.
    multiplicidad = df["factor_rh"].where(df["factor_rh"].isin(["SIMPLE", "DOBLE", "TRIPLE"]))
    df["factor_rh"] = df["factor_rh"].where(df["factor_rh"].isin(["POSITIVO", "NEGATIVO"]))
    df.insert(df.columns.get_loc("factor_rh") + 1, "multiplicidad_embarazo", multiplicidad)

    fechas = pd.to_datetime(df["fecha_nacimiento"], format="%Y %b %d %I:%M:%S %p", errors="coerce")
    df["fecha_nacimiento"] = fechas.dt.strftime("%Y-%m-%d")
    df.insert(df.columns.get_loc("mes") + 1, "mes_numero", df["mes"].map({m: i for i, m in enumerate(MESES, 1)}).astype("Int64"))

    # El código de institución viene redondeado en el origen (680,010,000,000)
    # así que no sirve como llave; se deja solo el nombre de la institución.
    df = df.drop(columns=["codigo_institucion"])

    return df.sort_values("id").reset_index(drop=True)


def main():
    print(f"Leyendo {ARCHIVO_ORIGINAL.name} ...")
    original = leer_archivo_original()
    print(f"  filas en el archivo original: {len(original):,}")

    limpio = limpiar(original)
    limpio.to_csv(ARCHIVO_LIMPIO, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    print(f"  registros únicos: {len(limpio):,}")
    print(f"  variables: {limpio.shape[1]}")
    print(f"Archivo generado: {ARCHIVO_LIMPIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
