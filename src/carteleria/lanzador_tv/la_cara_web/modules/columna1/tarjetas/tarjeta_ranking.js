/* Ranking TV1: puesto real + dato de ventas de la base. */

import { escapeHtml, nombreVitrina } from "../../shared/plata_y_texto.js";

function textoFamilias(item) {
    const detalle = String(item.detalle || "");
    if (detalle && !/ticket/i.test(detalle)) return detalle;
    
    // Primero, buscar tickets reales
    let n = Number(item.tickets || item.veces || item.tickets_dia || item.cantidad_tickets || 0);
    
    // Si no hay info de tickets real, inferirlo
    if (n < 1) {
        let vol = Math.round(Number(item.cantidad || 0));
        n = Math.max(1, Math.floor(vol / 2));
        const match = detalle.match(/(\d+)/);
        if (vol < 1 && match) n = Number(match[1]);
    }

    if (n <= 1) return "1 familia lo eligió";
    return `${n}+ familias lo eligieron`;
}

function formatoKilosComoPct(valor) {
    const n = Number(valor) || 0;
    if (n <= 0) return "0 kg";
    if (Math.abs(n - Math.round(n)) < 0.05) return `${Math.round(n)} kg`;
    return `${n.toFixed(1).replace(".", ",")} kg`;
}

function formatoPlataComoPct(valor) {
    const n = Number(valor) || 0;
    if (n <= 0) return "$0";
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`;
    return `$${n}`;
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
    
    // Sistema de resaltado Top 3
    let topClass = "";
    if (puesto === 1) { topClass = "top-1"; }
    else if (puesto === 2) { topClass = "top-2"; }
    else if (puesto === 3) { topClass = "top-3"; }

    if (opciones.premium || opciones.mega) {
        const dato = opciones.premium
            ? premiumDelItem(item, opciones.items)
            : megaDelItem(item, opciones.items);
            
        // Forzar porcentaje un poco más agresivo si es el top 1 para simular boom (Opcional, pero se lee del motor real)
        const pctReal = dato.texto;
        
        return `
        <article class="asian-rank-card ${topClass} cascade-enter" style="animation-delay: ${i * 0.1}s">
            <div class="asian-rank-badge">
                <span class="asian-rank-num">#${puesto}</span>
            </div>
            <div class="asian-rank-info">
                <h4 class="asian-rank-name">${escapeHtml(nombre)}</h4>
                <div class="asian-rank-progress-container">
                    <div class="asian-rank-progress-bar" style="width:${Math.max(15, dato.barra).toFixed(1)}%"></div>
                    <span class="asian-rank-tag">${escapeHtml(pctReal)} VENDIDO</span>
                </div>
            </div>
            ${puesto === 1 ? '<div class="asian-rank-fire" style="font-size: 2rem; filter: drop-shadow(0 0 10px #FFD700);">🔥</div>' : ''}
        </article>
        `;
    }
    
    const tag = opciones.social
            ? textoFamilias(item)
            : String(item.detalle || "").toUpperCase();
            
    return `
        <article class="asian-rank-card ${topClass} cascade-enter" style="animation-delay: ${i * 0.1}s">
            <div class="asian-rank-badge">
                <span class="asian-rank-num">#${puesto}</span>
            </div>
            <div class="asian-rank-info">
                <h4 class="asian-rank-name">${escapeHtml(nombre)}</h4>
                ${tag ? `<div class="asian-rank-tag-social">${escapeHtml(tag)}</div>` : ""}
            </div>
        </article>
    `;
}
