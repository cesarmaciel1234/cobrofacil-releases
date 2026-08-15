/* Franja de oferta: tarjetas + publicidad cada 4 (motor_publicidad). */

import { descuentoPct, esOferta, formatMoney, precioVigente, unidadProducto, escapeHtml, textoValidezOferta } from "../shared/plata_y_texto.js";

export function renderFranjaOferta(hero, productos, els) {
    const track = document.getElementById("carouselTrack");
    if (!track) return;

    const ofertas = productos.filter((p) => esOferta(p));
    const base = ofertas.length > 0 ? ofertas : (productos.length > 0 ? productos.slice(0, 10) : []);
    const tarjetas = inyectarPublicidad(base, productos);

    if (tarjetas.length === 0) {
        track.innerHTML = '<p class="no-ofertas">Sin ofertas activas</p>';
        return;
    }

    const tarjetasHTML = tarjetas.map((producto) =>
        producto.slot_ad ? crearTarjetaPublicidad(producto) : crearTarjetaOferta(producto)
    ).join("");
    track.innerHTML = tarjetasHTML + tarjetasHTML;
    iniciarCarrusel(track);
}

function inyectarPublicidad(ofertas, productos) {
    const ads = (productos || []).filter((item) => item.es_publicidad);
    if (!ads.length) return ofertas;
    const out = [];
    let adIndex = 0;
    ofertas.forEach((item, i) => {
        out.push(item);
        if ((i + 1) % 4 === 0) {
            out.push({ ...ads[adIndex % ads.length], es_publicidad: true, slot_ad: true });
            adIndex += 1;
        }
    });
    return out;
}

function crearTarjetaPublicidad(producto) {
    const vigente = precioVigente(producto);
    return `
        <article class="tv-card oferta-card is-ad">
            <div class="tv-card__top">
                <h3 class="tv-card__name">${escapeHtml(producto.nombre || "Destacado")}</h3>
                <span class="tv-card__off is-ad">PUBLICIDAD</span>
            </div>
            <div class="tv-card__pay">
                <div class="tv-card__now-row">
                    <strong class="tv-card__now">${vigente > 0 ? formatMoney(vigente) : "DESTACADO"}</strong>
                    <span class="tv-card__unit">CASA</span>
                </div>
            </div>
        </article>
    `;
}

function crearTarjetaOferta(producto) {
    const vigente = precioVigente(producto);
    const enOferta = esOferta(producto);
    const pct = descuentoPct(producto.precio, vigente);
    const validez = textoValidezOferta(producto);
    const ahorro = enOferta ? Number(producto.precio) - vigente : 0;
    const unidad = unidadProducto(producto);
    return `
        <article class="tv-card oferta-card${enOferta ? " is-flash" : ""}">
            <div class="tv-card__top">
                <h3 class="tv-card__name">${escapeHtml(producto.nombre)}</h3>
                ${pct ? `<span class="tv-card__off">-${pct}%</span>` : ""}
            </div>
            <div class="tv-card__pay">
                ${enOferta ? `<div class="tv-card__was-row"><s class="tv-card__was">${formatMoney(producto.precio)}</s>${validez ? `<span class="tv-card__rule">${escapeHtml(validez)}</span>` : ""}</div>` : ""}
                <div class="tv-card__now-row">
                    <strong class="tv-card__now">${formatMoney(vigente)}</strong>
                    ${ahorro > 0
                        ? `<span class="tv-card__save"><span class="tv-card__save-label">AHORRÁS</span><strong class="tv-card__save-amt">${formatMoney(ahorro)} x ${unidad}</strong></span>`
                        : `<span class="tv-card__unit">POR ${unidad.toUpperCase()}</span>`}
                </div>
            </div>
        </article>
    `;
}

function iniciarCarrusel(track) {
    if (track.dataset.running === "1") return;
    track.dataset.running = "1";
    let position = 0;
    const speed = 1.15;

    function animate() {
        position -= speed;
        const trackWidth = track.scrollWidth / 2;
        if (trackWidth > 0 && Math.abs(position) >= trackWidth) position = 0;
        track.style.transform = `translateX(${position}px)`;
        requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
}
