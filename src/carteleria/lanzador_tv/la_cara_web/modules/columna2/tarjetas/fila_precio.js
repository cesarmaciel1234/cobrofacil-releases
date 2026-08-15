/* Grilla de precios: ranking por departamento + precio en píldora. */

import { descuentoPct, escapeHtml, esOferta, formatMoney, precioVigente } from "../../shared/plata_y_texto.js";

export function htmlFilaPrecio(item, puesto = 1, depto = "") {
    const vigente = precioVigente(item);
    const oferta = esOferta(item);
    const pct = descuentoPct(item.precio, vigente);
    const rubro = String(depto || item.departamento || item.categoria || "").trim().toUpperCase();
    const meta = `#${puesto}${rubro ? ` · ${rubro}` : ""}`;
    return `
        <article class="price-row${oferta ? " is-offer" : ""}">
            <div class="price-row__info">
                <h5 class="price-row__name">${escapeHtml(item.nombre || "")}</h5>
                <p class="price-row__meta">${escapeHtml(meta)}</p>
            </div>
            <div class="price-row__prices">
                ${pct ? `<span class="price-row__off">-${pct}%</span>` : ""}
                ${oferta ? `<s class="price-row__was">${formatMoney(item.precio)}</s>` : ""}
                <strong class="price-row__now">${formatMoney(vigente)}</strong>
            </div>
        </article>
    `;
}
