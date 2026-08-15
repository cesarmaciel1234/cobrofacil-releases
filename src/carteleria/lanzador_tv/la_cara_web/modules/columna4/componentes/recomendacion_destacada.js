/* Recomendación destacada para pronóstico. */

import { escapeHtml, formatMoney } from "../../shared/plata_y_texto.js";

export function htmlRecomendacionDestacada(producto, precio) {
    return `
        <div class="pronostico-recomendacion">
            <p class="recomendacion-texto-full">${escapeHtml(producto)}</p>
            <p class="recomendacion-precio-full">${formatMoney(precio)}</p>
        </div>
    `;
}