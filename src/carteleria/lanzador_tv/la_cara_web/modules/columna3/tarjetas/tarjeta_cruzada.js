/* Venta cruzada: misma familia visual que el carrusel. */

import { escapeHtml, formatMoney, htmlDealStage, nombreVitrina, precioVigente, textoValidezOferta } from "../../shared/plata_y_texto.js";

function productoPorNombre(productos, nombre) {
    const clave = nombreVitrina(nombre).toLowerCase();
    const encontrado = (productos || []).find((item) => nombreVitrina(item.nombre).toLowerCase() === clave);
    if (encontrado) {
        return encontrado;
    }
    // Si no se encuentra, devuelve objeto básico solo con nombre
    return { nombre, precio: 0, precio_oferta: 0, cant_oferta: 0, tipo_unidad_oferta: "", unidad: "", es_pesable: 0 };
}

export function htmlTarjetaCruzada(slide, productos = []) {
    const ancla = nombreVitrina(slide.nombre || "");
    const pregunta = slide.pregunta || (ancla ? `¿LLEVÁS ${ancla.toUpperCase()}?` : "¿LLEVÁS ESTO?");
    const items = (slide.relacionados || []).slice(0, 3).map((nombre) => {
        const prod = productoPorNombre(productos, nombre);
        const limpio = nombreVitrina(prod.nombre || nombre);
        
        // Solo mostrar precio y condiciones si el producto existe realmente en BD
        const tienePrecio = prod.precio > 0 || prod.precio_oferta > 0;
        const tieneOferta = prod.precio_oferta > 0 && prod.precio_oferta < prod.precio;
        const precio = tieneOferta ? precioVigente(prod) : (prod.precio || 0);
        const regla = tieneOferta ? textoValidezOferta(prod) : "";
        
        return `
            <li class="xsell-item">
                ${htmlDealStage({ ...prod, nombre: limpio }, { extraClass: "xsell-item__stage" })}
                <div class="xsell-item__info">
                    <div class="xsell-item__text">
                        <span class="xsell-item__name">${escapeHtml(limpio.toUpperCase())}</span>
                        ${regla ? `<span class="xsell-item__rule">${escapeHtml(regla)}</span>` : ""}
                    </div>
                    ${tienePrecio ? `<span class="xsell-item__price">${formatMoney(precio)}</span>` : ""}
                </div>
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
