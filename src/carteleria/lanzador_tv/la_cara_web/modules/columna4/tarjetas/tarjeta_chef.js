/* Tarjeta principal del chef, extras y pronóstico del clima. */

import { escapeHtml, formatMoney } from "../../shared/plata_y_texto.js";
import { htmlBadgeClima } from "../componentes/badge_clima.js";
import { htmlLoboChef } from "../componentes/lobo_chef.js";
import { htmlMensajePersonalizado } from "../componentes/mensaje_personalizado.js";
import { htmlRecomendacionDestacada } from "../componentes/recomendacion_destacada.js";

export function htmlTarjetaChef(primero) {
    return `
        <article class="chef-pick">
            <p class="chef-reason">${escapeHtml(primero.razon || "Recomendado ahora")}</p>
            <h4 class="chef-name">${escapeHtml(primero.nombre)}</h4>
            <p class="chef-price">${formatMoney(primero.precio)}</p>
        </article>
    `;
}

export function htmlTarjetaChefExtra(rec) {
    return `
        <article class="price-tile chef-tile">
            <h5 class="price-tile__name">${escapeHtml(rec.nombre)}</h5>
            <div class="price-tile__prices">
                <strong class="price-tile__now">${formatMoney(rec.precio)}</strong>
            </div>
        </article>
    `;
}

export function htmlPronosticoClima(climaData) {
    const { icono, temperatura, mensaje, producto_recomendado, precio } = climaData;
    
    return `
        <article class="pronostico-card">
            <div class="pronostico-header">
                ${htmlBadgeClima(temperatura)}
            </div>
            <div class="pronostico-body">
                ${htmlLoboChef()}
                ${htmlMensajePersonalizado(mensaje)}
                ${htmlRecomendacionDestacada(producto_recomendado, precio)}
            </div>
        </article>
    `;
}
