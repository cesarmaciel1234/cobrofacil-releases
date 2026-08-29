/* Grilla de precios: ranking por departamento + precio en píldora. */

import { descuentoPct, escapeHtml, esOferta, formatMoney, nombreVitrina, precioVigente, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlFilaPrecio(item, puesto = 1, depto = "") {
    const vigente = precioVigente(item);
    const oferta = esOferta(item);
    const pct = descuentoPct(item.precio, vigente);
    const rubro = String(depto || item.departamento || item.categoria || "").trim().toUpperCase();
    const meta = puesto > 0
        ? `#${puesto}${rubro ? ` · ${rubro}` : ""}`
        : rubro;
    const regla = oferta ? textoValidezOferta(item) : "";
    return `
        <article class="price-row${oferta ? " is-offer" : ""}" style="display: flex; flex-direction: column; justify-content: center; gap: 0.2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <div class="price-row__info" style="display: flex; flex-direction: column; justify-content: center; gap: 0.1rem;">
                    <h5 class="price-row__name" style="margin: 0;">${escapeHtml(nombreVitrina(item.nombre))}</h5>
                    <p class="price-row__meta" style="margin: 0;">${escapeHtml(meta)}</p>
                </div>
                <div class="price-row__prices" style="display: flex; flex-direction: column; justify-content: center; align-items: flex-end; gap: 0;">
                    ${pct ? `<span class="price-row__off" style="margin: 0;">-${pct}%</span>` : ""}
                    ${oferta ? `<s class="price-row__was" style="margin: 0;">${formatMoney(item.precio)}</s>` : ""}
                    <strong class="price-row__now" style="margin-top: 0.1rem;"><span class="deal-currency">$</span><span class="odometer-val" data-val="${vigente}">${formatMoney(vigente).replace(/^\$\s*/, "")}</span></strong>
                </div>
            </div>
            ${regla ? `<div class="price-row__rule" style="width: 100%; font-size: clamp(0.75em, 1.1vw, 0.9em); color: #FFD700; opacity: 0.9; margin: 0;">${escapeHtml(regla)}</div>` : ""}
        </article>
    `;
}
