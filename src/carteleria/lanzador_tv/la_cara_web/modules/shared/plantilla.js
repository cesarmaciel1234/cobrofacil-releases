/* La forma de la tele queda en el navegador. Al abrir se pinta eso y después entran los datos vivos. */

const LLAVE = "tv-plantilla-v1";

export function guardarForma(state) {
    const productos = state?.productos || [];
    if (!productos.length && !(state?.rotacion || []).length) return;
    const forma = {
        config: state.config || null,
        productos: productos.slice(0, 96),
        destacados: state.destacados || [],
        rotacion: state.rotacion || [],
        combos: state.combos || [],
        columna3: state.columna3 || [],
        ia: state.ia || [],
        hero: state.hero || null,
        climaData: state.climaData || null,
    };
    try {
        localStorage.setItem(LLAVE, JSON.stringify(forma));
    } catch (err) {
        console.error("[TV] plantilla:", err);
    }
}

export function leerForma() {
    try {
        const raw = localStorage.getItem(LLAVE);
        if (!raw) return null;
        const forma = JSON.parse(raw);
        if (!forma || typeof forma !== "object") return null;
        if (!(forma.productos || []).length && !(forma.rotacion || []).length) return null;
        return forma;
    } catch (err) {
        return null;
    }
}
