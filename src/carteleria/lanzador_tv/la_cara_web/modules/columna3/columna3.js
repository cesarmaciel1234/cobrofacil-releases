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
        const depto = String(item.departamento || item.categoria || "").trim().toUpperCase();
        if (!depto) continue;
        if (!grupos.has(depto)) grupos.set(depto, []);
        grupos.get(depto).push(item);
    }
    const slides = [];
    const vistos = new Set();
    for (const [, items] of grupos) {
        if (items.length < 3) continue;
        const orden = [...items].sort((a, b) => {
            const fa = a.icono || a.icono_url ? 0 : 1;
            const fb = b.icono || b.icono_url ? 0 : 1;
            return fa - fb;
        });
        for (const item of orden) {
            const nombre = String(item.nombre || "").trim();
            if (!nombre || vistos.has(nombre)) continue;
            const mates = orden
                .map((p) => String(p.nombre || "").trim())
                .filter((n) => n && n !== nombre)
                .slice(0, 3);
            if (mates.length < 2) continue;
            vistos.add(nombre);
            slides.push({
                tipo: "cruzada",
                nombre,
                pregunta: `¿LLEVÁS ${tituloPregunta(nombre)}?`,
                relacionados: mates.map((n) => String(n).toUpperCase()),
            });
            if (slides.length >= 4) return slides;
        }
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
    if (api.length) {
        const cruzadas = api.filter((item) => item.tipo === "cruzada");
        const ofertas = api.filter((item) => item.tipo === "oferta");
        if (cruzadas.length && ofertas.length) return api;
        const mix = intercalar(cruzadas, ofertas);
        return mix.length ? mix : api;
    }
    const mix = intercalar(cruzadasDesdeProductos(state.productos), ofertasDesdeProductos(state.productos));
    return mix.length ? mix : api;
}

function htmlSlide(slide) {
    if (slide.tipo === "cruzada") return htmlTarjetaCruzada(slide, productosCache);
    return htmlTarjetaRelampago(slide);
}

function pintar() {
    if (!rootRef) return;
    if (!slidesCache.length) {
        rootRef.innerHTML = '<p class="column-empty">Sin venta cruzada ni ofertas todavía.</p>';
        return;
    }
    const index = rotacionIndex % slidesCache.length;
    rootRef.innerHTML = htmlSlide(slidesCache[index]);
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
        pintar();
    }
    if (rotacionTimer) return;
    if (slidesCache.length <= 1) return;
    rotacionTimer = setInterval(() => {
        if (!slidesCache.length) return;
        rotacionIndex = (rotacionIndex + 1) % slidesCache.length;
        pintar();
    }, ROTACION_MS);
}
