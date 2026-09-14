/* Columna 1: ranking real de ventas (tickets, kilos y recaudación). */

import { escapeHtml } from "../shared/plata_y_texto.js";
import { htmlTarjetaRanking } from "./tarjetas/tarjeta_ranking.js";

const TITULOS_KICKER = {
    elegidos: "Lo más pedido",
    volumen: "Mega ventas",
    plata: "Venta premium",
};

function kickerPanel(panel) {
    const sub = panel.subtitulo || "";
    if (panel.id === "volumen" || /kilo/i.test(sub)) return "Mega ventas";
    if (panel.id === "plata" || /en ventas/i.test(sub)) return "Venta premium";
    return TITULOS_KICKER[panel.id] || sub || "HOT";
}

const ROTACION_MS = 8000;

let rotacionTimer = null;
let rotacionIndex = 0;
let panelesCache = [];
let rootRef = null;

function panelesRotacion(state) {
    const paneles = (state.rotacion || []).filter((panel) => panel?.items?.length);
    if (paneles.length) return paneles;
    if (state.destacados?.length) {
        return [{ id: "elegidos", titulo: "Favoritos de las familias", subtitulo: "Lo más pedido", items: state.destacados }];
    }
    return [];
}

function htmlPanel(panel, paneles, index) {
    const dots = paneles.map((_, i) =>
        `<span class="rank-dot${i === index ? " is-on" : ""}"></span>`
    ).join("");
    const premium = panel.id === "plata" || /en ventas/i.test(panel.subtitulo || "");
    const social = panel.id === "elegidos";
    const mega = panel.id === "volumen" || /kilo/i.test(panel.subtitulo || "");
    const items = (panel.items || []).slice(0, 5);
    const cards = items.map((item, i) =>
        htmlTarjetaRanking(item, i, { premium, social, mega, items })
    ).join("");
    const listaClase = [
        "rank-list",
        social ? "is-social" : "",
        (premium || mega) ? "is-mega" : "",
    ].filter(Boolean).join(" ");
    return `
        <header class="rank-head sale-head">
            <p class="rank-kicker">🔥 ${escapeHtml(kickerPanel(panel))}</p>
            <div class="rank-dots" aria-hidden="true">${dots}</div>
        </header>
        <div class="${listaClase}">${cards}</div>
        <div class="rank-progress" style="--rank-duration:${ROTACION_MS}ms"></div>
    `;
}

function pintar(conFade) {
    if (!rootRef) return;
    if (!panelesCache.length) {
        rootRef.innerHTML = '<p class="column-empty">Sin ventas todavía.</p>';
        return;
    }
    const index = rotacionIndex % panelesCache.length;
    const html = htmlPanel(panelesCache[index], panelesCache, index);
    if (!conFade) {
        rootRef.innerHTML = html;
        return;
    }
    rootRef.classList.add("is-fading");
    window.setTimeout(() => {
        rootRef.innerHTML = html;
        rootRef.classList.remove("is-fading");
    }, 400);
}

export function iniciarRotacionColumna1(state, root) {
    rootRef = root;
    const paneles = panelesRotacion(state);
    const firma = JSON.stringify(paneles.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    const misma = firma === JSON.stringify(panelesCache.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    panelesCache = paneles;
    if (!misma) {
        pintar(false);
    }
    if (rotacionTimer) return;
    if (panelesCache.length <= 1) return;
    rotacionTimer = setInterval(() => {
        if (!panelesCache.length) return;
        rotacionIndex = (rotacionIndex + 1) % panelesCache.length;
        pintar(true);
    }, ROTACION_MS);
}


