/* TV4: Carrusel fluido de ofertas - Motor de franja_oferta */

import { 
    escapeHtml, 
    formatMoney, 
    htmlDealStage,
    FOTO_SISTEMA,
    urlsFotoProducto,
    nombreVitrina, 
    descuentoPct, 
    textoValidezOferta, 
    esOferta, 
    precioVigente, 
    unidadProducto 
} from "../../shared/plata_y_texto.js";

/* ── Motor de carrusel tipo desfile elegante ─────────────────────────── */

let carouselState = {
    currentIndex: 0,
    isAnimating: false,
    intervalId: null,
    pauseTime: 3000, // 3 segundos pausa por tarjeta
    transitionTime: 800, // 800ms transición suave
    itemsPerView: 2 // Cantidad de tarjetas visibles
};

function iniciarCarruselFluido(track) {
    if (carouselState.intervalId) return;
    
    const items = track.querySelectorAll('.asian-flash-product');
    if (items.length === 0) return;
    
    // Calcular cuántas tarjetas avanzar por paso
    const advanceBy = Math.max(1, Math.floor(items.length / 10)); // Avanzar 10% del total
    const itemWidth = items[0].offsetWidth + parseFloat(getComputedStyle(track).gap || 0);
    
    function moveToNext() {
        if (carouselState.isAnimating) return;
        carouselState.isAnimating = true;
        
        carouselState.currentIndex = (carouselState.currentIndex + advanceBy) % items.length;
        
        const targetPosition = -(carouselState.currentIndex * itemWidth);
        
        track.style.transition = `transform ${carouselState.transitionTime}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        track.style.transform = `translateX(${targetPosition}px)`;
        
        setTimeout(() => {
            carouselState.isAnimating = false;
            
            // Reset si llegamos al final para loop infinito
            if (carouselState.currentIndex >= items.length - advanceBy) {
                carouselState.currentIndex = 0;
                track.style.transition = 'none';
                track.style.transform = 'translateX(0)';
                setTimeout(() => {
                    track.style.transition = `transform ${carouselState.transitionTime}ms cubic-bezier(0.4, 0, 0.2, 1)`;
                }, 50);
            }
        }, carouselState.transitionTime);
    }
    
    // Iniciar el desfile
    carouselState.intervalId = setInterval(moveToNext, carouselState.pauseTime + carouselState.transitionTime);
    
    // Primera transición inmediata
    setTimeout(moveToNext, 500);
}

/* ── Carrusel de ofertas ───────────────────────────────── */

function pseudoRandom(seedStr) {
    let hash = 0;
    for (let i = 0; i < seedStr.length; i++) {
        hash = (hash << 5) - hash + seedStr.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

// Paleta de fondos vibrantes estilo Temu/Shopee — rotamos por índice del producto
const PALETA_FONDOS = [
    "linear-gradient(145deg, #FF6B6B 0%, #FFD93D 60%, #FF6B6B 100%)",   // rojo-amarillo cálido
    "linear-gradient(145deg, #6C63FF 0%, #A78BFA 60%, #EC4899 100%)",   // violeta-rosa
    "linear-gradient(145deg, #10B981 0%, #34D399 55%, #059669 100%)",   // verde esmeralda
    "linear-gradient(145deg, #F97316 0%, #FBBF24 60%, #EF4444 100%)",   // naranja fuego
    "linear-gradient(145deg, #0EA5E9 0%, #38BDF8 55%, #6366F1 100%)",   // azul cielo-índigo
    "linear-gradient(145deg, #EC4899 0%, #F9A8D4 55%, #F97316 100%)",   // rosa-durazno
];

function htmlCarruselOfertas(ofertas = []) {
    const items = ofertas.slice(0, 6);

    const itemsHtml = items.map((item, idx) => {
        const nombre = nombreVitrina(item.nombre);
        
        let precioVigenteVal = precioVigente(item) || item.precio;
        let precioOriginalVal = item.precio_original || item.precio_anterior || item.precio || precioVigenteVal;
        const esUnOfertaReal = esOferta(item);
        if (!esUnOfertaReal) {
            precioOriginalVal = precioVigenteVal;
        }

        const precioStr = formatMoney(precioOriginalVal);
        const precioVigenteStr = formatMoney(precioVigenteVal);
        const descuento = descuentoPct(precioOriginalVal, precioVigenteVal);
        const unidad = unidadProducto(item);
        const ahorro = (precioOriginalVal > precioVigenteVal) ? formatMoney(precioOriginalVal - precioVigenteVal) : "";
        const kicker = esOferta(item) ? "🔥 OFERTA" : "⭐⭐⭐⭐⭐";
        // Ventas dinámicas
        const vendidosReales = Number(item.cantidad || item.vendidos || item.cantidad_vendida || item.ventas_dia || item.ventas || item.volumen_dia || item.volumen || 0);
const ticketsReales = Number(item.tickets || item.veces || item.tickets_dia || item.cantidad_tickets || 0);
let porcentaje = 0;
let comprando = 0;
const precioVigenteNum = Number(item.precio_vigente || item.precio || 0);
const facturado = vendidosReales * precioVigenteNum;
const formatFacturado = facturado > 1000000 ? (facturado/1000000).toFixed(1) + "M" : (facturado > 1000 ? Math.round(facturado/1000) + "K" : Math.round(facturado));
        let mostrarVendido = 0;

        const tieneCondicion = esUnOfertaReal && Boolean(textoValidezOferta(item));
        if (vendidosReales > 0) {
            comprando = ticketsReales > 0 ? ticketsReales : Math.max(1, Math.ceil(vendidosReales / 2.5));
            mostrarVendido = Math.min(99, Math.round(vendidosReales));


            const stockTotal = item.stock_inicial || (vendidosReales + (item.stock || (vendidosReales < 10 ? 20 : Math.round(vendidosReales * 1.3))));
            porcentaje = Math.min(99, Math.max(5, Math.round((vendidosReales / stockTotal) * 100)));
        } else {
            const hora = new Date().getHours();
            const dia = new Date().getDate();
            const hash = pseudoRandom(nombre + dia);
            const factorHora = Math.max(1, hora - 7);
            comprando = 0;
            porcentaje = Math.min(96, 25 + (factorHora * 4.5) + (hash % 15));
            mostrarVendido = Math.floor(porcentaje * 1.2) + (hash % 10);
        }


        // Fondo vibrante rotativo por posición en la lista
        const fondo = PALETA_FONDOS[idx % PALETA_FONDOS.length];

        // Imagen PNG del producto
        const fotos = urlsFotoProducto(item);
        const iconoUrl = fotos[0] || FOTO_SISTEMA;
        const resto = fotos.slice(1).join("|");
        const imagenHtml = `<img src="${escapeHtml(iconoUrl)}" alt="${escapeHtml(nombre)}" loading="lazy" data-fallbacks="${escapeHtml(resto)}" onerror="const q=(this.dataset.fallbacks||'').split('|').filter(Boolean);if(q.length){this.src=q.shift();this.dataset.fallbacks=q.join('|');}else{this.src='${FOTO_SISTEMA}';}">`;

        return `
            <article class="asian-flash-product cascade-enter" style="animation-delay: ${idx * 0.2}s">
                <div class="asian-flash-badge">${esOferta(item) && descuento ? `-${descuento}%` : `TOP ${idx + 1}`}</div>
                <div class="asian-flash-product-image" style="background:${fondo};">
                    ${imagenHtml}
                    ${kicker ? `<div class="asian-flash-product-tag">${escapeHtml(kicker)}</div>` : ""}
                </div>
                <div class="asian-flash-product-info">
                    <div>
                        <h3 class="asian-flash-product-name">${escapeHtml(nombre)}</h3>
                          <div class="asian-flash-prices tv-card__now-box">
                              <strong class="asian-flash-current">$${escapeHtml(precioVigenteStr.replace(/^\$\s*/, ""))}</strong>
                              ${esUnOfertaReal ? `<span class="asian-flash-original">${escapeHtml(precioStr.replace(/\s+/g, ""))}</span>` : ""}
                          </div>
                          <div class="asian-flash-condition">${tieneCondicion ? escapeHtml(textoValidezOferta(item)) : "TUS VECINOS LO ELIGIERON"}</div>
                          
<div class="asian-flash-social-grid">
    <div class="social-stat">
        <span class="social-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="premium-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></span>
        <span class="social-value">${comprando}</span>
    </div>
    <div class="social-stat">
        <span class="social-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="premium-icon"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></span>
        <span class="social-value">${vendidosReales > 0 ? Math.min(99, Math.max(12, Math.round((vendidosReales / (vendidosReales + 8)) * 100))) : "0"}</span>
    </div>
    <div class="social-stat">
        <span class="social-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="premium-icon"><path d="M8 21h8"></path><path d="M12 17v4"></path><path d="M7 4h10"></path><path d="M17 4v8a5 5 0 0 1-10 0V4"></path><path d="M7 9H4.5A2.5 2.5 0 0 1 2 6.5V6a1 1 0 0 1 1-1h4"></path><path d="M17 9h2.5A2.5 2.5 0 0 0 22 6.5V6a1 1 0 0 0-1-1h-4"></path></svg></span>
        <span class="social-value">${formatFacturado}</span>
    </div>
</div>

                    </div>
                </div>
            </article>
        `;
    }).join('');
    
    // Desfile elegante: solo duplicamos suficientes para loop suave
    const infiniteScroll = itemsHtml.repeat(3); // 3 duplicaciones para desfile elegante
    
    return `
        <div class="asian-flash-container">
            <div class="chef-carousel">
                <div class="chef-carousel-track" id="columna4CarouselTrack">
                    ${infiniteScroll}
                </div>
            </div>
        </div>
    `;
}

/* ── Inicialización del carrusel ───────────────────────── */

export function iniciarCarruselColumna4() {
    const track = document.getElementById("columna4CarouselTrack");
    if (track && track.children.length > 0) {
        // Resetear estado anterior
        if (carouselState.intervalId) {
            clearInterval(carouselState.intervalId);
            carouselState.intervalId = null;
        }
        carouselState.currentIndex = 0;
        carouselState.isAnimating = false;
        
        iniciarCarruselFluido(track);
    }
}

/* ── HTML principal ──────────────────────────────────────── */

export function htmlPronosticoClima(climaData) {
    let { ofertas, producto_recomendado, precio, icono_url, departamento } = climaData || {};

    if (!ofertas || ofertas.length === 0) {
        if (producto_recomendado && Number(precio) > 0) {
            ofertas = [{
                nombre: producto_recomendado,
                precio,
                precio_oferta: precio,
                icono_url: icono_url || "",
                departamento: departamento || "",
            }];
        } else {
            ofertas = [];
        }
    }

    // Iniciar carrusel después de renderizar
    setTimeout(() => iniciarCarruselColumna4(), 100);

    return `
        <article class="chef-board professional">
            ${htmlCarruselOfertas(ofertas)}
        </article>
    `;
}
