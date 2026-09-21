/* Columna 4: lobo chef + clima real + rotación de lo más pedido en tickets. */

import { htmlPronosticoClima } from "./tarjetas/tarjeta_chef.js";
import { nombreVitrina } from "../shared/plata_y_texto.js";

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
    // Priorizamos "volumen" (volumen del día) para apalancar el boom del día
    const panel = (state.rotacion || []).find((p) => p.id === "volumen" || p.id === "elegidos");
    let lista = [];
    
    if (state.volumen && state.volumen.length > 0) {
        lista = state.volumen;
    } else if (panel?.items?.length) {
        lista = panel.items;
    } else {
        lista = state.destacados || [];
    }
    
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
        precio: Number(base.precio) || 0,
        precio_oferta: Number(base.precio_oferta) || 0,
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

function pintar() {
    if (!rootRef) return;
    const clima = climaVisible(climaCache);
    
    // Generar ofertas para el carrusel (primeros 6 productos)
    const ofertas = itemsCache.slice(0, 6).map(item => enriquecer(item, productosCache));
    
    if (!itemsCache.length) {
        const fallback = (productosCache || []).find((p) => Number(p?.precio) > 0);
        if (!fallback) {
            rootRef.innerHTML = '<p class="column-empty">Sin productos en la lista todavía.</p>';
            return;
        }
        const item = enriquecer(fallback, productosCache);
        rootRef.innerHTML = htmlPronosticoClima({
            ...clima,
            producto_recomendado: item.nombre,
            precio: item.precio,
            icono_url: item.icono_url,
            departamento: item.departamento,
            ofertas: [item],
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
        ofertas: ofertas,
    });
    rootRef.innerHTML = html;
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
        pintar();
    }
    // The inner carousel handles its own rotation now. No need to rebuild DOM every 8 seconds.
    // rotacionTimer = setInterval(...) was removed to prevent interrupting the carousel.
}
