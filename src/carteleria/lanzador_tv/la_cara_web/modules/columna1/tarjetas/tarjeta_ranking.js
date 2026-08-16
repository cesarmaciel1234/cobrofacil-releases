/* Ranking TV1: puesto real + dato de ventas de la base. */

import { escapeHtml, nombreVitrina } from "../../shared/plata_y_texto.js";

function textoFamilias(item) {
    const detalle = String(item.detalle || "");
    if (detalle && !/ticket/i.test(detalle)) return detalle;
    let n = Math.round(Number(item.cantidad || 0));
    if (n < 1) {
        const match = detalle.match(/(\d+)/);
        n = match ? Number(match[1]) : 1;
    }
    if (n <= 1) return "1 familia lo eligió";
    return `${n}+ familias lo eligieron`;
}

function formatoKilosComoPct(valor) {
    const n = Number(valor) || 0;
    if (n <= 0) return "0 %";
    if (Math.abs(n - Math.round(n)) < 0.05) return `${Math.round(n)} %`;
    return `${n.toFixed(1).replace(".", ",")} %`;
}

function formatoPlataComoPct(valor) {
    const n = Number(valor) || 0;
    if (n <= 0) return "0.00%";
    return `${(n / 1000).toFixed(2)}%`;
}

function barraRelativa(valor, items, clave) {
    const serie = (items || []).map((row) => Math.max(0, Number(row[clave] || 0)));
    const tope = Math.max(valor, ...serie, 1);
    return (valor / tope) * 100;
}

function megaDelItem(item, items = []) {
    const valor = Math.max(0, Number(item.cantidad || 0));
    const barraGuardada = Number(item.barra);
    return {
        texto: formatoKilosComoPct(valor),
        barra: Number.isFinite(barraGuardada) && barraGuardada > 0
            ? barraGuardada
            : barraRelativa(valor, items, "cantidad"),
    };
}

function premiumDelItem(item, items = []) {
    const valor = Math.max(0, Number(item.recaudacion || 0));
    const barraGuardada = Number(item.barra);
    return {
        texto: formatoPlataComoPct(valor),
        barra: Number.isFinite(barraGuardada) && barraGuardada > 0
            ? barraGuardada
            : barraRelativa(valor, items, "recaudacion"),
    };
}

export function htmlTarjetaRanking(item, i, opciones = {}) {
    const puesto = Number(item.puesto || i + 1);
    const nombre = nombreVitrina(item.nombre).toUpperCase();
    if ((opciones.premium || opciones.mega) && !item.es_publicidad) {
        const dato = opciones.premium
            ? premiumDelItem(item, opciones.items)
            : megaDelItem(item, opciones.items);
        return `
        <article class="rank-card">
            <div class="rank-line">
                <span class="rank-num">#${puesto}</span>
                <span class="rank-tag">${escapeHtml(dato.texto)}</span>
            </div>
            <h4 class="rank-name">${escapeHtml(nombre)}</h4>
            <div class="rank-share" aria-hidden="true">
                <span class="rank-share__bar" style="width:${Math.max(8, dato.barra).toFixed(1)}%"></span>
            </div>
        </article>
    `;
    }
    const tag = item.es_publicidad
        ? "PUBLICIDAD"
        : opciones.social
            ? textoFamilias(item)
            : String(item.detalle || "").toUpperCase();
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
