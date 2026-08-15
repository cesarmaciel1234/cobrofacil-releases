/* Publicidad adaptada al listado de precios (motor_publicidad). */

import { escapeHtml, formatMoney, precioVigente } from "../../shared/plata_y_texto.js";

export function htmlTarjetaPublicidad(item) {
    const nombre = item?.nombre || "Destacado";
    const precio = precioVigente(item);
    return `
        <article class="price-ad">
            <span class="price-ad__badge">PUBLICIDAD</span>
            <div class="price-ad__body">
                <h5 class="price-ad__name">${escapeHtml(nombre)}</h5>
                ${precio > 0 ? `<strong class="price-ad__price">${formatMoney(precio)}</strong>` : ""}
            </div>
        </article>
    `;
}
