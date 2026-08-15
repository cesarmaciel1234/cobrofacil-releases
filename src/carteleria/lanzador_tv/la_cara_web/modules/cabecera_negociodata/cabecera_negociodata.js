/* Cabecera: logo, nombre, teléfono, estado y reloj. */

export function renderCabeceraNegocio(config, els) {
    if (config?.business_name) els.brandName.textContent = config.business_name;
    if (config?.phone && config.phone !== "No disponible") {
        els.brandPhone.textContent = config.phone;
    } else {
        els.brandPhone.textContent = "---";
    }
    const offline = config?.data_status === "offline";
    els.statusText.textContent = offline ? "Caché local" : "En línea";
    const dot = els.statusText.parentElement?.querySelector(".status-dot");
    if (dot) dot.style.background = offline ? "#FCD34D" : "var(--success-color)";
}

export function marcarCabeceraDesconectada(els) {
    if (!els?.statusText) return;
    els.statusText.textContent = "Desconectado";
    const dot = els.statusText.parentElement?.querySelector(".status-dot");
    if (dot) dot.style.background = "#EF4444";
}

export function actualizarReloj(els) {
    const now = new Date();
    if (els.clock) {
        els.clock.textContent = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    }
    if (els.flashCountdown) {
        const fin = new Date(now);
        fin.setHours(24, 0, 0, 0);
        const ms = Math.max(0, fin - now);
        const h = String(Math.floor(ms / 3600000)).padStart(2, "0");
        const m = String(Math.floor((ms % 3600000) / 60000)).padStart(2, "0");
        const s = String(Math.floor((ms % 60000) / 1000)).padStart(2, "0");
        els.flashCountdown.textContent = `${h}:${m}:${s}`;
    }
}
