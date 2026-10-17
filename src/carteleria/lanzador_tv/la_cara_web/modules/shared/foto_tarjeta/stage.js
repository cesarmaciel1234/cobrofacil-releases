/* HTML del recuadro: letra hasta que el PNG tiene .is-ready. */

import { escapeHtml, letraVitrina, tonoDepto } from "../plata_y_texto.js";
import { FOTO_SISTEMA, urlsFotoProducto } from "./urls.js";

export function htmlDealStage(item, { off = "", extraClass = "", titulo = "", bolt = true } = {}) {
    const urls = urlsFotoProducto(item);
    const url = urls[0] || FOTO_SISTEMA;
    const fallbacks = urls.slice(1);
    const letra = letraVitrina(item?.nombre);
    const onerr = `this.classList.remove('is-ready');const q=(this.dataset.fallbacks||'').split('|').filter(Boolean);if(q.length){this.src=q.shift();this.dataset.fallbacks=q.join('|');}else if(this.src.indexOf('logo_sistema')<0){this.src='${FOTO_SISTEMA}';}else{this.classList.add('is-ready');}`;
    return `
        <div class="deal-stage${extraClass ? ` ${extraClass}` : ""}" data-tone="${escapeHtml(tonoDepto(item))}">
            ${url ? `<img class="deal-stage__img" src="${escapeHtml(url)}" alt="" decoding="async" fetchpriority="high" ${fallbacks.length ? `data-fallbacks="${escapeHtml(fallbacks.join("|"))}"` : ""} onload="this.classList.add('is-ready')" onerror="${onerr}">` : ""}
            <span class="deal-stage__letter${url ? " has-img" : ""}">${escapeHtml(letra)}</span>
            ${titulo ? `<span class="deal-stage__name">${escapeHtml(titulo)}</span>` : ""}
            ${off ? `<span class="deal-stage__off">${escapeHtml(off)}</span>` : ""}
        </div>
    `;
}
