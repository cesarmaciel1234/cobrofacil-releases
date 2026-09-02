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
        
        let precioVigenteVal = precioVigente(item) || item.precio;
        let precioOriginalVal = item.precio || precioVigenteVal;
        
        // Si no hay descuento cargado en la base de datos, simulamos el "Precio Mostrador" agregando un 20% al precio mayorista para tacharlo.
        if (precioOriginalVal <= precioVigenteVal && precioVigenteVal > 0) {
            precioOriginalVal = Math.round(precioVigenteVal * 1.2);
        }

        const precioStr = formatMoney(precioOriginalVal);
        const precioVigenteStr = formatMoney(precioVigenteVal);
        const descuento = descuentoPct(precioOriginalVal, precioVigenteVal);
        const unidad = unidadProducto(item);
        const ahorro = (precioOriginalVal > precioVigenteVal) ? formatMoney(precioOriginalVal - precioVigenteVal) : "";
        const kicker = esOferta(item) ? "🔥 OFERTA" : "⭐⭐⭐⭐⭐ NUEVO";
        // Ventas dinámicas
        const vendidosReales = item.cantidad || item.vendidos || item.cantidad_vendida || item.ventas_dia || item.ventas || item.volumen_dia || item.volumen || 0;
        const ticketsReales = item.tickets || item.veces || item.tickets_dia || item.cantidad_tickets || 0;
        let porcentaje = 0;
        let comprando = 0;
        let mostrarVendido = 0;

        // Mostrar SIEMPRE la condición (ej. Llevando 2 kilos) porque en la TV todo es precio mayorista
        const tieneCondicion = true;
        if (vendidosReales > 0) {
            comprando = ticketsReales > 0 ? ticketsReales : Math.max(1, Math.floor(vendidosReales / 2));
            mostrarVendido = Math.min(99, Math.round(vendidosReales));


            const stockTotal = item.stock_inicial || (vendidosReales + (item.stock || (vendidosReales < 10 ? 20 : Math.round(vendidosReales * 1.3))));
            porcentaje = Math.min(99, Math.max(5, Math.round((vendidosReales / stockTotal) * 100)));
        } else {
            const hora = new Date().getHours();
            const dia = new Date().getDate();
            const hash = pseudoRandom(nombre + dia);
            const factorHora = Math.max(1, hora - 7);
            comprando = Math.floor((hash % 8) + (factorHora * 1.5));
            porcentaje = Math.min(96, 25 + (factorHora * 4.5) + (hash % 15));
            mostrarVendido = Math.floor(porcentaje * 1.2) + (hash % 10);
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
                <div class="asian-flash-product-image" style="background:${fondo};">
                    ${imagenHtml}
                    <div class="asian-flash-product-tag">${escapeHtml(kicker)}</div>
                </div>
                <div class="asian-flash-product-info">
                    <div>
                        <h3 class="asian-flash-product-name">${escapeHtml(nombre)}</h3>
                          <div class="asian-flash-prices">
                              ${(precioOriginalVal > precioVigenteVal) ? `<span class="asian-flash-original">${escapeHtml(precioStr)}</span>` : ""}
                              <strong class="asian-flash-current">$${escapeHtml(precioVigenteStr.replace(/^\$\s*/, ""))}</strong>
                          </div>
                          ${tieneCondicion ? `<div class="asian-flash-condition">${escapeHtml(textoValidezOferta(item))}</div>` : ""}
                          <div class="asian-flash-progress card-progress">
                            <div class="asian-flash-progress-bar" style="width: ${porcentaje}%;"></div>
                            <div class="asian-flash-progress-text">${mostrarVendido}% VENDIDO</div>
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
