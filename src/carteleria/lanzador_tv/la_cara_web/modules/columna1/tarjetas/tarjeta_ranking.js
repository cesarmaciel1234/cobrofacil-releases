/* Ranking TV1: se ve el producto, no un renglón. Sin precio. */

import { escapeHtml, htmlDealStage, nombreVitrina } from "../../shared/plata_y_texto.js";

function numDia(item, claves) {
    for (const k of claves) {
        const n = Number(item[k]);
        if (Number.isFinite(n) && n > 0) return n;
    }
    return 0;
}

function fmtNumero(n, dec = 1) {
    if (!Number.isFinite(n) || n <= 0) return "0";
    if (Math.abs(n - Math.round(n)) < 0.05) return String(Math.round(n));
    return n.toFixed(dec).replace(".", ",");
}

function humoKilos(item) {
    const kg = numDia(item, ["cantidad", "kilos", "volumen", "vendidos"]);
    return `${fmtNumero(kg)} % vendidos hoy`;
}

function fmtSocial(n) {
    if (n >= 1000000) return `${fmtNumero(n / 1000000)}M`;
    if (n >= 1000) return `${fmtNumero(n / 1000)}K`;
    return fmtNumero(n, 0);
}

function humoPremium(item) {
    const plata = numDia(item, ["recaudacion", "total", "venta"]);
    const tag = fmtSocial(plata);
    return tag === "1" ? "1K lo eligió" : `${tag} lo eligieron`;
}

function textoFamiliasHoy(item) {
    const n = Math.max(0, Math.round(numDia(item, ["tickets", "veces", "tickets_dia", "cantidad_tickets", "cantidad"])));
    if (n <= 0) return "Hoy se elige en caja";
    if (n === 1) return "1 familia eligió hoy";
    return `${n} familias eligieron hoy`;
}

export function pruebaSocial(item, opciones = {}) {
    if (opciones.premium) return humoPremium(item);
    if (opciones.mega) return humoKilos(item);
    return textoFamiliasHoy(item);
}

export function htmlTarjetaRanking(item, i, opciones = {}) {
    const puesto = Number(item.puesto || i + 1);
    const nombre = nombreVitrina(item.nombre);
    const topClass = puesto === 1 ? "top-1" : (puesto === 2 ? "top-2" : (puesto === 3 ? "top-3" : ""));
    const social = pruebaSocial(item, opciones);
    const etiqueta = opciones.etiqueta || "Lo más elegido";
    const esPremium = Boolean(opciones.premium) || /premium/i.test(etiqueta);

    return `
        <article class="asian-rank-card is-photo ${topClass}${esPremium ? " is-panel-premium" : ""}">
            <span class="rank-escarapela" aria-hidden="true">#${puesto}</span>
            <div class="rank-roof">
                <h4 class="asian-rank-name rank-roof-name">${escapeHtml(nombre)}</h4>
                <p class="rank-roof-tag${esPremium ? " is-premium" : ""}">${escapeHtml(etiqueta)}<span class="rank-caret" aria-hidden="true">_</span></p>
            </div>
            ${htmlDealStage(item, { extraClass: "rank-stage", off: "" })}
            <div class="asian-rank-info">
                <div class="rank-proof">${escapeHtml(social)}</div>
            </div>
        </article>
    `;
}
