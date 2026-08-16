/* TV4: chef + recomendación con la misma familia visual del carrusel. */

import { escapeHtml, formatMoney, htmlDealStage, nombreVitrina } from "../../shared/plata_y_texto.js";
import { htmlLoboChef } from "../componentes/lobo_chef.js";

function mensajeCorto(mensaje) {
    const t = String(mensaje || "").toLowerCase();
    if (t.includes("noche")) return "Para esta noche, llevá";
    if (t.includes("lluvia")) return "Día de lluvia, llevá";
    if (t.includes("nublado") || t.includes("nube")) return "Día nublado, llevá";
    if (t.includes("sol")) return "Día de sol, llevá";
    return "Para este momento, llevá";
}

function tipoClima(icono, temperatura, mensaje) {
    // Usar directamente el icono del backend (viene de ClimaWorker con datos reales de Open-Meteo)
    const iconoLower = String(icono || "").toLowerCase();
    if (iconoLower === "lluvia") return "lluvia";
    if (iconoLower === "nube" || iconoLower === "nublado") return "nube";
    
    // Fallback: analizar mensaje si no viene el icono correcto
    const blob = `${mensaje || ""}`.toLowerCase();
    if (blob.includes("lluvia")) return "lluvia";
    if (blob.includes("nube") || blob.includes("nublado")) return "nube";
    
    return "sol";
}

function htmlIconoClima(tipo) {
    const src = tipo === "lluvia" ? "assets/lluvia.png" : (tipo === "nube" ? "assets/nube.png" : "assets/sol.png");
    const alt = tipo === "lluvia" ? "Lluvia" : (tipo === "nube" ? "Nublado" : "Sol");
    return `<img class="chef-weather-icon" src="${src}" alt="${alt}">`;
}

export function htmlPronosticoClima(climaData) {
    const { temperatura, mensaje, producto_recomendado, precio, icono } = climaData || {};
    const nombre = nombreVitrina(producto_recomendado || "Pollo entero");
    const monto = Number(precio) > 0 ? formatMoney(precio).replace(/^\$\s*/, "") : "";
    const clima = tipoClima(icono, temperatura, mensaje);
    return `
        <article class="chef-board">
            <header class="rank-head sale-head">
                <p class="rank-kicker">⚡ CHEF</p>
                ${temperatura ? `<span class="chef-temp">${htmlIconoClima(clima)}<span>${escapeHtml(temperatura)}</span></span>` : ""}
            </header>
            <div class="chef-hero">
                ${htmlLoboChef()}
                <p class="chef-msg">${escapeHtml(mensajeCorto(mensaje))}</p>
            </div>
            <div class="chef-deal">
                ${htmlDealStage({ nombre, icono_url: climaData?.icono_url, departamento: climaData?.departamento || nombre }, { bolt: false })}
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

