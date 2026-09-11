/* Un solo bloque de precio + tachado + condición para todas las columnas. */

import { escapeHtml, formatMoney, leerPrecios, textoValidezOferta } from "./plata_y_texto.js";

export function htmlFilaOfertaTv(item, opts = {}) {
    const { vigente, original, hayOferta } = leerPrecios(item);
    const regla = textoValidezOferta(item);
    const caja = opts.caja || "tv-card__now-box";
    const ahoraClase = opts.ahora || "tv-card__now";
    const antesClase = opts.antes || "tv-card__was";
    const reglaClase = opts.regla || "deal-save";
    const reglaTag = opts.reglaTag || "p";
    const monto = vigente > 0 ? formatMoney(vigente).replace(/^\$\s*/, "") : "";
    const tachado = hayOferta
        ? `<s class="${antesClase}">${escapeHtml(formatMoney(original).replace(/\s+/g, ""))}</s>`
        : "";
    const condicion = regla
        ? `<${reglaTag} class="${reglaClase}">${escapeHtml(regla)}</${reglaTag}>`
        : "";
    const ahora = vigente > 0
        ? `<strong class="${ahoraClase}"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>`
        : "";
    if (!ahora && !tachado) return "";
    return `
        <div class="${caja} tv-precio">
            ${ahora}
            ${tachado}
        </div>
        ${condicion}
    `;
}
