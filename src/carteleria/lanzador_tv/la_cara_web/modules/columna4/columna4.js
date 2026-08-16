/* Columna 4: lobo chef + clima real + rotación de lo más pedido en tickets. */

import { htmlPronosticoClima } from "./tarjetas/tarjeta_chef.js";
import { nombreVitrina, precioVigente } from "../shared/plata_y_texto.js";

const ROTACION_MS = 8000;

let rotacionTimer = null;
let rotacionIndex = 0;
let itemsCache = [];
let climaCache = null;
let productosCache = [];
let rootRef = null;

function esNoche() {
    const hora = new Date().getHours();
    return hora >= 18 || hora < 6;
}

function itemsTickets(state) {
    const panel = (state.rotacion || []).find((p) => p.id === "elegidos");
    const lista = (panel?.items?.length ? panel.items : state.destacados) || [];
    const vistos = new Set();
    const out = [];
    for (const item of lista) {
        const nombre = nombreVitrina(item?.nombre);
        const clave = nombre.toLowerCase();
        if (!nombre || vistos.has(clave)) continue;
        vistos.add(clave);
        out.push(item);
        if (out.length >= 8) break;
    }
    return out;
}

function enriquecer(item, productos) {
    const clave = nombreVitrina(item?.nombre).toLowerCase();
    const hit = (productos || []).find((p) => nombreVitrina(p.nombre).toLowerCase() === clave);
    const base = { ...item, ...(hit || {}) };
    return {
        ...base,
        nombre: nombreVitrina(base.nombre),
        precio: precioVigente(base) || Number(base.precio) || 0,
        icono_url: base.icono_url || item?.icono_url || "",
        departamento: base.departamento || base.categoria || item?.departamento || "",
    };
}

function climaVisible(climaData) {
    return {
        icono: climaData?.icono || "sol",
        temperatura: climaData?.temperatura || "22°C",
        mensaje: climaData?.mensaje || (esNoche()
            ? "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
            : "PARA ESTE MOMENTO DEL DÍA, TE RECOMENDAMOS LLEVAR"),
    };
}

function pintar(conFade) {
    if (!rootRef) return;
    const clima = climaVisible(climaCache);
    if (!itemsCache.length) {
        rootRef.innerHTML = htmlPronosticoClima({
            ...clima,
            producto_recomendado: "Pollo entero",
            precio: 4900,
        });
        return;
    }
    const index = rotacionIndex % itemsCache.length;
    const item = enriquecer(itemsCache[index], productosCache);
    const html = htmlPronosticoClima({
        ...clima,
        producto_recomendado: item.nombre,
        precio: item.precio,
        icono_url: item.icono_url,
        departamento: item.departamento,
    });
    if (!conFade) {
        rootRef.innerHTML = html;
        return;
    }
    rootRef.classList.add("is-fading");
    window.setTimeout(() => {
        rootRef.innerHTML = html;
        rootRef.classList.remove("is-fading");
    }, 160);
}

export function iniciarRotacionColumna4(state, root) {
    rootRef = root;
    productosCache = state.productos || [];
    climaCache = state.climaData;
    const items = itemsTickets(state);
    const firma = JSON.stringify(items.map((i) => i.nombre));
    const misma = firma === JSON.stringify(itemsCache.map((i) => i.nombre));
    itemsCache = items.length ? items : itemsCache;
    if (!misma) {
        rotacionIndex = 0;
        pintar(false);
    } else {
        pintar(false);
    }
    if (rotacionTimer) return;
    if (itemsCache.length <= 1) return;
    rotacionTimer = setInterval(() => {
        if (itemsCache.length <= 1) return;
        rotacionIndex = (rotacionIndex + 1) % itemsCache.length;
        pintar(true);
    }, ROTACION_MS);
}
