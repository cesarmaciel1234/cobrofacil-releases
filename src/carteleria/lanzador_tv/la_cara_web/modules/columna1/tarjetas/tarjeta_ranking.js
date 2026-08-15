/* Ranking TV1: #N + etiqueta amarilla + nombre grande. */

import { escapeHtml } from "../../shared/plata_y_texto.js";

const ETIQUETAS = {
    elegidos: [
        "👑 N°1 EN TICKETS 🔥",
        "🔥 EL MÁS ELEGIDO",
        "⭐ TOP EN TICKETS 🔥",
        "🎯 FAVORITO CLIENTES",
        "💥 MÁS PEDIDO HOY 🔥",
    ],
    volumen: [
        "🏆 N°1 MEGA VENTAS 🔥",
        "🥩 TOP EN KILOS 🔥",
        "⚡ ALTO VOLUMEN 🔥",
        "💥 VENTAS MASIVAS 🔥",
        "🚀 TOP VOLUMEN HOY 🔥",
    ],
    recomendados: [
        "✨ RECOMENDADO HOY 🔥",
        "🎲 SELECCIÓN AL AZAR",
        "💎 PARA LLEVAR",
        "🌟 SUGERENCIA",
        "🎁 ELEGIDO DEL DÍA 🔥",
    ],
};

export function htmlTarjetaRanking(item, i, panelId) {
    const puesto = Number(item.puesto || i + 1);
    const tags = ETIQUETAS[panelId] || ETIQUETAS.elegidos;
    const tag = item.es_publicidad
        ? "📢 PUBLICIDAD"
        : tags[(puesto - 1) % tags.length];
    const nombre = String(item.nombre || "").toUpperCase();
    return `
        <article class="rank-card${item.es_publicidad ? " is-ad" : ""}">
            <div class="rank-line">
                <span class="rank-num">#${puesto}</span>
                <span class="rank-tag">${escapeHtml(tag)}</span>
            </div>
            <h4 class="rank-name">${escapeHtml(nombre)}</h4>
        </article>
    `;
}
