/*
   Configuración común para las gráficas de Chart.js.
   Usar PALETA en todas las dimensiones para mantener los mismos colores.

   Ejemplo:
     new Chart(document.getElementById("grafica1"), {
         type: "bar",
         data: { labels: [...], datasets: [{ data: [...], backgroundColor: PALETA[0] }] }
     });
*/
const PALETA = [
    "#0f6e7a", // principal
    "#e07a5f", // acento
    "#3d5a80",
    "#81b29a",
    "#f2cc8f",
    "#98c1d9",
    "#6d597a",
    "#b56576",
];

if (window.Chart) {
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    Chart.defaults.color = "#495057";
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.plugins.legend.position = "bottom";
}

// Envía automáticamente el formulario de filtros cuando cambia un <select>.
// Basta con ponerle la clase "filtro-auto" al <form>.
document.querySelectorAll("form.filtro-auto select").forEach((select) => {
    select.addEventListener("change", () => select.form.submit());
});
