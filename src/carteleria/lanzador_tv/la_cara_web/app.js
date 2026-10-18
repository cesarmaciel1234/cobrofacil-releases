import { initCenterFocus, updateVFX } from "./modules/shared/vfx.js";
/* Cartelería TV: orquesta los módulos de la cara web. */

import { renderCabeceraNegocio, marcarCabeceraDesconectada, actualizarReloj } from "./modules/cabecera_negociodata/cabecera_negociodata.js";
import { renderFranjaOferta } from "./modules/franja_oferta/franja_oferta.js";
import { iniciarRotacionColumna1 } from "./modules/columna1/columna1.js";
import { renderColumna2 } from "./modules/columna2/columna2.js";
import { iniciarRotacionColumna3 } from "./modules/columna3/columna3.js";
import { iniciarRotacionColumna4 } from "./modules/columna4/columna4.js";
import { renderMensajeZocalo } from "./modules/mensaje_zocalo/mensaje_zocalo.js";
import { precargarFotosEstado, revelarFotosEn } from "./modules/shared/foto_tarjeta/index.js";

const TV_UI = "268";
const API_URL = "/api/state";
const REFRESH_RAPIDO = 600;
const REFRESH_NORMAL = 4000;

const state = {
    config: null,
    productos: [],
    destacados: [],
    rotacion: [],
    combos: [],
    columna3: [],
    ia: [],
    hero: null,
    climaData: null,
    currentTheme: "temu",
    isLoading: true,
    lastDataHash: null,
};

const els = {
    statusText: document.getElementById("statusText"),
    clock: document.getElementById("clock"),
    flashCountdown: document.getElementById("flashCountdown"),
    carouselTrack: document.getElementById("carouselTrack"),
    content1: document.getElementById("content1"),
    content2: document.getElementById("content2"),
    content3: document.getElementById("content3"),
    content4: document.getElementById("content4"),
    marquee: document.getElementById("marquee"),
    loading: document.getElementById("loading"),
    climaIcon: document.getElementById("climaIcon"),
    climaTemp: document.getElementById("climaTemp"),
};

function esChromium() {
    const ua = navigator.userAgent || "";
    return /Chrome|Chromium|Edg|Brave/i.test(ua);
}

function aplicarPerfil(_perfil) {
    const modo = esChromium() ? "max" : "eco";
    document.body.setAttribute("data-perf", modo);
}

function loadTheme(themeName) {
    if (!themeName) return;
    const alias = { auto: "premium", negro_temu: "premium" };
    const nombre = alias[themeName] || themeName;
    document.body.setAttribute("data-theme", nombre);
    const themeColorsLink = document.getElementById("theme-colors");
    const themeStylesLink = document.getElementById("theme-styles");
    const themePaths = {
        apple:        "css/themes/apple/colores.css",
        temu:         "css/themes/temu/colores.css",
        premium:      "css/themes/premium/colores.css",
        black:        "css/themes/black/colores.css",
        blackfriday:  "css/themes/blackfriday/colores.css",
    };
    const stylePaths = {
        apple:        "css/themes/apple/estilos.css",
        temu:         "css/themes/temu/estilos.css",
        premium:      "css/themes/premium/estilos.css",
        black:        "css/themes/black/estilos.css",
        blackfriday:  "css/themes/blackfriday/estilos.css",
    };
    if (!themePaths[nombre] || !stylePaths[nombre]) return;
    const bust = `?v=${TV_UI}`;
    const ya = themeStylesLink.dataset.loaded === nombre && themeStylesLink.dataset.ui === TV_UI;
    if (ya) return;
    themeColorsLink.href = themePaths[nombre] + bust;
    themeStylesLink.href = stylePaths[nombre] + bust;
    themeStylesLink.dataset.loaded = nombre;
    themeStylesLink.dataset.ui = TV_UI;
    state.currentTheme = nombre;
}

let pollId = 0;
let intervaloActual = 0;
const tInicio = Date.now();

function hayDatosEnPantalla() {
    return (state.productos && state.productos.length > 0)
        || (state.rotacion && state.rotacion.length > 0)
        || (state.destacados && state.destacados.length > 0);
}

function caraLista() {
    return (state.productos && state.productos.length > 0)
        && (state.rotacion && state.rotacion.length > 0);
}

function esEco() {
    return document.body.getAttribute("data-perf") === "eco";
}

function programarPoll() {
    const listo = caraLista() || Date.now() - tInicio > 15000;
    const ms = listo ? REFRESH_NORMAL : REFRESH_RAPIDO;
    if (ms === intervaloActual && pollId) return;
    if (pollId) clearInterval(pollId);
    intervaloActual = ms;
    pollId = setInterval(fetchState, ms);
}

function quitarCarga() {
    state.isLoading = false;
    if (els.loading) els.loading.classList.add("hidden");
}

async function fetchState() {
    try {
        const response = await fetch(API_URL, { cache: "no-store" });
        if (!response.ok) throw new Error(response.statusText);
        const data = await response.json();
        aplicarPerfil(data.config?.carteleria_perf);
        loadTheme(data.config?.carteleria_theme || "premium");
        const p = data.precios || [];
        const newDataHash = [
            data.datos_gen,
            (data.config || {}).data_status,
            p.length,
            p.map((x) => `${x.nombre}:${x.precio}:${x.precio_oferta || 0}`).join("|"),
            (data.rotacion || []).length,
            (data.destacados || [])[0]?.nombre,
            (data.hero || {}).nombre,
        ].join("§");
        if (state.lastDataHash === newDataHash) {
            if (state.isLoading && hayDatosEnPantalla()) quitarCarga();
            programarPoll();
            return;
        }
        const nuevos = data.precios || [];
        if (!nuevos.length && state.productos.length) {
            if (data.config) {
                state.config = data.config;
                try { renderCabeceraNegocio(state.config, els); } catch (err) { console.error("[Cartelería]", err); }
            }
            if (state.isLoading) quitarCarga();
            programarPoll();
            return;
        }
        state.lastDataHash = newDataHash;
        state.config = data.config;
        state.productos = nuevos;
        state.destacados = data.destacados || [];
        state.rotacion = data.rotacion || [];
        state.combos = data.combos || [];
        state.columna3 = data.columna3 || [];
        state.ia = data.ia || [];
        state.hero = data.hero || null;
        state.climaData = data.climaData || null;

        // --- APLICACIÓN DE ESTRUCTURA.md (Lógica Empresarial) ---
        
        // 1. Scoring de Productos (Estilo Amazon): Priorizar por ventas y ofertas
        if (state.productos.length > 0) {
            state.productos.sort((a, b) => {
                const scoreA = (a.precio_oferta ? 50 : 0) + (a.vendidos || a.ventas_dia || 0);
                const scoreB = (b.precio_oferta ? 50 : 0) + (b.vendidos || b.ventas_dia || 0);
                return scoreB - scoreA;
            });
        }
        
        // 2-8. Las demás lógicas (Precios Dinámicos, Categorización, Discovery, Combos) 
        // ya se aplican en la renderización de las columnas (shimmer-fx, rotación, etc).
        // --------------------------------------------------------

        const safe = (fn) => {
            try { fn(); } catch (err) { console.error("[Cartelería]", err); }
        };
        precargarFotosEstado(data);
        safe(() => renderFranjaOferta(state.hero, state.productos, els));
        safe(() => iniciarRotacionColumna1(state, els.content1));
        safe(() => renderColumna2(state.productos, els.content2));
        safe(() => iniciarRotacionColumna3(state, els.content3));
        safe(() => iniciarRotacionColumna4(state, els.content4));
        safe(() => renderMensajeZocalo(state.config, els.marquee));
        safe(() => renderCabeceraNegocio(state.config, els));
        safe(() => actualizarClimaHeader(state.climaData));
        safe(() => updateVFX());

        if (hayDatosEnPantalla()) quitarCarga();
        revelarFotosEn(document);
        programarPoll();
    } catch (error) {
        console.error("[Cartelería] Error al obtener datos:", error);
        marcarCabeceraDesconectada(els);
        programarPoll();
    }
}

function actualizarClimaHeader(climaData) {
    if (!els.climaIcon || !els.climaTemp) return;
    
    const icono = climaData?.icono || "sol";
    const temperatura = climaData?.temperatura || "22°C";
    
    const iconMap = {
        lluvia: "assets/lluvia.png",
        nube: "assets/nube.png",
        nublado: "assets/nube.png",
        sol: "assets/sol.png"
    };
    
    els.climaIcon.src = iconMap[icono] || iconMap.sol;
    els.climaIcon.alt = icono.charAt(0).toUpperCase() + icono.slice(1);
    els.climaTemp.textContent = temperatura;
    
    const flashClima = document.getElementById('flashClima');
    if (flashClima) {
        flashClima.classList.remove('clima-cold', 'clima-hot', 'clima-mild');
        const numTemp = parseInt(temperatura);
        if (!isNaN(numTemp)) {
            if (numTemp < 15) {
                flashClima.classList.add('clima-cold');
            } else if (numTemp > 25) {
                flashClima.classList.add('clima-hot');
            } else {
                flashClima.classList.add('clima-mild');
            }
        }
    }
}

function ajustarZoomTv() {
    document.documentElement.style.zoom = "1";
    const stage = document.querySelector(".app-container");
    if (!stage) return;
    const W = 1920;
    const H = 1080;
    const iw = Math.max(1, window.innerWidth);
    const ih = Math.max(1, window.innerHeight);
    const s = Math.min(iw / W, ih / H);
    stage.style.width = `${W}px`;
    stage.style.height = `${H}px`;
    stage.style.transformOrigin = "0 0";
    const ox = (iw - W * s) / 2;
    const oy = (ih - H * s) / 2;
    // zoom de Chromium: vuelve a rasterizar letras y CSS al tamaño del panel.
    stage.style.zoom = String(s);
    stage.style.transform = "none";
    stage.style.margin = `${oy}px 0 0 ${ox}px`;
}

function setupTvKeys() {
    window.addEventListener("keydown", (event) => {
        if (event.key === "F5") {
            event.preventDefault();
            event.stopPropagation();
            fetchState();
            return;
        }
        if (event.key === "F9") {
            event.preventDefault();
            event.stopPropagation();
            const body = document.body;
            let current = body.getAttribute("data-wall") || "4h";
            const sequence = ["4h", "3h", "2h", "ofertas"];
            let idx = sequence.indexOf(current);
            if (idx === -1) idx = 0;
            let next_wall = sequence[(idx + 1) % sequence.length];
            body.setAttribute("data-wall", next_wall);
            return;
        }

        
        if (event.key === "F10") {
            event.preventDefault();
            event.stopPropagation();
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(()=>{});
            } else {
                document.exitFullscreen().catch(()=>{});
            }
            return;
        }
        if (event.key === "F11" || event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            fetch('/api/control?action=stop', { cache: "no-store" }).catch(() => {});
        }
    }, true);
}

function init() {
    aplicarPerfil();
    ajustarZoomTv();
    window.addEventListener("resize", ajustarZoomTv);
    if (window.visualViewport) {
        window.visualViewport.addEventListener("resize", ajustarZoomTv);
    }
    actualizarReloj(els);
    setInterval(() => actualizarReloj(els), 1000);
    setupTvKeys();
    initCenterFocus();
    fetchState();
    programarPoll();
    setTimeout(() => { if (state.isLoading) quitarCarga(); }, 12000);
}

document.addEventListener("DOMContentLoaded", init);


