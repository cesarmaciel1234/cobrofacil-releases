/* Plata y texto: formatea $ , detecta oferta, arma el precio vigente y limpia nombres. */

export function nombreVitrina(nombre) {
    const original = String(nombre || "").trim();
    const limpio = original.replace(/^oferta\s+(?:de\s+)?/i, "").trim() || original;
    if (!limpio) return original;
    
    // Corrección de errores comunes en nombres de productos
    const corregido = corregirErroresComunes(limpio);
    
    return corregido.replace(/^\p{L}/u, (ch) => ch.toUpperCase());
}

function corregirErroresComunes(nombre) {
    const correcciones = {
        'asadc': 'asado',
        'asado c': 'asado',
        'asadoc': 'asado',
        'pollo entero c': 'pollo entero',
        'pollo c': 'pollo entero',
        'bondiola c': 'bondiola',
        'bife c': 'bife',
        'milanesa c': 'milanesa',
    };
    
    const nombreLower = nombre.toLowerCase();
    for (const [error, correcto] of Object.entries(correcciones)) {
        if (nombreLower === error || nombreLower.endsWith(' ' + error)) {
            return nombreLower.replace(error, correcto);
        }
    }
    
    return nombre;
}

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
    if (Number(item?.es_pesable || 0) === 1) return true;
    
    // Inferir por departamento/rubro si la DB no está completa
    const rubro = String(item?.departamento || item?.categoria || item?.rubro || "").trim().toLowerCase();
    if (rubro.includes("carne") || rubro.includes("pollo") || rubro.includes("cerdo") || rubro.includes("pescado") || rubro.includes("fiambre") || rubro.includes("queso") || rubro.includes("fruta") || rubro.includes("verdura") || rubro.includes("achura") || rubro.includes("granja")) {
        return true;
    }
    
    // Inferir por nombre del producto como último recurso
    const nombre = String(item?.nombre || "").toLowerCase();
    const pesables = ["asado", "vacio", "vacío", "costilla", "matambre", "falda", "tapa", "nalga", "cuadril", "peceto", "bola de lomo", "bife", "entraña", "chorizo", "morcilla", "chinchulin", "bondiola", "pechito", "pollo", "pata", "muslo", "alita", "suprema", "milanesa", "picada", "roast beef", "aguja", "paleta", "osobuco", "molida", "chuleta"];
    if (pesables.some(c => nombre.includes(c))) return true;
    
    return false;
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
        ? `Llevando ${n} kilos o más`
        : `Llevando ${n} unidades o más`;
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

export function letraVitrina(nombre) {
    const texto = nombreVitrina(nombre);
    return (texto.match(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/) || ["•"])[0].toUpperCase();
}

export function tonoDepto(item) {
    const d = `${item?.departamento || ""} ${item?.categoria || ""} ${item?.nombre || ""}`.toLowerCase();
    if (/ave|pollo|pavo|gallina|alita|suprema|pechuga/.test(d)) return "aves";
    if (/cerdo|bondiola|chorizo|lech[oó]n|jam[oó]n/.test(d)) return "cerdo";
    if (/almac[eé]n|fideo|aceite|arroz|bebida|l[aá]cteo/.test(d)) return "almacen";
    return "carnes";
}

export function slugNombre(nombre) {
    return nombreVitrina(nombre)
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_|_$/g, "")
        .slice(0, 60);
}

const ALIAS_PNG = {
    suprema: "suprema.png",
    pechuga: "pechuga.png",
    bife_chorizo: "bife_de_chorizo.png",
    milanesa_de_pollo: "milanesa_pollo.png",
};

export function urlIcono(item) {
    const raw = String(item?.icono_url || item?.icono || "").trim();
    if (raw.startsWith("/iconos/")) return raw;
    if (/^[\w.\- ]+\.(png|jpe?g|webp|svg)$/i.test(raw)) return `/iconos/${raw}`;
    const slug = slugNombre(item?.nombre || "");
    if (!slug) return "";
    const alias = ALIAS_PNG[slug];
    if (alias) return `/iconos/${alias}`;
    return `/iconos/${slug}.png`;
}

export function htmlDealStage(item, { off = "", extraClass = "", titulo = "", bolt = true } = {}) {
    const assignedRaw = String(item?.icono || "").trim();
    let assignedUrl = "";
    if (assignedRaw.startsWith("/iconos/")) assignedUrl = assignedRaw;
    else if (/^[\w.\- ]+\.(png|jpe?g|webp|svg)$/i.test(assignedRaw)) assignedUrl = `/iconos/${assignedRaw}`;
    const slug = slugNombre(item?.nombre);
    const slugUrl = slug ? `/iconos/${ALIAS_PNG[slug] || `${slug}.png`}` : "";
    const computedRaw = String(item?.icono_url || "").trim();
    let computedUrl = "";
    if (computedRaw.startsWith("/iconos/")) computedUrl = computedRaw;
    else if (/^[\w.\- ]+\.(png|jpe?g|webp|svg)$/i.test(computedRaw)) computedUrl = `/iconos/${computedRaw}`;
    const urls = [assignedUrl, computedUrl, slugUrl].filter((u, i, arr) => u && arr.indexOf(u) === i);
    const url = urls[0] || "";
    const fallback = urls[1] || "";
    const letra = letraVitrina(item?.nombre);
    const onerr = fallback
        ? `if(this.dataset.fallback){const u=this.dataset.fallback;this.removeAttribute('data-fallback');this.src=u;}else{this.remove();}`
        : `this.remove()`;
    return `
        <div class="deal-stage${extraClass ? ` ${extraClass}` : ""}" data-tone="${escapeHtml(tonoDepto(item))}">
            ${url ? `<img class="deal-stage__img" src="${escapeHtml(url)}" alt="" ${fallback ? `data-fallback="${escapeHtml(fallback)}"` : ""} onerror="${onerr}">` : ""}
            <span class="deal-stage__letter${url ? " has-img" : ""}">${escapeHtml(letra)}</span>
            ${titulo ? `<span class="deal-stage__name">${escapeHtml(titulo)}</span>` : ""}
            ${off ? `<span class="deal-stage__off">${escapeHtml(off)}</span>` : ""}
        </div>
    `;
}

export function escapeHtml(text) {
    return String(text ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
