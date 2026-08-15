/* Venta cruzada: ¿LLEVÁS X? + llevá también. */

import { escapeHtml } from "../../shared/plata_y_texto.js";

export function htmlTarjetaCruzada(slide) {
    const items = (slide.relacionados || []).slice(0, 3)
        .map((nombre) => `<li>${escapeHtml(nombre)}</li>`)
        .join("");
    return `
        <article class="xsell-card">
            <h3 class="xsell-ask">${escapeHtml(slide.pregunta || "")}</h3>
            <p class="xsell-cta">👈 LLEVÁ TAMBIÉN 👉</p>
            <ul class="xsell-list">${items}</ul>
        </article>
    `;
}
