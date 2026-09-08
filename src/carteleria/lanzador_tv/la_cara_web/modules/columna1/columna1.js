/* Columna 1: ranking. Las tarjetas se quedan; solo cambia el producto. */

import { htmlTarjetaRanking, pruebaSocial } from "./tarjetas/tarjeta_ranking.js";
import { nombreVitrina, urlsFotoProducto } from "../shared/plata_y_texto.js";

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

function metaPanel(panel) {
    const firma = `${panel.id || ""} ${panel.titulo || ""} ${panel.subtitulo || ""}`;
    const premium = panel.id === "plata" || /premium|plata|recaud/i.test(firma);
    const social = panel.id === "elegidos" || /elegid|pedido/i.test(firma);
    const mega = panel.id === "volumen" || /mega|kilo|volumen/i.test(firma);
    const etiqueta = premium ? "Venta premium" : (mega ? "Mega ventas" : "Lo más elegido");
    return { premium, social, mega, etiqueta };
}

function htmlPanel(panel) {
    const meta = metaPanel(panel);
    const items = (panel.items || []).slice(0, 4);
    const cards = items.map((item, i) =>
        htmlTarjetaRanking({ ...item, puesto: i + 1 }, i, { ...meta, items, etiqueta: meta.etiqueta })
    ).join("");
    return `<div class="rank-list">${cards}</div>`;
}

function ponerFoto(stage, item) {
    if (!stage) return;
    const urls = urlsFotoProducto(item);
    const img = stage.querySelector(".deal-stage__img");
    const letra = stage.querySelector(".deal-stage__letter");
    const next = urls[0] || "";
    const fallbacks = urls.slice(1).join("|");
    if (img) {
        if (img.getAttribute("src") === next) return;
        const preload = new Image();
        preload.onload = () => {
            if (stage.querySelector(".deal-stage__img") !== img) return;
            img.src = next;
            img.dataset.fallbacks = fallbacks;
        };
        preload.onerror = () => {
            if (urls[1]) img.src = urls[1];
        };
        if (next) preload.src = next;
        return;
    }
    if (!next) return;
    const nuevo = document.createElement("img");
    nuevo.className = "deal-stage__img";
    nuevo.alt = "";
    nuevo.dataset.fallbacks = fallbacks;
    nuevo.src = next;
    stage.prepend(nuevo);
    if (letra) letra.classList.add("has-img");
}

function aplicarTarjeta(card, item, i, meta) {
    const puesto = i + 1;
    card.classList.toggle("top-1", puesto === 1);
    card.classList.toggle("top-2", puesto === 2);
    card.classList.toggle("top-3", puesto === 3);
    card.classList.toggle("is-panel-premium", Boolean(meta.premium));
    const badge = card.querySelector(".rank-escarapela");
    if (badge) badge.textContent = `#${puesto}`;
    const nombre = card.querySelector(".rank-roof-name");
    if (nombre) nombre.textContent = nombreVitrina(item.nombre);
    const tag = card.querySelector(".rank-roof-tag");
    if (tag) {
        tag.classList.toggle("is-premium", Boolean(meta.premium));
        const caret = tag.querySelector(".rank-caret");
        const texto = meta.etiqueta || "Lo más elegido";
        tag.textContent = texto;
        if (caret) tag.appendChild(caret);
        else if (meta.premium) {
            const blink = document.createElement("span");
            blink.className = "rank-caret";
            blink.setAttribute("aria-hidden", "true");
            blink.textContent = "_";
            tag.appendChild(blink);
        }
    }
    const proof = card.querySelector(".rank-proof");
    if (proof) proof.textContent = pruebaSocial(item, meta);
    ponerFoto(card.querySelector(".rank-stage"), item);
}

function pintar(recrear) {
    if (!rootRef) return;
    if (!panelesCache.length) {
        rootRef.innerHTML = '<p class="column-empty">Sin ventas todavía.</p>';
        return;
    }
    const panel = panelesCache[rotacionIndex % panelesCache.length];
    const meta = metaPanel(panel);
    const items = (panel.items || []).slice(0, 4);
    let list = rootRef.querySelector(".rank-list");
    const cards = list ? [...list.querySelectorAll(".asian-rank-card")] : [];
    if (recrear || !list || cards.length !== items.length) {
        rootRef.innerHTML = htmlPanel(panel);
        return;
    }
    items.forEach((item, i) => aplicarTarjeta(cards[i], { ...item, puesto: i + 1 }, i, meta));
}

export function iniciarRotacionColumna1(state, root) {
    rootRef = root;
    const paneles = panelesRotacion(state);
    const firma = JSON.stringify(paneles.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    const misma = firma === JSON.stringify(panelesCache.map((p) => [p.id, (p.items || []).map((i) => i.nombre)]));
    const habia = root.querySelectorAll(".asian-rank-card").length;
    panelesCache = paneles;
    if (!misma || !habia) {
        pintar(!habia);
    }
    if (rotacionTimer) return;
    if (panelesCache.length <= 1) return;
    rotacionTimer = setInterval(() => {
        if (!panelesCache.length) return;
        rotacionIndex = (rotacionIndex + 1) % panelesCache.length;
        pintar(false);
    }, ROTACION_MS);
}
