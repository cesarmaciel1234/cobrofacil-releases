/* Mensaje personalizado para pronóstico. */

import { escapeHtml } from "../../shared/plata_y_texto.js";

export function htmlMensajePersonalizado(mensaje) {
    return `
        <p class="pronostico-mensaje-full">${escapeHtml(mensaje)}</p>
    `;
}