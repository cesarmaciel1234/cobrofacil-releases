
// VFX Engine - Efectos Premium (Optimizado para escalabilidad y 24/7 uptime)

let observer = null;

export function initCenterFocus() {
    if (esEco()) return;
    // Usamos IntersectionObserver en lugar de requestAnimationFrame.
    // Esto evita recalcular layout (reflow) a 60fps, salvando muchísima CPU.
    // Creamos un margen de observación que solo detecta el centro de la pantalla (aprox 15% de ancho).
    const options = {
        root: null,
        rootMargin: "0px -42% 0px -42%", 
        threshold: 0
    };

    observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-center-focus');
            } else {
                entry.target.classList.remove('is-center-focus');
            }
        });
    }, options);
}

// Nueva función que se llama solo cuando se re-renderiza el DOM
function esEco() {
    return document.body.getAttribute("data-perf") === "eco";
}

export function updateVFX() {
    if (esEco()) {
        checkSmartMarquee();
        return;
    }
    if (observer) {
        // Desconectar observables viejos (previene memory leaks al recargar datos)
        observer.disconnect();
        // Observar las nuevas tarjetas
        document.querySelectorAll('.oferta-card').forEach(card => observer.observe(card));
    }
    
    animateOdometers();
    checkSmartMarquee();
}

function animateOdometers() {
    const odometers = document.querySelectorAll('.odometer-val:not(.counted)');
    odometers.forEach(el => {
        el.classList.add('counted');
        const finalVal = parseFloat(el.getAttribute('data-val')) || 0;
        const duration = 1200; 
        const start = performance.now();
        
        const formatNumber = (num) => Math.floor(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");

        const update = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            el.innerText = formatNumber(finalVal * easeProgress);
            
            if (progress < 1) requestAnimationFrame(update);
            else el.innerText = formatNumber(finalVal);
        };
        requestAnimationFrame(update);
    });
}

function checkSmartMarquee() {
    const names = document.querySelectorAll('.tv-card__name, .asian-rank-name, .price-row__name, .oferta-nombre, .xsell-item__name');
    names.forEach(el => {
        if (el.scrollWidth > el.clientWidth + 5) {
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
