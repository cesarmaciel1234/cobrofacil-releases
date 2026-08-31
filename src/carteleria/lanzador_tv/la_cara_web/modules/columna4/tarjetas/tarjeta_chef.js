/* TV4: Carrusel fluido de ofertas - Motor de franja_oferta */

import { 
    escapeHtml, 
    formatMoney, 
    htmlDealStage, 
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
        const precio = formatMoney(item.precio);
        const precioVigenteVal = precioVigente(item) || item.precio;
        const precioVigenteStr = formatMoney(precioVigenteVal);
        const descuento = descuentoPct(item.precio, precioVigenteVal);
        const unidad = unidadProducto(item);
        const ahorro = item.precio_oferta && item.precio_oferta < item.precio
            ? formatMoney(item.precio - item.precio_oferta)
            : (item.precio && precioVigenteVal < item.precio ? formatMoney(item.precio - precioVigenteVal) : "");
        const kicker = esOferta(item) ? "🔥 OFERTA" : "⭐ NUEVO";

        // Ventas dinámicas
        const vendidosReales = item.cantidad || item.vendidos || item.cantidad_vendida || item.ventas_dia || item.ventas || item.tickets_dia || item.volumen_dia || item.tickets || item.volumen || 0;
        let porcentaje = 0;
        let comprando = 0;
        if (vendidosReales > 0) {
            comprando = vendidosReales;
            const stockTotal = item.stock_inicial || (vendidosReales + (item.stock || (vendidosReales < 10 ? 20 : Math.round(vendidosReales * 1.3))));
            porcentaje = Math.min(99, Math.max(5, Math.round((vendidosReales / stockTotal) * 100)));
        } else {
            const hora = new Date().getHours();
            const dia = new Date().getDate();
            const hash = pseudoRandom(nombre + dia);
            const factorHora = Math.max(1, hora - 7);
            comprando = Math.floor((hash % 8) + (factorHora * 1.5));
            porcentaje = Math.min(96, 25 + (factorHora * 4.5) + (hash % 15));
        }

        // Fondo vibrante rotativo por posición en la lista
        const fondo = PALETA_FONDOS[idx % PALETA_FONDOS.length];

        // Imagen PNG del producto
        const iconoUrl = item.icono_url || "";
        const imagenHtml = iconoUrl
            ? `<img src="${iconoUrl}" alt="${escapeHtml(nombre)}" loading="lazy" onerror="this.style.display='none'">`
            : `<span class="prod-emoji-fallback">🥩</span>`;

        return `
            <article class="asian-flash-product cascade-enter shimmer-fx" style="animation-delay: ${idx * 0.2}s">
                <div class="asian-flash-badge">${descuento ? `-${descuento}%` : "HOT"}</div>
                <div class="asian-flash-product-image" style="background:${fondo};">${imagenHtml}</div>
                <div class="asian-flash-product-info">
                    <div>
                        <span class="asian-flash-product-tag">${escapeHtml(kicker)}</span>
                        <h3 class="asian-flash-product-name">${escapeHtml(nombre)}</h3>
                        <div class="asian-flash-prices">
                            ${esOferta(item) ? `<span class="asian-flash-original">${escapeHtml(precio)}</span>` : ""}
                            <strong class="asian-flash-current">$${escapeHtml(precioVigenteStr.replace(/^\$\s*/, ""))}</strong>
                        </div>
                        ${esOferta(item) ? `<div style="color: #FFDF00; font-size: clamp(1rem, 1.2vw, 1.3rem); font-weight: 900; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.8vh; display: inline-block; background: rgba(0,0,0,0.75); padding: 0.25em 0.6em; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">${escapeHtml(textoValidezOferta(item))}</div>` : ""}
                        <div class="asian-flash-progress card-progress">
                            <div class="asian-flash-progress-bar" style="width: ${porcentaje}%;"></div>
                            <div class="asian-flash-progress-text">${porcentaje}% VENDIDO</div>
                        </div>
                    </div>
                    <div>
                        <div class="asian-flash-social">
                            <div class="asian-flash-avatars">
                                <div class="asian-flash-avatar">👤</div>
                                <div class="asian-flash-avatar">👤</div>
                            </div>
                            <span class="asian-flash-social-text"><strong>${comprando}</strong> comprando hoy</span>
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
        ofertas = [{
            nombre: producto_recomendado || "Súper Oferta",
            precio: precio ? precio * 1.2 : 5500,
            precio_oferta: precio || 4900,
            icono_url: icono_url || "",
            departamento: departamento || "Destacados"
        }];
    }

    // Iniciar carrusel después de renderizar
    setTimeout(() => iniciarCarruselColumna4(), 100);

    return `
        <article class="chef-board professional">
            ${htmlCarruselOfertas(ofertas)}
        </article>
    `;
}
