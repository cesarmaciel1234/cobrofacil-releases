/* Precarga los PNG visibles antes de pintar las columnas. */

import { urlsFotoProducto } from "./urls.js";

export function precargarFotosEstado(data) {
    const vistos = new Set();
    const cola = [];
    const meter = (item) => {
        if (!item || vistos.size >= 24) return;
        const src = urlsFotoProducto(item)[0];
        if (!src || vistos.has(src)) return;
        vistos.add(src);
        cola.push(src);
    };
    meter(data?.hero);
    (data?.rotacion || []).forEach((panel) => (panel.items || []).slice(0, 4).forEach(meter));
    (data?.destacados || []).slice(0, 4).forEach(meter);
    (data?.columna3 || []).slice(0, 8).forEach(meter);
    (data?.ia || []).slice(0, 6).forEach(meter);
    (data?.combos || []).slice(0, 4).forEach(meter);
    cola.forEach((src) => {
        const pre = new Image();
        pre.decoding = "async";
        pre.src = src;
    });
}
