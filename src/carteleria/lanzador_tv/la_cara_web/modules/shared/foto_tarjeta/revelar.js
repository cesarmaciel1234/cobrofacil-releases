/* Marca la foto lista. Hasta entonces la letra tapa el hueco. */

export function revelarFoto(img) {
    if (!img || img.classList.contains("is-ready")) return;
    const ok = () => {
        if (!img.naturalWidth) return;
        img.classList.toggle("is-chica", img.naturalWidth < 360);
        img.classList.add("is-ready");
    };
    if (img.complete) {
        ok();
        return;
    }
    img.addEventListener("load", ok, { once: true });
}

export function revelarFotosEn(root) {
    (root || document).querySelectorAll("img.deal-stage__img").forEach(revelarFoto);
}
