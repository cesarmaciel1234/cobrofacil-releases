/* Relámpago TV3: foto + bloque único de precio/condición. */

import { descuentoPct, escapeHtml, htmlDealStage, leerPrecios, nombreVitrina } from "../../shared/plata_y_texto.js";
import { htmlFilaOfertaTv } from "../../shared/precio_tv.js";

export function htmlTarjetaRelampago(item) {
    const { original, vigente, hayOferta } = leerPrecios(item);
    const nombre = nombreVitrina(item.nombre);
    const pct = hayOferta ? descuentoPct(original, vigente) : 0;
    return `
        <article class="flash-offer">
            <div class="flash-offer__deal">
                ${htmlDealStage({ ...item, nombre }, {
                    off: pct ? `-${pct}%` : "",
                    extraClass: "flash-offer__stage",
                    titulo: nombre,
                    bolt: false,
                })}
                <div class="deal-copy flash-offer__copy">
                    ${htmlFilaOfertaTv(item, {
                        caja: "tv-card__now-box",
                        ahora: "tv-card__now",
                        antes: "tv-card__was",
                        regla: "deal-save deal-line",
                        reglaTag: "p",
                    })}
                </div>
            </div>
        </article>
    `;
}
