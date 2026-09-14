/* Combo: misma tarjeta híbrida que el carrusel. */

import { descuentoPct, escapeHtml, formatMoney, textoValidezOferta, unidadProducto } from "../../shared/plata_y_texto.js";

export function htmlTarjetaCombo(combo) {
    const ahorro = Number(combo.ahorro || 0);
    const original = Number(combo.precio_original || 0);
    const precio = Number(combo.precio || 0);
    const pct = descuentoPct(original, precio);
    const validez = textoValidezOferta(combo);
    return `
        <article class="tv-card meal-card is-flash">
            <div class="tv-card__top">
                <h4 class="tv-card__name meal-name">${escapeHtml(combo.nombre)}</h4>
                ${pct ? `<span class="tv-card__off">-${pct}%</span>` : ""}
            </div>
            <div class="tv-card__pay">
                ${original > precio ? `<div class="tv-card__was-row"><s class="tv-card__was">${formatMoney(original)}</s>${validez ? `<span class="tv-card__rule">${escapeHtml(validez)}</span>` : ""}</div>` : ""}
                <div class="tv-card__now-row">
                    <strong class="tv-card__now">${formatMoney(combo.precio)}</strong>
                    ${ahorro > 0 ? `<span class="tv-card__save"><span class="tv-card__save-label">AHORRÁS</span><strong class="tv-card__save-amt">${formatMoney(ahorro)} x ${unidadProducto(combo)}</strong></span>` : ""}
                </div>
            </div>
        </article>
    `;
}
