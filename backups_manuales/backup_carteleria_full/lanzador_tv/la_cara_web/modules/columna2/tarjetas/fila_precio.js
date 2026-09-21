/* Grilla de precios: mismo bloque de oferta que el resto de la TV. */

import { descuentoPct, escapeHtml, leerPrecios, nombreVitrina } from "../../shared/plata_y_texto.js";
import { htmlFilaOfertaTv } from "../../shared/precio_tv.js";

export function htmlFilaPrecio(item) {
    const { original, vigente, hayOferta } = leerPrecios(item);
    const pct = hayOferta ? descuentoPct(original, vigente) : 0;
    return `
        <article class="price-row${hayOferta ? " is-offer" : ""}">
            ${hayOferta && pct ? `<span class="price-row__off">-${pct}%</span>` : ""}
            <header class="price-row__mast">
                <h5 class="price-row__name">${escapeHtml(nombreVitrina(item.nombre) || "Producto")}</h5>
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
