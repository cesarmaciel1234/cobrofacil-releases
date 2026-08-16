/* Columna 3: venta cruzada rotando con ofertas relámpago. */

import { esOferta, nombreVitrina } from "../shared/plata_y_texto.js";
import { htmlTarjetaCruzada } from "./tarjetas/tarjeta_cruzada.js";
import { htmlTarjetaRelampago } from "./tarjetas/tarjeta_relampago.js";

const ROTACION_MS = 7000;

let rotacionTimer = null;
let rotacionIndex = 0;
let slidesCache = [];
let productosCache = [];
let rootRef = null;

function tituloPregunta(nombre) {
    return nombreVitrina(nombre).toUpperCase() || "ESTO";
}

function cruzadasDesdeProductos(productos) {
    const grupos = new Map();
    for (const item of productos || []) {
        const nombre = String(item.nombre || "").trim();
        if (!nombre) continue;
        const depto = String(item.departamento || item.categoria || "GENERAL").toUpperCase();
        if (!grupos.has(depto)) grupos.set(depto, []);
        grupos.get(depto).push(nombre);
    }
    const slides = [];
    const vistos = new Set();
    for (const item of productos || []) {
        const nombre = String(item.nombre || "").trim();
        if (!nombre || vistos.has(nombre)) continue;
        const depto = String(item.departamento || item.categoria || "GENERAL").toUpperCase();
        const mates = (grupos.get(depto) || []).filter((n) => n !== nombre).slice(0, 3);
        if (mates.length < 2) continue;
        vistos.add(nombre);
        slides.push({
            tipo: "cruzada",
            nombre,
            pregunta: `¿LLEVÁS ${tituloPregunta(nombre)}?`,
            relacionados: mates.map((n) => String(n).toUpperCase()),
        });
        if (slides.length >= 4) break;
    }
    return slides;
}

function ofertasDesdeProductos(productos) {
    return (productos || []).filter(esOferta).slice(0, 4).map((item) => ({
        tipo: "oferta",
        nombre: item.nombre,
        precio: Number(item.precio_oferta),
        precio_original: Number(item.precio),
        cant_oferta: Number(item.cant_oferta || 0),
        tipo_unidad_oferta: item.tipo_unidad_oferta || "",
        unidad: item.unidad || "",
        es_pesable: item.es_pesable || 0,
    }));
}

function intercalar(cruzadas, ofertas) {
    const slides = [];
    const n = Math.max(cruzadas.length, ofertas.length);
    for (let i = 0; i < n; i += 1) {
        if (cruzadas.length) slides.push(cruzadas[i % cruzadas.length]);
        if (ofertas.length) slides.push(ofertas[i % ofertas.length]);
        if (slides.length >= 8) break;
    }
    return slides;
}

function slidesColumna3(state) {
    const api = (state.columna3 || []).filter((item) => item && item.tipo);
    const hayCruzada = api.some((item) => item.tipo === "cruzada");
    const hayOferta = api.some((item) => item.tipo === "oferta");
    if (hayCruzada && hayOferta) return api;
    const cruzadas = hayCruzada ? api.filter((item) => item.tipo === "cruzada") : cruzadasDesdeProductos(state.productos);
    const ofertas = hayOferta ? api.filter((item) => item.tipo === "oferta") : ofertasDesdeProductos(state.productos);
    const mix = intercalar(cruzadas, ofertas);
    return mix.length ? mix : api;
}

function htmlSlide(slide) {
    if (slide.tipo === "cruzada") return htmlTarjetaCruzada(slide, productosCache);
    return htmlTarjetaRelampago(slide);
}

function pintar(conFade) {
    if (!rootRef) return;
    if (!slidesCache.length) {
        rootRef.innerHTML = '<p class="column-empty">Sin venta cruzada ni ofertas todavía.</p>';
        return;
    }
    const index = rotacionIndex % slidesCache.length;
    const html = htmlSlide(slidesCache[index]);
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

export function iniciarRotacionColumna3(state, root) {
    rootRef = root;
    productosCache = state.productos || [];
    const slides = slidesColumna3(state);
    const firma = JSON.stringify(slides.map((s) => [s.tipo, s.nombre || s.pregunta]));
    const misma = firma === JSON.stringify(slidesCache.map((s) => [s.tipo, s.nombre || s.pregunta]));
    slidesCache = slides;
    if (!misma) {
        rotacionIndex = 0;
        pintar(false);
    }
    if (rotacionTimer) return;
    if (slidesCache.length <= 1) return;
    rotacionTimer = setInterval(() => {
        if (!slidesCache.length) return;
        rotacionIndex = (rotacionIndex + 1) % slidesCache.length;
        pintar(true);
    }, ROTACION_MS);
}
