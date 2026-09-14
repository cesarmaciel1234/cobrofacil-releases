import { descuentoPct, escapeHtml, leerPrecios, nombreVitrina, htmlDealStage } from "../../shared/plata_y_texto.js";
import { htmlFilaOfertaTv } from "../../shared/precio_tv.js";

export function htmlTarjetaPublicidad(item) {
    const nombre = nombreVitrina(item?.nombre || "Destacado");
    const { original, vigente, hayOferta } = leerPrecios(item);
    const pct = hayOferta ? descuentoPct(original, vigente) : 0;
    const badge = pct
        ? `<span class="price-row__off">-${pct}%</span>`
        : `<span class="price-row__off price-row__off--hot">AD</span>`;

    return `
        <article class="price-row price-ad${hayOferta ? " is-offer" : ""}${item?.alarma ? " is-ad-alarm" : ""}">
            <span class="price-row__kicker">Publicidad</span>
            ${badge}
            ${htmlDealStage(item, { extraClass: "price-ad__stage", off: "" })}
            <header class="price-row__mast">
                <h5 class="price-row__name">${escapeHtml(nombre)}</h5>
                <span class="price-row__hair" aria-hidden="true"></span>
            </header>
            <div class="price-row__bottom">
                ${htmlFilaOfertaTv(item, {
                    caja: "price-row__prices",
                    ahora: "price-row__now",
                    antes: "price-row__was",
                    regla: "price-row__rule",
                    reglaTag: "div",
                })}
            </div>
        </article>
    `;
}
