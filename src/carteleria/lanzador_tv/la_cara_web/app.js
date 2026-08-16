/* Cartelería TV: orquesta los módulos de la cara web. */

import { renderCabeceraNegocio, marcarCabeceraDesconectada, actualizarReloj } from "./modules/cabecera_negociodata/cabecera_negociodata.js";
import { renderFranjaOferta } from "./modules/franja_oferta/franja_oferta.js";
import { iniciarRotacionColumna1 } from "./modules/columna1/columna1.js";
import { renderColumna2 } from "./modules/columna2/columna2.js";
import { iniciarRotacionColumna3 } from "./modules/columna3/columna3.js";
import { renderColumna4 } from "./modules/columna4/columna4.js";
import { renderMensajeZocalo } from "./modules/mensaje_zocalo/mensaje_zocalo.js";

const API_URL = "/api/state";
const REFRESH_INTERVAL = 5000;

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
};

function loadTheme(themeName) {
    if (!themeName) return;
    document.body.setAttribute("data-theme", themeName);
    if (themeName === state.currentTheme) return;
    const themeColorsLink = document.getElementById("theme-colors");
    const themeStylesLink = document.getElementById("theme-styles");
    const themePaths = {
        apple: "css/themes/apple/colores.css",
        temu: "css/themes/temu/colores.css",
        blackfriday: "css/themes/blackfriday/colores.css",
    };
    const stylePaths = {
        apple: "css/themes/apple/estilos.css",
        temu: "css/themes/temu/estilos.css",
        blackfriday: "css/themes/blackfriday/estilos.css",
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
        const newDataHash = JSON.stringify({
            config: data.config,
            precios: data.precios,
            destacados: data.destacados,
            rotacion: data.rotacion,
            combos: data.combos,
            columna3: data.columna3,
            ia: data.ia,
            hero: data.hero,
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

        if (data.config?.carteleria_theme) loadTheme(data.config.carteleria_theme);
        renderFranjaOferta(state.hero, state.productos, els);
        iniciarRotacionColumna1(state, els.content1);
        renderColumna2(state.productos, els.content2);
        iniciarRotacionColumna3(state, els.content3);
        renderColumna4(state.ia, els.content4, state.climaData, state.productos);
        renderMensajeZocalo(state.config, els.marquee);

        if (state.isLoading) {
            state.isLoading = false;
            els.loading.classList.add("hidden");
        }
    } catch (error) {
        console.error("[Cartelería] Error al obtener datos:", error);
        marcarCabeceraDesconectada(els);
    }
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
    document.body.setAttribute("data-theme", state.currentTheme);
    actualizarReloj(els);
    setInterval(() => actualizarReloj(els), 1000);
    setupTvKeys();
    fetchState();
    setInterval(fetchState, REFRESH_INTERVAL);
}

document.addEventListener("DOMContentLoaded", init);
