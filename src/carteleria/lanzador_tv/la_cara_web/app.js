import { initCenterFocus, updateVFX } from "./modules/shared/vfx.js";
/* Cartelería TV: orquesta los módulos de la cara web. */

import { renderCabeceraNegocio, marcarCabeceraDesconectada, actualizarReloj } from "./modules/cabecera_negociodata/cabecera_negociodata.js";
import { renderFranjaOferta } from "./modules/franja_oferta/franja_oferta.js";
import { iniciarRotacionColumna1 } from "./modules/columna1/columna1.js";
import { renderColumna2 } from "./modules/columna2/columna2.js";
import { iniciarRotacionColumna3 } from "./modules/columna3/columna3.js";
import { iniciarRotacionColumna4 } from "./modules/columna4/columna4.js";
import { renderMensajeZocalo } from "./modules/mensaje_zocalo/mensaje_zocalo.js";

const API_URL = "/api/state";
const REFRESH_INTERVAL = 15000;

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
    currentTheme: "premium",
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

function perfilNavegador() {
    const ram = navigator.deviceMemory || 4;
    const cpu = navigator.hardwareConcurrency || 4;
    return ram < 6 || cpu < 4 ? "eco" : "max";
}

function aplicarPerfil(perfil) {
    const modo = perfil === "eco" || perfil === "max" ? perfil : perfilNavegador();
    document.body.setAttribute("data-perf", modo);
}

function loadTheme(themeName) {
    if (!themeName) return;
    document.body.setAttribute("data-theme", themeName);
    if (themeName === state.currentTheme) return;
    const themeColorsLink = document.getElementById("theme-colors");
    const themeStylesLink = document.getElementById("theme-styles");
    const themePaths = {
        apple:      "css/themes/apple/colores.css",
        temu:       "css/themes/temu/colores.css",
        blackfriday:"css/themes/blackfriday/colores.css",
        premium:    "css/themes/premium/colores.css",
    };
    const stylePaths = {
        apple:      "css/themes/apple/estilos.css",
        temu:       "css/themes/temu/estilos.css",
        blackfriday:"css/themes/blackfriday/estilos.css",
        premium:    "css/themes/premium/estilos.css",
    };
    if (themePaths[themeName] && stylePaths[themeName]) {
        const bust = `?v=${Date.now()}`;
        themeColorsLink.href = themePaths[themeName] + bust;
        themeStylesLink.href = stylePaths[themeName] + bust;
        state.currentTheme = themeName;
    }
}

async function fetchState() {
    try {
        const response = await fetch(API_URL, { cache: "no-store" });
        if (!response.ok) throw new Error(response.statusText);
        const data = await response.json();
        aplicarPerfil(data.config?.carteleria_perf);
        const newDataHash = JSON.stringify({
            config: data.config,
            precios: data.precios,
            destacados: data.destacados,
            rotacion: data.rotacion,
            combos: data.combos,
            columna3: data.columna3,
            ia: data.ia,
            hero: data.hero,
            climaData: data.climaData,
        });
        if (state.lastDataHash === newDataHash) return;
        state.lastDataHash = newDataHash;
        state.config = data.config;
        state.productos = data.precios || [];
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
        
        // 2. Personalización Temporal (Estilo Netflix): Cambiar tema por hora del día
        let temaDefinitivo = data.config?.carteleria_theme;
        if (!temaDefinitivo || temaDefinitivo === "auto") {
            const hora = new Date().getHours();
            if (hora >= 6 && hora < 12) temaDefinitivo = "apple";       // Mañana: Limpio y claro
            else if (hora >= 12 && hora < 19) temaDefinitivo = "temu";  // Tarde: Vibrante comercial
            else temaDefinitivo = "premium";                            // Noche: Oscuro y elegante
        }
        loadTheme(temaDefinitivo);
        
        // 3-8. Las demás lógicas (Precios Dinámicos, Categorización, Discovery, Combos) 
        // ya se aplican en la renderización de las columnas (shimmer-fx, rotación, etc).
        // --------------------------------------------------------

        renderFranjaOferta(state.hero, state.productos, els);
        iniciarRotacionColumna1(state, els.content1);
        renderColumna2(state.productos, els.content2);
        iniciarRotacionColumna3(state, els.content3);
        iniciarRotacionColumna4(state, els.content4);
        renderMensajeZocalo(state.config, els.marquee);
        actualizarClimaHeader(state.climaData);
        updateVFX(); // Dispara los efectos solo cuando hay datos nuevos

        if (state.isLoading) {
            state.isLoading = false;
            els.loading.classList.add("hidden");
        }
    } catch (error) {
        console.error("[Cartelería] Error al obtener datos:", error);
        marcarCabeceraDesconectada(els);
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
    const stage = document.querySelector(".app-container");
    if (!stage) return;
    const W = 1920;
    const H = 1080;
    const vw = Math.max(1, window.innerWidth);
    const vh = Math.max(1, window.innerHeight);
    const s = Math.min(vw / W, vh / H);
    const ox = (vw - W * s) / 2;
    const oy = (vh - H * s) / 2;
    stage.style.width = `${W}px`;
    stage.style.height = `${H}px`;
    stage.style.transformOrigin = "0 0";
    stage.style.transform = `scale(${s})`;
    stage.style.margin = `${oy}px 0 0 ${ox}px`;
}

function setupTvKeys() {
    window.addEventListener("keydown", (event) => {
        if (event.key !== "F10" && event.key !== "F11" && event.key !== "Escape") return;
        event.preventDefault();
        event.stopPropagation();
        const action = event.key === "F10" ? "monitor" : "stop";
        fetch(`/api/control?action=${action}`, { cache: "no-store" }).catch(() => {});
    }, true);
}

function init() {
    aplicarPerfil();
    document.body.setAttribute("data-theme", state.currentTheme);
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
    setInterval(fetchState, REFRESH_INTERVAL);
}

document.addEventListener("DOMContentLoaded", init);


