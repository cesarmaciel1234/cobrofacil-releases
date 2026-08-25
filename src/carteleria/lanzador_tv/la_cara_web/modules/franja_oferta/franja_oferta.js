/* Franja de oferta: tarjetas + publicidad cada 4 (motor_publicidad). */

import {
    cantMinimaOferta,
    descuentoPct,
    esOferta,
    escapeHtml,
    formatMoney,
    htmlDealStage,
    nombreVitrina,
    precioVigente,
    unidadProducto,
} from "../shared/plata_y_texto.js";

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

function nombreClave(item) {
    return String(item?.nombre || "").toLowerCase().trim();
}

function siguienteAd(ads, adIndex, evitar) {
    const evitarClave = nombreClave(evitar);
    for (let k = 0; k < ads.length; k += 1) {
        const ad = ads[(adIndex + k) % ads.length];
        if (nombreClave(ad) !== evitarClave) {
            return { ad, next: adIndex + k + 1 };
        }
    }
    return { ad: ads[adIndex % ads.length], next: adIndex + 1 };
}

function inyectarPublicidad(ofertas, productos) {
    const ads = (productos || []).filter((item) => item.es_publicidad);
    if (!ads.length) return ofertas;
    const out = [];
    let adIndex = 0;
    let inyectadas = 0;
    ofertas.forEach((item, i) => {
        out.push(item);
        if ((i + 1) % 4 === 0) {
            const { ad, next } = siguienteAd(ads, adIndex, item);
            out.push({ ...ad, es_publicidad: true, slot_ad: true });
            adIndex = next;
            inyectadas += 1;
        }
    });
    if (inyectadas === 0 && ofertas.length) {
        const { ad } = siguienteAd(ads, 0, ofertas[ofertas.length - 1]);
        out.push({ ...ad, es_publicidad: true, slot_ad: true });
    }
    return out;
}

function crearTarjetaPublicidad(producto) {
    return htmlDealCard(producto, { ad: true });
}

function crearTarjetaOferta(producto) {
    return htmlDealCard(producto, { ad: false });
}

function htmlDealCard(producto, { ad }) {
    const vigente = precioVigente(producto);
    const enOferta = esOferta(producto);
    const pct = descuentoPct(producto.precio, vigente);
    const unidad = unidadProducto(producto);
    const ahorro = enOferta ? Number(producto.precio) - vigente : 0;
    const nombre = nombreVitrina(producto.nombre || "Destacado");
    const esAd = Boolean(ad || producto.slot_ad);
    const vendidos = Number(producto.veces || producto.cantidad || producto.vendidos || 0);
    const stock = Number(producto.stock || 0);
    const min = cantMinimaOferta(producto);
    const proof = stock > 0 && stock <= 8
        ? `Últimos ${Math.round(stock)}`
        : (vendidos > 0
            ? `${Math.round(vendidos)} vendidos`
            : (enOferta ? `Llevá ${min}+ ${unidad === "kilo" ? "kg" : "un."}` : "Destacado hoy"));
    const kicker = esAd ? "Publicidad" : (enOferta ? "Oferta relámpago" : "Precio especial");
    const offLabel = pct ? `-${pct}%` : (esAd ? "HOT" : "NEW");
    const monto = vigente > 0 ? formatMoney(vigente).replace(/^\$\s*/, "") : "";
    const clave = claveTimer(producto, esAd);
    return `
        <article class="tv-card oferta-card is-deal${enOferta ? " is-flash" : ""}${esAd ? " is-ad" : ""}">
            ${htmlDealStage(producto, { off: offLabel })}
            <div class="deal-copy">
                <p class="deal-kicker">${escapeHtml(kicker)}</p>
                <h3 class="tv-card__name">${escapeHtml(nombre)}</h3>
                <div class="deal-price-row">
                    ${vigente > 0
                        ? `<strong class="tv-card__now"><span class="deal-currency">$</span>${escapeHtml(monto)}</strong>`
                        : `<strong class="tv-card__now">DESTACADO</strong>`}
                    ${enOferta ? `<s class="tv-card__was">${formatMoney(producto.precio)}</s>` : ""}
                </div>
                ${ahorro > 0 ? `<p class="deal-save">Ahorrás ${formatMoney(ahorro)} / ${unidad}</p>` : ""}
                <div class="deal-foot">
                    <span class="tv-card__timer">
                        <span class="tv-card__timer-icon" aria-hidden="true">⏰</span>
                        <span class="tv-card__timer-text" data-deal-timer="${escapeHtml(clave)}">${formatMmSs(segundosDeTarjeta(clave))}</span>
                    </span>
                    <span class="deal-proof${stock > 0 && stock <= 8 ? " is-low" : ""}">${escapeHtml(proof)}</span>
                </div>
            </div>
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
    return `${m}:${String(s).padStart(2, "0")}`;
}

function tickCronometros(track) {
    track.querySelectorAll("[data-deal-timer]").forEach((el) => {
        const secs = segundosDeTarjeta(el.dataset.dealTimer);
        el.textContent = formatMmSs(secs);
        el.closest(".tv-card__timer")?.classList.toggle("is-urgent", secs < 60);
    });
}


function iniciarCarrusel(track) {
    if (track.dataset.running === "1") return;
    track.dataset.running = "1";
    
    let currentIndex = 0;
    
    // Para que la primera tarjeta arranque en el centro (opcional, pero ayuda al efecto)
    // Inicialmente track está a la izquierda.
    track.style.transition = "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)";
    
    function moverSiguiente() {
        if (!track.children.length) return;
        
        const card = track.children[0];
        const gap = window.innerWidth * 0.014; // 1.4vw
        const cardWidth = card.offsetWidth + gap;
        
        // Calculamos offset para que la tarjeta actual quede en el centro de la pantalla
        const centerOffset = (window.innerWidth / 2) - (card.offsetWidth / 2);
        
        currentIndex++;
        
        // Si llegamos a la mitad (porque el html está duplicado), reiniciamos sin transición
        const totalOriginal = track.children.length / 2;
        if (currentIndex > totalOriginal) {
            track.style.transition = "none";
            currentIndex = 1;
            const resetPos = centerOffset - (currentIndex - 1) * cardWidth;
            track.style.transform = `translateX(${resetPos}px)`;
            
            // Forzar reflow
            void track.offsetWidth;
            track.style.transition = "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)";
        }
        
        const position = centerOffset - (currentIndex * cardWidth);
        track.style.transform = `translateX(${position}px)`;
    }

    if (track.dataset.timer !== "1") {
        track.dataset.timer = "1";
        setInterval(() => tickCronometros(track), 1000);
    }

    // Posicionamos la primera en el centro inmediatamente
    setTimeout(() => {
        if (!track.children.length) return;
        const card = track.children[0];
        const centerOffset = (window.innerWidth / 2) - (card.offsetWidth / 2);
        track.style.transform = `translateX(${centerOffset}px)`;
    }, 100);

    // Cada 4 segundos, avanza una tarjeta y se detiene (posa)
    setInterval(moverSiguiente, 4000);
}
