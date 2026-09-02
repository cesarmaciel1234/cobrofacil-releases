/* Grilla de precios: ranking por departamento + precio en píldora. */

import { descuentoPct, escapeHtml, esOferta, formatMoney, nombreVitrina, precioVigente, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlFilaPrecio(item, puesto = 1, depto = "") {
    const vigente = precioVigente(item);
    const oferta = esOferta(item);
    
    // Simular precio mostrador (20% más alto) cuando no hay descuento en la base de datos
    let precioOriginal = item.precio_original || item.precio_anterior || item.precio || vigente;
    if (precioOriginal <= vigente && vigente > 0) {
        precioOriginal = Math.round(vigente * 1.2);
    }
    
    const pct = descuentoPct(precioOriginal, vigente);
    const rubro = String(depto || item.departamento || item.categoria || "").trim().toUpperCase();
    const meta = puesto > 0
        ? `#${puesto}${rubro ? ` · ${rubro}` : ""}`
        : rubro;
    
    // Mostrar siempre la condición porque en TV todo es precio mayorista
    const regla = textoValidezOferta(item);
    const esDestacado = puesto === 1 || (item.cantidad || 0) > 10;
    
    return `
        <article class="price-row${oferta ? " is-offer" : ""}${esDestacado ? " is-featured" : ""}" style="display: flex; flex-direction: column; justify-content: center; gap: 0.3rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <div class="price-row__info" style="display: flex; flex-direction: column; justify-content: center; gap: 0.15rem;">
                    <div style="display: flex; align-items: center; gap: 0.5vw;">
                        ${esDestacado ? '<span style="font-size: clamp(0.8rem, 1.2vw, 1rem);">🔥</span>' : ''}
                        <h5 class="price-row__name" style="margin: 0;">${escapeHtml(nombreVitrina(item.nombre) || "Oferta Especial")}</h5>
                    </div>
                    <p class="price-row__meta" style="margin: 0;">${escapeHtml(meta)}</p>
                </div>
                <div class="price-row__prices" style="display: flex; flex-direction: column; justify-content: center; align-items: flex-end; gap: 0.2rem;">
                    ${pct ? `<span class="price-row__off" style="margin: 0; align-self: flex-end;">-${pct}%</span>` : ""}
                    <div style="display: flex; flex-direction: row; align-items: center; gap: 0.5vw;">
                        ${(precioOriginal > vigente) ? `<s class="price-row__was" style="margin: 0; color: rgba(255,255,255,0.6); font-size: 0.85em;">${formatMoney(precioOriginal)}</s>` : ""}
                        <strong class="price-row__now" style="margin: 0;"><span class="deal-currency">$</span><span class="odometer-val" data-val="${vigente}">${formatMoney(vigente).replace(/^\$\s*/, "")}</span></strong>
                    </div>
                </div>
            </div>
            ${regla ? `<div class="price-row__rule" style="width: 100%; font-size: clamp(0.75em, 1.1vw, 0.9em); color: #FFDF00; font-weight: bold; margin: 0; background: rgba(255, 215, 0, 0.15); padding: 0.3vh 0.6vw; border-radius: 6px; border: 1px solid rgba(255, 215, 0, 0.4); text-transform: uppercase;">${escapeHtml(regla)}</div>` : ""}
        </article>
    `;
}
