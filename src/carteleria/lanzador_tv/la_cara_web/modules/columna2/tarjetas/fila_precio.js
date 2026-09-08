/* Grilla de precios: misma lectura que las tarjetas de publicidad. */

import { descuentoPct, escapeHtml, esOferta, formatMoney, nombreVitrina, precioVigente, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlFilaPrecio(item, puesto = 1, depto = "") {
    const vigente = precioVigente(item);
    const oferta = esOferta(item);

    let precioOriginal = item.precio_original || item.precio_anterior || item.precio || vigente;
    if (precioOriginal <= vigente && vigente > 0) {
        precioOriginal = Math.round(vigente * 1.2);
    }

    const pct = descuentoPct(precioOriginal, vigente);
    const regla = textoValidezOferta(item);

    return `
        <article class="price-row${oferta ? " is-offer" : ""}">
            ${pct ? `<span class="price-row__off">-${pct}%</span>` : `<span class="price-row__off price-row__off--hot">OFERTA</span>`}
            <header class="price-row__mast">
                <h5 class="price-row__name">${escapeHtml(nombreVitrina(item.nombre) || "Oferta Especial")}</h5>
                <span class="price-row__hair" aria-hidden="true"></span>
            </header>
            <div class="price-row__bottom">
                <div class="price-row__prices">
                    ${(precioOriginal > vigente) ? `<s class="price-row__was">${formatMoney(precioOriginal)}</s>` : ""}
                    <strong class="price-row__now"><span class="deal-currency">$</span><span class="odometer-val" data-val="${vigente}">${formatMoney(vigente).replace(/^\$\s*/, "")}</span></strong>
                </div>
                ${regla ? `<div class="price-row__rule">${escapeHtml(regla)}</div>` : ""}
            </div>
        </article>
    `;
}
