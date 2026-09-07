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
            <header class="rank-head sale-head">
                <p class="rank-kicker">OFERTAS</p>
            </header>
            <div class="flash-offer__deal">
                ${htmlDealStage({ ...item, nombre }, {
                    off: pct ? `-${pct}%` : "",
                    extraClass: "flash-offer__stage",
                    titulo: nombre,
                    bolt: false,
                })}
                <div class="deal-copy flash-offer__copy" style="background:#0A0602">
                    <p class="deal-kicker">Precio de hoy</p>
                    <div class="deal-price-row">
                        ${precio > 0
                            ? `<strong class="tv-card__now" style="background:linear-gradient(135deg,#FFDF00,#FFA500);color:#550000;-webkit-text-fill-color:#550000;border-radius:8px;padding:0.08em 0.35em;border:2px solid #fff"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>`
                            : ""}
                        ${original > precio ? `<s class="tv-card__was">${formatMoney(original)}</s>` : ""}
                    </div>
                    <p class="deal-save">${escapeHtml(textoValidezOferta(item))}</p>
                </div>
            </div>
        </article>
    `;
}
