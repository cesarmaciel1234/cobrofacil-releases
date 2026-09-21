/* Cabecera: logo, nombre, teléfono, estado y reloj. */

export function renderCabeceraNegocio(config, els) {
    if (config?.business_name && els.brandName) els.brandName.textContent = config.business_name;
    if (config?.phone && config.phone !== "No disponible" && els.brandPhone) {
        els.brandPhone.textContent = config.phone;
    } else if (els.brandPhone) {
        els.brandPhone.textContent = "---";
    }
    
    // Inyectar el nombre del negocio automáticamente en las marquesinas de ofertas relámpago
    if (config?.business_name) {
        const nombreNegocio = config.business_name.toUpperCase();
        const marqueeCycles = document.querySelectorAll(".flash-strip__cycle");
        marqueeCycles.forEach(cycle => {
            const unidad = `<span>${nombreNegocio}</span><span class="flash-dot">·</span>`;
            cycle.innerHTML = unidad.repeat(6);
        });

        // Actualizar marquesina inferior (zocalo) si existe
        if (els.marquee) {
            const marqueeText = els.marquee.querySelector(".marquee-text");
            if (marqueeText) {
                marqueeText.textContent = `Bienvenido a ${nombreNegocio} 💎 Los mejores precios 💎 Calidad VIP 💎`;
            }
        }
    }

    const offline = config?.data_status === "offline";
    if (els.statusText) {
        els.statusText.textContent = offline ? "Caché local" : "En línea";
        const dot = els.statusText.parentElement?.querySelector(".status-dot");
        if (dot) dot.style.background = offline ? "#FCD34D" : "var(--success-color)";
    }
}

export function marcarCabeceraDesconectada(els) {
    if (!els?.statusText) return;
    els.statusText.textContent = "Desconectado";
    const dot = els.statusText.parentElement?.querySelector(".status-dot");
    if (dot) dot.style.background = "#EF4444";
}

export function actualizarReloj(els) {
    const now = new Date();
    const h = now.getHours();
    const m = now.getMinutes();
    const s = now.getSeconds();
    if (els.clock) {
        const hm = els.clock.querySelector(".clock-hm");
        const sec = els.clock.querySelector(".clock-sec");
        const hh = String(h).padStart(2, "0");
        const mm = String(m).padStart(2, "0");
        const ss = String(s).padStart(2, "0");
        if (hm && sec) {
            hm.textContent = `${hh}:${mm}`;
            sec.textContent = ss;
        } else {
            els.clock.textContent = `${hh}:${mm}:${ss}`;
        }
        els.clock.style.setProperty("--rot-h", `${(h % 12) * 30 + m * 0.5}deg`);
        els.clock.style.setProperty("--rot-m", `${m * 6 + s * 0.1}deg`);
        els.clock.style.setProperty("--rot-s", `${s * 6}deg`);
    }
    if (els.flashCountdown) {
        const fin = new Date(now);
        const nextBlock = Math.floor(now.getMinutes() / 30) * 30 + 30;
        fin.setMinutes(nextBlock, 0, 0);
        const ms = Math.max(0, fin - now);
        const min = String(Math.floor(ms / 60000)).padStart(2, "0");
        const seg = String(Math.floor((ms % 60000) / 1000)).padStart(2, "0");
        els.flashCountdown.textContent = `${min}:${seg}`;
    }
}
