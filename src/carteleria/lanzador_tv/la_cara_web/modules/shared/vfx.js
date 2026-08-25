
// VFX Engine - Efectos Premium para Alta Gama

export function initCenterFocus() {
    // El "Mouse Imaginario" en el centro exacto de la pantalla
    const loop = () => {
        const cards = document.querySelectorAll('.oferta-card');
        const centerX = window.innerWidth / 2;
        // Rango de "captura" del mouse imaginario (e.g. 15vw a cada lado del centro)
        const triggerWidth = window.innerWidth * 0.12; 

        cards.forEach(card => {
            const rect = card.getBoundingClientRect();
            // Calculamos el centro de la tarjeta
            const cardCenter = rect.left + (rect.width / 2);
            
            // Si el centro de la tarjeta está cerca del centro de la pantalla
            if (Math.abs(cardCenter - centerX) < triggerWidth) {
                if (!card.classList.contains('is-center-focus')) {
                    card.classList.add('is-center-focus');
                }
            } else {
                if (card.classList.contains('is-center-focus')) {
                    card.classList.remove('is-center-focus');
                }
            }
        });

        requestAnimationFrame(loop);
    };
    
    // Iniciar el loop
    requestAnimationFrame(loop);
}

export function animateOdometers() {
    // Cuenta kilómetros para precios
    const odometers = document.querySelectorAll('.odometer-val:not(.counted)');
    odometers.forEach(el => {
        el.classList.add('counted');
        const finalVal = parseFloat(el.getAttribute('data-val')) || 0;
        const duration = 1200; // 1.2 segundos
        const start = performance.now();
        
        const formatNumber = (num) => {
            // Formatear simulando el punto de miles (Argentina)
            return Math.floor(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        };

        const update = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Easing easeOutQuart
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            
            const currentVal = finalVal * easeProgress;
            el.innerText = formatNumber(currentVal);
            
            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.innerText = formatNumber(finalVal);
            }
        };
        requestAnimationFrame(update);
    });
}

export function checkSmartMarquee() {
    // Si el texto es más ancho que su contenedor, activa el scroll automático de ida y vuelta
    const names = document.querySelectorAll('.tv-card__name, .asian-rank-name, .price-row__name, .oferta-nombre');
    names.forEach(el => {
        if (el.scrollWidth > el.clientWidth + 5) {
            // Agregamos animación CSS dinamica
            if (!el.classList.contains('smart-marquee')) {
                el.classList.add('smart-marquee');
                el.style.cssText = `
                    white-space: nowrap;
                    overflow: visible;
                    animation: textPan 6s alternate infinite ease-in-out;
                `;
            }
        }
    });
    
    // Inyectar el keyframe de paneo si no existe
    if (!document.getElementById('vfx-marquee')) {
        const style = document.createElement('style');
        style.id = 'vfx-marquee';
        style.innerHTML = `
            @keyframes textPan {
                0%, 15% { transform: translateX(0); }
                85%, 100% { transform: translateX(calc(-100% + var(--marquee-width, 200px))); }
            }
        `;
        document.head.appendChild(style);
    }
}
