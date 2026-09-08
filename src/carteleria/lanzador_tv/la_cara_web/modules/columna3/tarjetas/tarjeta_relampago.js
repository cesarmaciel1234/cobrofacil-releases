/* Relámpago TV3: deal card vertical, igual al carrusel. */

import {
    descuentoPct,
    escapeHtml,
    formatMoney,
    htmlDealStage,
    nombreVitrina,
    textoValidezOferta,
} from "../../shared/plata_y_texto.js";

export function htmlTarjetaRelampago(item) {
    const original = Number(item.precio_original || item.precio || 0);
    const precio = Number(item.precio || 0);
    const nombre = nombreVitrina(item.nombre);
    const pct = descuentoPct(original, precio);
    const monto = precio > 0 ? formatMoney(precio).replace(/^\$\s*/, "") : "";
    return `
        <article class="flash-offer">
            <div class="flash-offer__deal">
                ${htmlDealStage({ ...item, nombre }, {
                    off: pct ? `-${pct}%` : "",
                    extraClass: "flash-offer__stage",
                    titulo: nombre,
                    bolt: false,
                })}
                <div class="deal-copy flash-offer__copy" style="background:#0A0602">
                    <h3 class="tv-card__name deal-line">${escapeHtml(nombre)}</h3>
                    <div class="deal-price-row deal-line">
                        ${precio > 0 ? `
                        <div class="tv-card__now-box">
                            <strong class="tv-card__now"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>
                            ${original > precio ? `<s class="tv-card__was">${formatMoney(original)}</s>` : ""}
                        </div>` : ""}
                    </div>
                    <p class="deal-save deal-line">${escapeHtml(textoValidezOferta(item))}</p>
                </div>
            </div>
        </article>
    `;
}
