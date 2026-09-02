import { escapeHtml, formatMoney, precioVigente, esOferta, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlTarjetaPublicidad(item) {
    const nombre = item?.nombre || "Destacado";
    const precio = precioVigente(item);
    const precioAnterior = item?.precio_original || item?.precio_anterior || item?.precio || 0;
    const descuento = item?.descuento || 0;
    const imagen = item?.imagen || "";
    const vendido = item?.cantidad || item?.vendidos || 0;
    const totalStock = item?.stock_total || 100;
    const porcentajeVendido = totalStock > 0 && vendido > 0 ? Math.round((vendido / totalStock) * 100) : 0;
    
    const tieneDescuento = descuento > 0 || (precioAnterior > 0 && precioAnterior > precio);
    const descuentoPorcentaje = tieneDescuento 
        ? (descuento > 0 ? descuento : Math.round(((precioAnterior - precio) / precioAnterior) * 100))
        : 0;
    
    const esHot = porcentajeVendido > 50 || descuentoPorcentaje > 15;
    const esOfertaEspecial = true; 
    
    const tieneCondicion = true;
    const condicion = tieneCondicion ? textoValidezOferta(item) : "";

    let badgeHTML = '';
    if (tieneDescuento) {
        badgeHTML = `<span class="luxury-badge luxury-badge--discount">-${descuentoPorcentaje}%</span>`;
    } else if (esHot) {
        badgeHTML = `<span class="luxury-badge luxury-badge--hot">🔥 HOT</span>`;
    } else if (esOfertaEspecial) {
        badgeHTML = `<span class="luxury-badge luxury-badge--hot">⚡ OFERTA</span>`;
    }
    
    return `
        <style>
            .luxury-ad-card {
                background: linear-gradient(145deg, #111111 0%, #1a1a1a 100%) !important;
                border: 1px solid #FFDF00 !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
                border-radius: 12px;
                position: relative;
                overflow: hidden;
                padding: 2.5vh 2vw;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                min-height: 100%;
            }
            .luxury-ad-card__badges {
                position: absolute;
                top: 15px; right: 0;
            }
            .luxury-badge {
                padding: 0.4vh 1vw;
                font-weight: 800;
                font-size: clamp(0.75rem, 1.2vw, 0.9rem);
                text-transform: uppercase;
                border-radius: 4px 0 0 4px;
                letter-spacing: 0.05em;
                box-shadow: -2px 2px 5px rgba(0,0,0,0.3);
            }
            .luxury-badge--hot {
                background: #000; color: #FFDF00; border: 1px solid #FFDF00; border-right: none;
            }
            .luxury-badge--discount {
                background: #FFDF00; color: #000; border: none;
            }
            .luxury-ad-card__title {
                color: #FFFFFF;
                font-size: clamp(1.4rem, 2vw, 1.7rem);
                font-weight: 600;
                margin: 0 0 1.5vh 0;
                letter-spacing: 0.01em;
                line-height: 1.2;
                padding-right: 4vw;
            }
            .luxury-ad-card__price-now {
                color: #FFDF00;
                font-size: clamp(2.5rem, 4vw, 3.5rem);
                font-weight: 800;
                line-height: 1;
            }
            .luxury-ad-card__price-before {
                color: #888888;
                font-size: clamp(1.1rem, 1.6vw, 1.4rem);
                text-decoration: line-through;
                margin-right: 1vw;
                font-weight: 500;
            }
            .luxury-ad-card__condition {
                color: #FFDF00;
                font-size: clamp(0.9rem, 1.2vw, 1.1rem);
                font-weight: 600;
                margin-top: 1.5vh;
                letter-spacing: 0.03em;
            }
        </style>
        <article class="asian-billboard-card luxury-ad-card" ${!imagen ? 'style="grid-template-columns: 1fr;"' : ''}>
            <div class="luxury-ad-card__badges">
                ${badgeHTML}
            </div>
            
            <div class="asian-billboard__main" style="position: relative; z-index: 2; display: flex; flex-direction: column; justify-content: center; height: 100%;">
                <div class="asian-billboard__content">
                    <h4 class="luxury-ad-card__title">${escapeHtml(nombre)}</h4>
                    
                    <div class="asian-billboard__price-section">
                        <div style="display: flex; align-items: baseline; flex-wrap: wrap;">
                            ${precioAnterior > 0 && precioAnterior > precio ? `
                                <span class="luxury-ad-card__price-before">${formatMoney(precioAnterior)}</span>
                            ` : ''}
                            <span class="luxury-ad-card__price-now">${formatMoney(precio)}</span>
                        </div>
                        
                        ${condicion ? `
                            <div class="luxury-ad-card__condition">
                                ${escapeHtml(condicion)}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </article>
    `;
}
