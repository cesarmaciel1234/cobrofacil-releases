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
    let original = Number(item.precio_original || item.precio || 0);
    const precio = Number(item.precio || 0);
    const nombre = nombreVitrina(item.nombre);
    
    if (original <= precio && precio > 0) {
        original = Math.round(precio * 1.2);
    }
    
    const pct = descuentoPct(original, precio);
    const monto = precio > 0 ? formatMoney(precio).replace(/^\$\s*/, "") : "";
    const tieneCondicion = true; // Forzar mostrar condición

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
                <div class="deal-copy flash-offer__copy">
                    <div class="deal-price-row">
                        ${precio > 0
                            ? `<strong class="tv-card__now"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>`
                            : ""}
                        ${original > precio ? `<s class="tv-card__was" style="font-size: 0.85em; opacity: 0.8;">${formatMoney(original)}</s>` : ""}
                    </div>
                    ${tieneCondicion ? `<div style="color: #000; font-size: clamp(0.85rem, 1.1vw, 1.2rem); font-weight: 900; letter-spacing: 0.05em; text-transform: uppercase; margin-top: 1vh; display: inline-block; background: linear-gradient(90deg, #FFDF00, #FFA500, #FFDF00); padding: 0.4em 1em; border-radius: 50px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.8), inset 0 2px 4px rgba(255,255,255,0.8); border: 2px solid #FFF; text-shadow: 1px 1px 0px rgba(255,255,255,0.5); animation: pulseGold 2s infinite;">${escapeHtml(textoValidezOferta(item))}</div>` : ""}
                </div>
            </div>
        </article>
    `;
}
