/* Zócalo inferior: píldora blanca con mensaje en cinta. */

import { escapeHtml } from "../shared/plata_y_texto.js";

const MENSAJE_DEFAULT = "¡La mejor calidad para disfrutar en familia! ★ Los mejores precios ★ Calidad garantizada ★";

export function renderMensajeZocalo(config, marquee) {
    const crudo = (config?.mensaje_zocalo || "").trim();
    const mensaje = crudo || MENSAJE_DEFAULT;
    const negocio = (config?.business_name || "").trim();
    const texto = negocio && !mensaje.toLowerCase().includes(negocio.toLowerCase())
        ? `${mensaje} ★ Bienvenido a ${negocio} ★`
        : mensaje;
    marquee.innerHTML = `
        <span class="marquee-text">${escapeHtml(texto)} ★ </span>
        <span class="marquee-text">${escapeHtml(texto)} ★ </span>
    `;
}
