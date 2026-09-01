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
    const kicker = esAd ? "Publicidad" : (enOferta ? "Ofertas" : "Precio especial");
    const tieneCondicion = true;

    return `
        <article class="tv-card ${esAd ? "tv-card--ad" : ""}">
            <div class="tv-card__inner">
                ${htmlDealStage({ ...producto, nombre }, { off: pct ? `-${pct}%` : "", titulo: nombre })}
                <div class="tv-card__copy">
                    <p class="tv-card__kicker">${escapeHtml(kicker)}</p>
                    <div class="tv-card__price-row">
                        ${vigente > 0
                            ? `<strong class="tv-card__now"><span class="deal-currency">$</span><span class="odometer-val" data-val="${vigente}">${escapeHtml(monto)}</span></strong>`
                            : `<strong class="tv-card__now">DESTACADO</strong>`}
                        ${enOferta ? `<s class="tv-card__was" style="font-size: 0.85em; opacity: 0.8;">${formatMoney(original)}</s>` : ""}
                    </div>
                    ${ahorro > 0 ? `<p class="deal-save" style="margin-bottom: 0.5vh;">Ahorro: ${formatMoney(ahorro)} / ${unidad}</p>` : ""}
                    
                    ${tieneCondicion ? `<div style="color: #000; font-size: clamp(0.7rem, 0.9vw, 1rem); font-weight: 900; letter-spacing: 0.05em; text-transform: uppercase; display: inline-block; background: linear-gradient(90deg, #FFDF00, #FFA500, #FFDF00); padding: 0.25em 0.8em; border-radius: 50px; box-shadow: 0 0 10px rgba(255, 215, 0, 0.6), inset 0 2px 4px rgba(255,255,255,0.8); border: 2px solid #FFF; text-shadow: 1px 1px 0px rgba(255,255,255,0.5); animation: pulseGold 2s infinite;">${escapeHtml(textoValidezOferta(producto))}</div>` : ""}
                </div>
            </div>
        </article>
    `;
}

function textoValidezOferta(p) {
    const min = cantMinimaOferta(p);
    const u = unidadProducto(p) === "kilo" ? "kg" : "un.";
    return p.stock > 0 && p.stock <= 8 ? "¡Últimas unidades!" : `Llevá ${min}+ ${u}`;
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
    // Inicialmente track estÃ¡ a la izquierda.
    track.style.transition = "transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)";
    
    function moverSiguiente() {
        if (!track.children.length) return;
        
        const card = track.children[0];
        const gap = window.innerWidth * 0.014; // 1.4vw
        const cardWidth = card.offsetWidth + gap;
        
        // Calculamos offset para que la tarjeta actual quede en el centro de la pantalla
        const centerOffset = (window.innerWidth / 2) - (card.offsetWidth / 2);
        
        currentIndex++;
        
        // Si llegamos a la mitad (porque el html estÃ¡ duplicado), reiniciamos sin transiciÃ³n
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


