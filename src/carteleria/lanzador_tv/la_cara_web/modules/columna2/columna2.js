/* Columna 2: precios por departamento + publicidad cada 4 filas. */

import { escapeHtml } from "../shared/plata_y_texto.js";
import { htmlFilaPrecio } from "./tarjetas/fila_precio.js";
import { htmlTarjetaPublicidad } from "./tarjetas/tarjeta_publicidad.js";

const ORDEN_DEPTO = ["CARNE", "CARNES", "AVES", "CERDO", "EMBUTIDOS", "EMBUTIDO", "FIAMBRES", "ALMACEN"];

function nombreDepto(item) {
    const raw = String(item.departamento || item.categoria || "GENERAL").trim().toUpperCase();
    if (raw === "CARNE") return "CARNES";
    if (raw === "EMBUTIDO") return "EMBUTIDOS";
    return raw || "GENERAL";
}

function agruparPorDepartamento(productos) {
    const grupos = new Map();
    for (const item of productos) {
        const depto = nombreDepto(item);
        if (!grupos.has(depto)) grupos.set(depto, []);
        grupos.get(depto).push(item);
    }
    for (const [, items] of grupos) {
        items.sort((a, b) => Number(b.cantidad || 0) - Number(a.cantidad || 0));
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

function nombreClave(item) {
    return String(item?.nombre || "").toLowerCase().trim();
}

function siguienteAd(ads, adIndex, evitar) {
    const evitarClave = nombreClave(evitar);
    for (let k = 0; k < ads.length; k += 1) {
        const ad = ads[(adIndex + k) % ads.length];
        if (nombreClave(ad) !== evitarClave) {
            return { ad, next: adIndex + k + 1 };
        }
    }
    return { ad: ads[adIndex % ads.length], next: adIndex + 1 };
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
            const vendido = Number(item.cantidad || 0) > 0;
            if (vendido) ranking += 1;
            partes.push(htmlFilaPrecio(item, vendido ? ranking : 0, depto));
            enBloque += 1;
            if (enBloque % 4 === 0 && ads.length) {
                const { ad, next } = siguienteAd(ads, adIndex, item);
                partes.push(htmlTarjetaPublicidad(ad));
                adIndex = next;
            }
        }
    }
    if (ads.length && enBloque > 0 && enBloque < 4) {
        const { ad } = siguienteAd(ads, 0, null);
        partes.push(htmlTarjetaPublicidad(ad));
    }
    return partes.join("");
}

let lastColumna2Html = "";

export function renderColumna2(productos, root) {
    if (!productos || productos.length === 0) {
        root.innerHTML = '<p class="column-empty">Sin precios para mostrar.</p>';
        return;
    }
    const filas = armarCiclo(productos);
    const duracion = Math.max(50, Math.min(productos.length * 5, 180));
    
    const newHtml = `
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
    
    // Solo actualizar el DOM si los productos/precios cambiaron para no resetear la animación CSS
    if (newHtml !== lastColumna2Html) {
        root.innerHTML = newHtml;
        lastColumna2Html = newHtml;
    }
}
