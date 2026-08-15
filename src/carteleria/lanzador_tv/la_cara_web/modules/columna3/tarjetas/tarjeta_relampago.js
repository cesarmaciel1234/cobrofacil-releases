/* Oferta relámpago a pantalla completa en TV3. */

import { escapeHtml, formatMoney, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlTarjetaRelampago(item) {
    const original = Number(item.precio_original || item.precio || 0);
    const precio = Number(item.precio || 0);
    const validez = textoValidezOferta(item);
    const nombre = String(item.nombre || "").replace(/^oferta\s+/i, "");
    return `
        <article class="flash-offer">
            <p class="flash-offer__badge">OFERTA RELÁMPAGO</p>
            <h3 class="flash-offer__name">${escapeHtml(nombre.toUpperCase())}</h3>
            <div class="flash-offer__stars">
                <span>★★★★★</span>
                <p>(⭐ ¡Favorito de todos!)</p>
            </div>
            ${original > precio ? `<s class="flash-offer__was">${formatMoney(original)}</s>` : ""}
            <strong class="flash-offer__now">${formatMoney(precio)}</strong>
            <p class="flash-offer__rule">🔥 Oferta ${escapeHtml(validez)} 🔥</p>
        </article>
    `;
}
