/* Venta cruzada: misma familia visual que el carrusel. */

import { escapeHtml, htmlDealStage, nombreVitrina } from "../../shared/plata_y_texto.js";

function productoPorNombre(productos, nombre) {
    const clave = nombreVitrina(nombre).toLowerCase();
    return (productos || []).find((item) => nombreVitrina(item.nombre).toLowerCase() === clave)
        || { nombre };
}

export function htmlTarjetaCruzada(slide, productos = []) {
    const ancla = nombreVitrina(slide.nombre || "");
    const pregunta = slide.pregunta || (ancla ? `¿LLEVÁS ${ancla.toUpperCase()}?` : "¿LLEVÁS ESTO?");
    const items = (slide.relacionados || []).slice(0, 3).map((nombre) => {
        const prod = productoPorNombre(productos, nombre);
        const limpio = nombreVitrina(prod.nombre || nombre);
        return `
            <li class="xsell-item">
                ${htmlDealStage({ ...prod, nombre: limpio }, { extraClass: "xsell-item__stage" })}
                <span class="xsell-item__name">${escapeHtml(limpio.toUpperCase())}</span>
            </li>`;
    }).join("");
    return `
        <article class="xsell-card">
            <header class="rank-head sale-head">
                <p class="rank-kicker">⚡ COMPRAS RELACIONADAS</p>
            </header>
            <p class="xsell-ask">${escapeHtml(pregunta)}</p>
            <ul class="xsell-list">${items}</ul>
        </article>
    `;
}
