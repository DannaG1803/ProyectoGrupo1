# Proyecto de análisis exploratorio de datos con Flask y Bootstrap.

Análisis exploratorio de los **nacimientos registrados en Bucaramanga (2020 - 2026)**,
con datos descargados del Portal Nacional de Datos Abiertos de Colombia (datos.gov.co).

## Equipo
- Integrante 1: Danna Gonzalez - Dimensión poblacional / Administración del repositorio
- Integrante 2: Sergio Luis Gómez Ramírez - Dimensión territorial / Configuración Flask
- Integrante 3: Andrés Felipe Beltrán Barrera - Dimensión temporal / Publicación
- Integrante 4: Ana María Cortés Prieto - Dimensión relacional / Informe

## Estructura del proyecto

```
ProyectoGrupo1/
├── app.py                      # Aplicación Flask: inicio, menú y registro de rutas
├── requirements.txt            # Dependencias
├── README.md
├── .gitignore
├── data/
│   ├── raw/
│   │   └── NACIMIENTOS_20260930.xlsx   # Archivo original descargado del portal
│   └── nacimientos.csv                 # Dataset limpio que usa la app
├── scripts/
│   └── preparar_datos.py       # Convierte el archivo original en nacimientos.csv
├── utils/
│   └── datos.py                # cargar_datos(), descripción de variables y fuente
├── routes/                     # Un archivo (Blueprint) por dimensión
│   ├── poblacional.py          # Integrante 1
│   ├── territorial.py          # Integrante 2
│   ├── temporal.py             # Integrante 3
│   └── multivariada.py         # Integrante 4
├── templates/
│   ├── base.html               # Plantilla principal (Bootstrap, menú lateral, footer)
│   ├── index.html              # Página de inicio
│   ├── 404.html
│   ├── _macros.html            # Componentes: indicador, visualización, conocimiento
│   ├── partials/
│   │   ├── sidebar.html        # Menú lateral con los módulos
│   │   └── footer.html         # Nombre del proyecto y Universidad de Cundinamarca
│   └── dimensiones/
│       ├── _estructura.html    # Estructura común de los tableros
│       ├── poblacional.html
│       ├── territorial.html
│       ├── temporal.html
│       └── multivariada.html
└── static/
    ├── css/estilos.css         # Identidad visual
    ├── js/main.js              # Paleta de colores y configuración de Chart.js
    └── img/
```

## Cómo ejecutar el proyecto en local

Requisitos: Python 3.11 o superior y Git.

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone https://github.com/DannaG1803/ProyectoGrupo1.git
   cd ProyectoGrupo1
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / Mac
   source venv/bin/activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:

   ```bash
   python app.py
   ```

5. Abrir en el navegador: <http://127.0.0.1:5000>

### Rutas disponibles

| Página | URL |
|---|---|
| Inicio | `/` |
| Dimensión poblacional | `/dimension/poblacional` |
| Dimensión territorial | `/dimension/territorial` |
| Dimensión temporal | `/dimension/temporal` |
| Dimensión relacional y multivariada | `/dimension/multivariada` |

## Sobre los datos

El Excel descargado del portal trae todo el CSV en una sola columna, las tildes dañadas
y cada registro repetido 5 veces (34.309 filas → **7.016 nacimientos únicos**).
El script `scripts/preparar_datos.py` corrige esto y genera `data/nacimientos.csv`.
Solo hay que volver a ejecutarlo si se cambia el archivo original:

```bash
python scripts/preparar_datos.py
```

Además de la limpieza, el script:
- Renombra las columnas a nombres cortos (`edad_madre`, `municipio_residencia`, `anio`...).
- Unifica categorías escritas sin espacios o con punto final (`CABECERAMUNICIPAL`, `CÉDULA DE CIUDADANÍA.`).
- Unifica `SEXO` (M/F → MASCULINO/FEMENINO) y el estado conyugal, que cambió de redacción en 2023.
- Separa la columna `FACTOR RH`, que desde 2023 trae la multiplicidad del embarazo
  (SIMPLE/DOBLE/TRIPLE), en `factor_rh` y `multiplicidad_embarazo`.
- Agrega `mes_numero` y deja la fecha en formato `AAAA-MM-DD`.

## Cómo trabajar una dimensión

Cada integrante trabaja **solo en sus dos archivos**, así no hay conflictos al unir las ramas:

- `routes/<dimension>.py` → cálculos con pandas (filtros, indicadores, datos de las gráficas).
- `templates/dimensiones/<dimension>.html` → contenido del tablero.

La plantilla de cada dimensión hereda de `_estructura.html`, que ya trae todas las secciones
que pide la guía. Solo se reemplazan los bloques necesarios:

| Bloque | Contenido |
|---|---|
| `variables` | Descripción de las variables utilizadas |
| `filtros` | Los dos filtros interactivos (formulario GET) |
| `indicadores` | Tres indicadores (`ui.indicador`) |
| `visualizaciones` | Tres gráficas con su interpretación (`ui.visualizacion`) |
| `conocimientos` | Tres conocimientos evidentes (`ui.conocimiento`) |
| `limitacion` | Limitación del análisis |
| `decision` | Decisión sustentada en los datos |
| `graficas` | JavaScript de Chart.js que dibuja las gráficas |

Ejemplo corto:

```python
# routes/territorial.py
@bp.route("/dimension/territorial")
def index():
    df = cargar_datos()
    area = request.args.get("area", "")
    if area:
        df = df[df["area_residencia"] == area]
    top = df["municipio_residencia"].value_counts().head(10)
    return render_template("dimensiones/territorial.html",
                           titulo="Dimensión territorial", pregunta="...",
                           total_registros=len(df),
                           etiquetas=top.index.tolist(), valores=top.tolist())
```

```html
{% extends "dimensiones/_estructura.html" %}

{% block graficas %}
<script>
new Chart(document.getElementById("grafica1"), {
    type: "bar",
    data: {
        labels: {{ etiquetas | tojson }},
        datasets: [{ label: "Nacimientos", data: {{ valores | tojson }}, backgroundColor: PALETA[0] }]
    }
});
</script>
{% endblock %}
```

## Dimensión poblacional (Integrante 1)

Pregunta de análisis: *¿Cómo está compuesta y distribuida la población analizada según sus principales características?*

Archivos: `routes/poblacional.py` (cálculos con pandas y textos del análisis) y
`templates/dimensiones/poblacional.html` (tablero). Se ve en `/dimension/poblacional`.

| Elemento | Contenido |
|---|---|
| Filtros | Año de reporte e institución |
| Indicadores | Total de registros, edad promedio de la madre y % de madres en régimen subsidiado |
| Visualizaciones | Dona de régimen de seguridad, barras de nivel educativo de la madre e histograma de edad de la madre |
| Perfil general | Tabla con el grupo predominante y el minoritario de sexo, tipo de parto, curso de vida, estado conyugal, documento e institución |
| Conocimientos evidentes | Régimen de salud, edad y adolescencia, nivel educativo (con las 8 partes que pide la guía) |
| Limitación y decisión | Cobertura de solo dos instituciones públicas y propuesta de afiliación durante la atención prenatal |

Las cifras de los textos se calculan con los datos filtrados, así siempre coinciden con las gráficas.

## Dimensión territorial (Integrante 2)

Pregunta de análisis: *¿Cómo se distribuye la población y sus principales características entre los territorios disponibles?*

Archivos: `routes/territorial.py` (cálculos con pandas y textos del análisis) y
`templates/dimensiones/territorial.html` (tablero). Se ve en `/dimension/territorial`.

| Elemento | Contenido |
|---|---|
| Filtros | Año de reporte y área de residencia |
| Indicadores | Municipios de residencia, participación del territorio con más registros y % de madres de fuera de Santander |
| Visualizaciones | Barras de los 10 municipios principales, barras de comunas de Bucaramanga y barras agrupadas con % de cesárea, % de no aseguradas y % de residencia rural por municipio |
| Participación | Tabla con todos los municipios, su departamento, % y % acumulado |
| Conocimientos evidentes | Concentración territorial, distribución por comunas y diferencias entre municipios |
| Limitación y decisión | El territorio es la residencia de la madre en solo dos instituciones; propuesta de priorizar la comuna con más nacimientos y coordinar con los municipios vecinos |

Notas sobre los datos territoriales:
- La comuna se digita a mano. Se unifican las variantes (`MORRORRICO`, `MORORRICO` → `MORRORICO`, etc.)
  y lo que no corresponde a una de las 17 comunas oficiales se agrupa en zona rural u otros barrios.
- `CACHIRÁ` y `CÁCHIRA` son el mismo municipio y se cuentan juntos.
- La comparación entre municipios solo incluye los que tienen 30 o más registros, para que los porcentajes sean estables.

## Flujo de trabajo en GitHub

1. Actualizar `main`: `git checkout main && git pull`
2. Crear la rama: `git checkout -b feature/dimension-<nombre>`
3. Hacer commits descriptivos (mínimo tres).
4. Subir la rama: `git push -u origin feature/dimension-<nombre>`
5. Crear el pull request hacia `main` y pedir revisión al integrante 1.
