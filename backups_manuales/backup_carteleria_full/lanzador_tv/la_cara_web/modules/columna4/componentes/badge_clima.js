/* Badge del clima para pronóstico. */

import { escapeHtml } from "../../shared/plata_y_texto.js";

export function htmlBadgeClima(temperatura) {
    return `
        <div class="clima-badge">
            <span class="clima-temp-badge">${escapeHtml(temperatura)}</span>
            <span class="clima-dot"></span>
        </div>
    `;
}