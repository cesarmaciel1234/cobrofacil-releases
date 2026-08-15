/* Plata y texto: formatea $ , detecta oferta, arma el precio vigente y limpia nombres. */

export function formatMoney(value) {
    const n = Number(value) || 0;
    const conDecimales = Math.abs(n - Math.round(n)) > 0.001;
    return new Intl.NumberFormat("es-AR", {
        style: "currency",
        currency: "ARS",
        minimumFractionDigits: conDecimales ? 2 : 0,
        maximumFractionDigits: conDecimales ? 2 : 0,
    }).format(n);
}

export function esPorKg(item) {
    const cant = Number(item?.cant_oferta || 0);
    if (cant > 0 && cant < 1) return true;
    const tipo = String(item?.tipo_unidad_oferta || "").trim().toLowerCase();
    if (tipo.includes("kilo") || tipo === "kg") return true;
    if (tipo.includes("unidad") || tipo === "un" || tipo === "u") return false;
    const unidad = String(item?.unidad || "").trim().toUpperCase();
    if (unidad === "KG") return true;
    if (unidad === "UN" || unidad === "U" || unidad === "UNIDAD") return false;
    return Number(item?.es_pesable || 0) === 1;
}

export function unidadProducto(item) {
    return esPorKg(item) ? "kilo" : "unidad";
}

export function cantMinimaOferta(item) {
    const directa = Number(item?.cant_oferta || 0);
    if (directa >= 1) return Math.round(directa);
    const match = String(item?.productos || "").match(/llev[aá]\s+(\d+(?:[.,]\d+)?)/i);
    if (match) {
        const n = Number(match[1].replace(",", "."));
        if (n >= 1) return Math.round(n);
    }
    return 2;
}

export function textoValidezOferta(item) {
    const n = cantMinimaOferta(item);
    return esPorKg(item)
        ? `válida llevando ${n} kilos o más`
        : `válida llevando ${n} unidades o más`;
}

export function esOferta(producto) {
    const precio = Number(producto?.precio || 0);
    const oferta = Number(producto?.precio_oferta || 0);
    return precio > 0 && oferta > 0 && oferta < precio;
}

export function precioVigente(producto) {
    if (!producto) return 0;
    if (esOferta(producto)) return Number(producto.precio_oferta);
    const relampago = Number(producto.precio_oferta_relampago || 0);
    const precio = Number(producto.precio || 0);
    if (relampago > 0 && (precio <= 0 || relampago < precio)) return relampago;
    return precio;
}

export function descuentoPct(original, vigente) {
    const antes = Number(original) || 0;
    const ahora = Number(vigente) || 0;
    if (antes <= 0 || ahora <= 0 || ahora >= antes) return 0;
    return Math.max(1, Math.round((1 - ahora / antes) * 100));
}

export function escapeHtml(text) {
    return String(text ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
