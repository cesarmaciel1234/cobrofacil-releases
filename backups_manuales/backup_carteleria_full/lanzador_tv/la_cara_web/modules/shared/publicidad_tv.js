/* Un solo lugar: cada cuántas tarjetas/filas va una publicidad. */

export const PUBLICIDAD_CADA = 2;

export function esPublicidad(item) {
    const v = item?.es_publicidad;
    return v === true || v === 1 || String(v) === "1" || String(v).toLowerCase() === "true";
}

export function listarAds(productos) {
    return (productos || []).filter(esPublicidad);
}

export function alarmaPocosAds(productos) {
    const n = listarAds(productos).length;
    return n === 1 || n === 2;
}

export function poolAds(productos) {
    return listarAds(productos);
}

function nombreClave(item) {
    return String(item?.nombre || "").toLowerCase().trim();
}

export function siguienteAd(ads, adIndex, evitar) {
    if (!ads.length) return { ad: null, next: adIndex };
    const evitarClave = nombreClave(evitar);
    for (let k = 0; k < ads.length; k += 1) {
        const ad = ads[(adIndex + k) % ads.length];
        if (nombreClave(ad) !== evitarClave) {
            return { ad, next: adIndex + k + 1 };
        }
    }
    return { ad: ads[adIndex % ads.length], next: adIndex + 1 };
}

export function tocaPublicidad(contador) {
    return contador > 0 && contador % PUBLICIDAD_CADA === 0;
}

export function intercalateAds(items, productos) {
    const ads = poolAds(productos);
    const alarma = alarmaPocosAds(productos);
    const marcar = (ad) => ({ ...ad, es_publicidad: true, slot_ad: true, alarma });
    const lista = (items || []).filter((item) => !item?.slot_ad);
    if (!ads.length) return lista;
    if (!lista.length) return ads.map(marcar);
    const out = [];
    let adIndex = 0;
    let inyectadas = 0;
    lista.forEach((item, i) => {
        out.push(item);
        if (tocaPublicidad(i + 1)) {
            const { ad, next } = siguienteAd(ads, adIndex, item);
            if (ad) {
                out.push(marcar(ad));
                adIndex = next;
                inyectadas += 1;
            }
        }
    });
    if (inyectadas === 0) {
        const { ad } = siguienteAd(ads, 0, lista[lista.length - 1]);
        if (ad) out.push(marcar(ad));
    }
    return out;
}
