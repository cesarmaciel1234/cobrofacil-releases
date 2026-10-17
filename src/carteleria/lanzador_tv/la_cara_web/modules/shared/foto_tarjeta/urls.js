/* URLs de PNG de producto para la tarjeta. */

export const FOTO_SISTEMA = "assets/logo_sistema.svg";

export function urlsFotoProducto(item) {
    const out = [];
    const push = (u) => {
        const v = String(u || "").trim();
        if (v && !out.includes(v)) out.push(v);
    };
    const asUrl = (raw) => {
        const v = String(raw || "").trim();
        if (!v) return "";
        if (/^https?:\/\//i.test(v) || v.startsWith("data:") || v.startsWith("assets/")) return v;
        if (v.startsWith("/iconos/")) return v.replace(/\\/g, "/");
        const base = v.replace(/\\/g, "/").split("/").pop() || "";
        if (/\.(png|jpe?g|webp|svg)$/i.test(base)) return `/iconos/${base}`;
        return "";
    };
    push(asUrl(item?.icono_url));
    push(asUrl(item?.icono));
    return out;
}

export function urlIcono(item) {
    return urlsFotoProducto(item)[0] || "";
}
