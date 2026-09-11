/* Franja de oferta: tarjetas + publicidad cada 2. */

import {
    descuentoPct,
    esOferta,
    escapeHtml,
    formatMoney,
    htmlDealStage,
    leerPrecios,
    nombreVitrina,
    precioVigente,
    textoValidezOferta,
    unidadProducto,
} from "../shared/plata_y_texto.js";
import { iniciarCintaInfinita } from "../shared/cinta_infinita.js";
import { intercalateAds } from "../shared/publicidad_tv.js";

export function renderFranjaOferta(hero, productos, els) {
    const track = document.getElementById("carouselTrack");
    if (!track) return;

    const ofertas = (productos || []).filter(esOferta);
    const tarjetas = intercalateAds(ofertas, productos);

    if (tarjetas.length === 0) {
        track.innerHTML = '<p class="no-ofertas">Sin ofertas activas</p>';
        track.dataset.firma = "";
        return;
    }

    const firma = tarjetas.map((p) =>
        `${p.id || p.nombre}:${p.slot_ad ? "a" : "o"}:${p.alarma ? "1" : "0"}:${precioVigente(p)}`
    ).join("|");
    if (track.dataset.firma === firma && track.children.length >= 2) {
        tickCronometros(track);
        return;
    }
    track.dataset.firma = firma;

    const tarjetasHTML = tarjetas.map((producto) =>
        producto.slot_ad ? crearTarjetaPublicidad(producto) : crearTarjetaOferta(producto)
    ).join("");
    track.innerHTML = tarjetasHTML + tarjetasHTML;
    track.classList.remove("is-infinite");
    iniciarCarrusel(track);
}

function crearTarjetaPublicidad(producto) {
    return htmlDealCard(producto, { ad: true });
}

function crearTarjetaOferta(producto) {
    return htmlDealCard(producto, { ad: false });
}

function htmlDealCard(producto, { ad }) {
    const { original, vigente, hayOferta } = leerPrecios(producto);
    const pct = descuentoPct(original, vigente);
    const unidad = unidadProducto(producto);
    const ahorro = hayOferta ? original - vigente : 0;
    const nombre = nombreVitrina(producto.nombre || "Destacado");
    const esAd = Boolean(ad || producto.slot_ad);
    const stock = Number(producto.stock || 0);
    const condicion = textoValidezOferta(producto);
    const pie = stock > 0 && stock <= 8
        ? "¡Se agota!"
        : (ahorro > 0 ? `Ahorrás ${formatMoney(ahorro)} / ${unidad}` : "");
    const kicker = esAd ? "PUBLICIDAD" : (hayOferta ? "Ofertas" : "Precio especial");
    const offLabel = pct ? `-${pct}%` : (esAd ? "AD" : "NEW");
    const monto = vigente > 0 ? formatMoney(vigente).replace(/^\$\s*/, "") : "";
    const clave = claveTimer(producto, esAd);
    return `
        <article class="tv-card oferta-card is-deal${hayOferta ? " is-flash" : ""}${esAd ? " is-ad" : ""}${esAd && producto.alarma ? " is-ad-alarm" : ""}">
            ${htmlDealStage(producto, { off: offLabel })}
            <div class="deal-copy glass-panel">
                <div class="deal-copy__head">
                    <p class="deal-kicker deal-line">${escapeHtml(kicker)}</p>
                    <h3 class="tv-card__name deal-line">${escapeHtml(nombre)}</h3>
                </div>
                <div class="deal-copy__mid">
                    <div class="deal-price-row deal-line">
                        <div class="tv-card__now-box price-highlight">
                        ${vigente > 0
                            ? `<strong class="tv-card__now giant-price"><span class="deal-currency">$</span><span class="odometer-val" data-val="${vigente}">${escapeHtml(monto)}</span></strong>`
                            : `<strong class="tv-card__now giant-price">DESTACADO</strong>`}
                        ${hayOferta ? `<s class="tv-card__was diagonal-strike">${formatMoney(original)}</s>` : ""}
                        </div>
                    </div>
                    ${condicion ? `<p class="deal-save deal-line">${escapeHtml(condicion)}</p>` : ""}
                </div>
                <div class="deal-foot deal-line deal-line--split">
                    <span class="tv-card__timer">
                        <span class="tv-card__timer-icon pulse-icon" aria-hidden="true"></span>
                        <span class="tv-card__timer-text" data-deal-timer="${escapeHtml(clave)}">${formatMmSs(segundosDeTarjeta(clave))}</span>
                    </span>
                    ${pie ? `<span class="deal-proof${stock > 0 && stock <= 8 ? " is-low pulse-alert" : ""}">${escapeHtml(pie)}</span>` : ""}
                </div>
            </div>
            ${esAd ? "" : '<div class="card-shimmer"></div>'}
        </article>
    `;
}

const DURACIONES_MIN = [5, 10, 15, 30];
const cronometros = new Map();

function claveTimer(producto, ad) {
    return `${producto?.id || producto?.nombre || "x"}:${ad ? "ad" : "of"}`;
}

function minutosAlAzar() {
    return DURACIONES_MIN[Math.floor(Math.random() * DURACIONES_MIN.length)];
}

function segundosDeTarjeta(key) {
    const now = Date.now();
    let t = cronometros.get(key);
    if (!t || t.endsAt <= now) {
        const totalMs = minutosAlAzar() * 60 * 1000;
        const yaCorrio = Math.floor(Math.random() * totalMs * 0.35);
        t = { endsAt: now + totalMs - yaCorrio };
        cronometros.set(key, t);
    }
    return Math.max(1, Math.round((t.endsAt - now) / 1000));
}

function formatMmSs(total) {
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function tickCronometros(track) {
    track.querySelectorAll("[data-deal-timer]").forEach((el) => {
        const secs = segundosDeTarjeta(el.dataset.dealTimer);
        el.textContent = formatMmSs(secs);
        el.closest(".tv-card__timer")?.classList.toggle("is-urgent", secs < 60);
    });
}


function iniciarCarrusel(track) {
    if (track.dataset.timer !== "1") {
        track.dataset.timer = "1";
        setInterval(() => tickCronometros(track), 1000);
    }
    tickCronometros(track);

    const viewport = track.parentElement;
    iniciarCintaInfinita(track, {
        periodoMs: 4000,
        inicio: 0,
        xDeCuadro(i) {
            const card = track.children[i];
            if (!card || !viewport) return 0;
            return viewport.clientWidth / 2 - (card.offsetLeft + card.offsetWidth / 2);
        },
        alPosar(i, mitad) {
            const foco = i >= mitad ? i - mitad : i;
            const prev = track._foco;
            if (prev === i) return;
            track._foco = i;
            if (typeof prev === "number") {
                const p2 = prev >= mitad ? prev - mitad : prev;
                track.children[prev]?.classList.remove("is-center-focus");
                track.children[p2]?.classList.remove("is-center-focus");
            }
            track.children[i]?.classList.add("is-center-focus");
            track.children[foco]?.classList.add("is-center-focus");
        },
    });
}

