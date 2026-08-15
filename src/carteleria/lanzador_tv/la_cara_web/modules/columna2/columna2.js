/* Columna 2: precios por departamento + publicidad cada 4 filas. */

import { escapeHtml } from "../shared/plata_y_texto.js";
import { htmlFilaPrecio } from "./tarjetas/fila_precio.js";
import { htmlTarjetaPublicidad } from "./tarjetas/tarjeta_publicidad.js";

const ORDEN_DEPTO = ["CARNE", "CARNES", "AVES", "CERDO", "EMBUTIDOS", "FIAMBRES", "ALMACEN"];

function nombreDepto(item) {
    const raw = String(item.departamento || item.categoria || "GENERAL").trim().toUpperCase();
    if (raw === "CARNE") return "CARNES";
    return raw || "GENERAL";
}

function agruparPorDepartamento(productos) {
    const grupos = new Map();
    for (const item of productos) {
        const depto = nombreDepto(item);
        if (!grupos.has(depto)) grupos.set(depto, []);
        grupos.get(depto).push(item);
    }
    return [...grupos.entries()].sort((a, b) => {
        const ia = ORDEN_DEPTO.indexOf(a[0]);
        const ib = ORDEN_DEPTO.indexOf(b[0]);
        if (ia === -1 && ib === -1) return a[0].localeCompare(b[0], "es");
        if (ia === -1) return 1;
        if (ib === -1) return -1;
        return ia - ib;
    });
}

function htmlDepartamento(nombre) {
    return `<div class="price-dept">${escapeHtml(nombre)}</div>`;
}

function armarCiclo(productos) {
    const ads = productos.filter((item) => item.es_publicidad);
    let adIndex = 0;
    let enBloque = 0;
    const partes = [];

    for (const [depto, items] of agruparPorDepartamento(productos)) {
        partes.push(htmlDepartamento(depto));
        let ranking = 0;
        for (const item of items) {
            ranking += 1;
            partes.push(htmlFilaPrecio(item, ranking, depto));
            enBloque += 1;
            if (enBloque % 4 === 0 && ads.length) {
                partes.push(htmlTarjetaPublicidad(ads[adIndex % ads.length]));
                adIndex += 1;
            }
        }
    }
    return partes.join("");
}

export function renderColumna2(productos, root) {
    if (!productos || productos.length === 0) {
        root.innerHTML = '<p class="column-empty">Sin precios para mostrar.</p>';
        return;
    }
    const filas = armarCiclo(productos);
    const duracion = Math.max(50, Math.min(productos.length * 5, 180));
    root.innerHTML = `
        <header class="board-head sale-head sale-head--solo">
            <p class="board-kicker">⚡ PRECIOS</p>
        </header>
        <div class="price-ticker">
            <div class="price-track" style="--price-scroll-duration: ${duracion}s">
                <div class="price-cycle">${filas}</div>
                <div class="price-cycle" aria-hidden="true">${filas}</div>
            </div>
        </div>
    `;
}
