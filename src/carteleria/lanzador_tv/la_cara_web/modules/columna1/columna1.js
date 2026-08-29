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
let productosCache = [];
let rootRef = null;

function panelesRotacion(state) {
    const paneles = (state.rotacion || []).filter((panel) => panel?.items?.length);
    if (paneles.length) return paneles;
    if (state.destacados?.length) {
        return [{ id: "elegidos", titulo: "Favoritos de las familias", subtitulo: "Lo más pedido", items: state.destacados }];
    }
    return [];
}

function nombreClave(item) {
    return String(item?.nombre || "").toLowerCase().trim();
}

function siguienteAd(ads, adIndex, evitar) {
    if (!ads.length) return { ad: null, next: adIndex };
    const evitarClave = nombreClave(evitar);
    for (let k = 0; k < ads.length; k += 1) {
        const ad = ads[(adIndex + k) % ads.length];
        if (nombreClave(ad) !== evitarClave) {
            return { ad, next: adIndex + k + 1 };
        }
    }
    return { ad: ads[adIndex % ads.length], next: adIndex + 1 };
}

function inyectarPublicidad(items, productos) {
    const ads = (productos || []).filter((item) => item.es_publicidad);
    if (!ads.length || !items.length) return items;
    const out = [];
    let adIndex = 0;
    items.forEach((item, i) => {
        out.push(item);
        if ((i + 1) % 4 === 0) {
            const { ad, next } = siguienteAd(ads, adIndex, item);
            if (ad) {
                out.push({ ...ad, es_publicidad: true, slot_ad: true });
                adIndex = next;
            }
        }
    });
    if (out.every((item) => !item.es_publicidad) && ads.length) {
        const { ad } = siguienteAd(ads, 0, items[items.length - 1]);
        if (ad) out.push({ ...ad, es_publicidad: true, slot_ad: true });
    }
    return out;
}

function htmlPanel(panel, paneles, index, productos) {
    const dots = paneles.map((_, i) =>
        `<span class="rank-dot${i === index ? " is-on" : ""}"></span>`
    ).join("");
    const premium = panel.id === "plata" || /en ventas/i.test(panel.subtitulo || "");
    const social = panel.id === "elegidos";
    const mega = panel.id === "volumen" || /kilo/i.test(panel.subtitulo || "");
    const ranking = (panel.items || []).slice(0, 5);
    const items = inyectarPublicidad(ranking, productos);
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
            <p class="rank-kicker">⚡ ${escapeHtml(kickerPanel(panel))}</p>
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
    const html = htmlPanel(panelesCache[index], panelesCache, index, productosCache);
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
    productosCache = state.productos || [];
    const firma = JSON.stringify(paneles.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    const misma = firma === JSON.stringify(panelesCache.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    panelesCache = paneles;
    if (!misma) {
        rotacionIndex = 0;
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
