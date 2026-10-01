const temporalDataElement = document.getElementById("datosTemporales");
const temporalDataJson = temporalDataElement?.textContent;

if (!temporalDataJson) {
    throw new Error("No se encontraron los datos de la dimensión temporal.");
}

const {
    anios,
    registros,
    periodos,
    meses,
    indices,
    dias,
    promedioDias,
} = JSON.parse(temporalDataJson);

new Chart(document.getElementById("graficaAnual"), {
    type: "bar",
    data: {
        labels: anios,
        datasets: [{
            label: "Registros",
            data: registros,
            backgroundColor: [PALETA[0], PALETA[0], PALETA[0], PALETA[1], PALETA[0], PALETA[0], PALETA[4]],
        }],
    },
    options: { scales: { y: { beginAtZero: true, title: { display: true, text: "Registros" } } } },
});

const aniosComparables = Object.keys(periodos);
new Chart(document.getElementById("graficaPeriodos"), {
    type: "line",
    data: {
        labels: aniosComparables,
        datasets: [
            {
                label: "Enero–marzo",
                data: aniosComparables.map((anio) => periodos[anio][0]),
                borderColor: PALETA[0],
                backgroundColor: PALETA[0],
                tension: 0.25,
            },
            {
                label: "Enero–julio",
                data: aniosComparables.map((anio) => periodos[anio][1]),
                borderColor: PALETA[1],
                backgroundColor: PALETA[1],
                tension: 0.25,
            },
        ],
    },
    options: { scales: { y: { beginAtZero: true, title: { display: true, text: "Registros" } } } },
});

new Chart(document.getElementById("graficaEstacional"), {
    type: "bar",
    data: {
        labels: meses,
        datasets: [{
            label: "Índice estacional",
            data: indices,
            backgroundColor: indices.map((valor) => valor >= 1 ? PALETA[0] : PALETA[2]),
        }],
    },
    options: {
        scales: {
            y: {
                min: 0.7,
                max: 1.2,
                title: { display: true, text: "1,00 = promedio anual" },
            },
        },
    },
});

new Chart(document.getElementById("graficaSemana"), {
    type: "bar",
    data: {
        labels: dias,
        datasets: [{ label: "Registros por día", data: promedioDias, backgroundColor: PALETA[3] }],
    },
    options: {
        scales: { y: { beginAtZero: true, title: { display: true, text: "Promedio diario" } } },
        plugins: { legend: { display: false } },
    },
});