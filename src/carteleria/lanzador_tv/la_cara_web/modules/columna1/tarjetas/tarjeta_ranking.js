/* Ranking TV1: puesto real + dato de ventas de la base. */

import { escapeHtml, nombreVitrina } from "../../shared/plata_y_texto.js";

export function htmlTarjetaRanking(item, i) {
    const puesto = Number(item.puesto || i + 1);
    const tag = item.es_publicidad
        ? "PUBLICIDAD"
        : String(item.detalle || "").toUpperCase();
    const nombre = nombreVitrina(item.nombre).toUpperCase();
    return `
        <article class="rank-card${item.es_publicidad ? " is-ad" : ""}">
            <div class="rank-line">
                <span class="rank-num">#${puesto}</span>
                ${tag ? `<span class="rank-tag">${escapeHtml(tag)}</span>` : ""}
            </div>
            <h4 class="rank-name">${escapeHtml(nombre)}</h4>
        </article>
    `;
}
