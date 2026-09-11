import { escapeHtml, formatMoney, htmlDealStage, leerPrecios, nombreVitrina, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlTarjetaPublicidad(item) {
    const nombre = nombreVitrina(item?.nombre || "Destacado");
    const { original, vigente, hayOferta } = leerPrecios(item);
    const precio = vigente;
    const anterior = hayOferta ? original : 0;
    const pct = anterior > precio && precio > 0
        ? Math.round(((anterior - precio) / anterior) * 100)
        : 0;
    const condicion = textoValidezOferta(item);
    const foto = item?.imagen || item?.icono_url || item?.icono || "";

    return `
        <article class="price-row price-ad is-offer${item?.alarma ? " is-ad-alarm" : ""}">
            <span class="price-row__kicker">Publicidad</span>
            ${pct ? `<span class="price-row__off">-${pct}%</span>` : `<span class="price-row__off price-row__off--hot">AD</span>`}
            ${foto ? htmlDealStage(item, { extraClass: "price-ad__stage", off: "" }) : ""}
            <header class="price-row__mast">
                <h5 class="price-row__name">${escapeHtml(nombre)}</h5>
                <span class="price-row__hair" aria-hidden="true"></span>
            </header>
            <div class="price-row__bottom">
                <div class="price-row__prices">
                    ${anterior > precio ? `<s class="price-row__was">${formatMoney(anterior)}</s>` : ""}
                    <strong class="price-row__now"><span class="deal-currency">$</span>${escapeHtml(formatMoney(precio).replace(/^\$\s*/, ""))}</strong>
                </div>
                ${condicion ? `<div class="price-row__rule">${escapeHtml(condicion)}</div>` : ""}
            </div>
        </article>
    `;
}
