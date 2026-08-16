/* TV4: chef + recomendación con la misma familia visual del carrusel. */

import { escapeHtml, formatMoney, htmlDealStage, nombreVitrina } from "../../shared/plata_y_texto.js";
import { htmlLoboChef } from "../componentes/lobo_chef.js";

function kickerClima(mensaje) {
    const t = String(mensaje || "").toLowerCase();
    if (t.includes("noche")) return "Esta noche";
    if (t.includes("lluvia")) return "Día de lluvia";
    if (t.includes("nublado")) return "Día nublado";
    return "Del momento";
}

function mensajeCorto(mensaje) {
    const t = String(mensaje || "").toLowerCase();
    if (t.includes("noche")) return "Para esta noche, llevá";
    if (t.includes("lluvia")) return "Día de lluvia, llevá";
    if (t.includes("nublado")) return "Día nublado, llevá";
    return "Para este momento, llevá";
}

export function htmlPronosticoClima(climaData) {
    const { temperatura, mensaje, producto_recomendado, precio } = climaData || {};
    const nombre = nombreVitrina(producto_recomendado || "Pollo entero");
    const monto = Number(precio) > 0 ? formatMoney(precio).replace(/^\$\s*/, "") : "";
    return `
        <article class="chef-board">
            <header class="rank-head sale-head">
                <div>
                    <p class="rank-kicker">⚡ CHEF</p>
                    <h3 class="rank-title">${escapeHtml(kickerClima(mensaje))}</h3>
                </div>
                ${temperatura ? `<span class="chef-temp">${escapeHtml(temperatura)}</span>` : ""}
            </header>
            <div class="chef-hero">
                ${htmlLoboChef()}
                <p class="chef-msg">${escapeHtml(mensajeCorto(mensaje))}</p>
            </div>
            <div class="chef-deal">
                ${htmlDealStage({ nombre, icono_url: climaData?.icono_url, departamento: climaData?.departamento || nombre })}
                <div class="deal-copy">
                    <p class="deal-kicker">Recomendado</p>
                    <h3 class="tv-card__name">${escapeHtml(nombre)}</h3>
                    ${monto ? `<div class="deal-price-row">
                        <strong class="tv-card__now"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>
                    </div>` : ""}
                </div>
            </div>
        </article>
    `;
}
