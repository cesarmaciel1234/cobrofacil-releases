/* Publicidad estilo asiático para cartelería - elementos de venta impactantes */

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
    
    // Forzar que TODAS las publicidades tengan el borde dorado y el estilo impactante,
    // ya que al ser publicidades queremos que resalten y luzcan premium.
    const esHot = porcentajeVendido > 50 || descuentoPorcentaje > 15;
    const esOfertaEspecial = true; 
    
    // Mostrar siempre la condición porque en la TV todo es precio mayorista
    const tieneCondicion = true;
    const condicion = tieneCondicion ? textoValidezOferta(item) : "";
    
    return `
        <style>
            .luxury-ad-card {
                background: linear-gradient(145deg, #111111 0%, #1a1a1a 100%) !important;
                border: 2px solid #FFDF00 !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5), inset 0 0 15px rgba(255, 223, 0, 0.1) !important;
                border-radius: 12px;
                position: relative;
                overflow: hidden;
                padding: 1.5vh 1.5vw;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .luxury-ad-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, #FFDF00, transparent);
            }
            .luxury-ad-card__badges {
                position: absolute;
                top: 10px; right: -5px;
                display: flex;
                flex-direction: column;
                gap: 5px;
                align-items: flex-end;
            }
            .luxury-badge {
                padding: 0.3vh 0.8vw;
                font-weight: 900;
                font-size: clamp(0.7rem, 1vw, 0.85rem);
                text-transform: uppercase;
                border-radius: 4px 0 0 4px;
                letter-spacing: 0.05em;
                box-shadow: -2px 2px 5px rgba(0,0,0,0.5);
            }
            .luxury-badge--hot {
                background: #000; color: #FFDF00; border: 1px solid #FFDF00; border-right: none;
            }
            .luxury-badge--discount {
                background: linear-gradient(90deg, #FFDF00, #FFA500); color: #000; border: none;
            }
            .luxury-ad-card__title {
                color: #FFF;
                font-size: clamp(1.4rem, 2.2vw, 1.8rem);
                font-weight: 800;
                margin: 0 0 1vh 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
                letter-spacing: 0.02em;
            }
            .luxury-ad-card__price-now {
                color: #FFDF00;
                font-size: clamp(2rem, 3.5vw, 3rem);
                font-weight: 900;
                text-shadow: 0 0 15px rgba(255, 223, 0, 0.4);
            }
            .luxury-ad-card__price-before {
                color: #888;
                font-size: clamp(1rem, 1.5vw, 1.2rem);
                text-decoration: line-through;
                margin-right: 1vw;
            }
            .luxury-ad-card__savings {
                display: inline-block;
                background: rgba(255, 223, 0, 0.1);
                color: #FFDF00;
                border: 1px solid rgba(255, 223, 0, 0.3);
                padding: 0.3vh 0.8vw;
                border-radius: 6px;
                font-weight: 800;
                font-size: clamp(0.75rem, 1.1vw, 0.9rem);
                margin-top: 0.5vh;
            }
            .luxury-ad-card__footer {
                margin-top: 1.5vh;
                background: linear-gradient(90deg, #FFDF00, #FFA500, #FFDF00);
                color: #000;
                text-align: center;
                padding: 0.6vh;
                border-radius: 4px;
                font-weight: 900;
                font-size: clamp(0.8rem, 1.2vw, 1rem);
                letter-spacing: 0.1em;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            }
        </style>
        <article class="asian-billboard-card luxury-ad-card" ${!imagen ? 'style="grid-template-columns: 1fr;"' : ''}>
            <!-- Corner Badges -->
            <div class="luxury-ad-card__badges">
                ${esHot ? '<span class="luxury-badge luxury-badge--hot">🔥 HOT</span>' : ''}
                ${esOfertaEspecial ? '<span class="luxury-badge luxury-badge--hot">⭐ OFERTA</span>' : ''}
                ${tieneDescuento ? `<span class="luxury-badge luxury-badge--discount">-${descuentoPorcentaje}%</span>' : ''}
            </div>
            
            <div class="asian-billboard__main" style="position: relative; z-index: 2;">
                <div class="asian-billboard__content">
                    <h4 class="luxury-ad-card__title">${escapeHtml(nombre)}</h4>
                    
                    <div class="asian-billboard__price-section">
                        <div style="display: flex; align-items: baseline;">
                            ${precioAnterior > 0 && precioAnterior > precio ? `
                                <span class="luxury-ad-card__price-before">${formatMoney(precioAnterior)}</span>
                            ` : ''}
                            <span class="luxury-ad-card__price-now">${formatMoney(precio)}</span>
                        </div>
                        ${tieneDescuento && precioAnterior > 0 ? `
                            <div class="luxury-ad-card__savings">AHORRÓ ${formatMoney(precioAnterior - precio)}</div>
                        ` : ''}
                        
                        <!-- Condiciones de oferta -->
                        ${condicion ? `
                            <div style="margin-top: 1.2vh; color: #000; font-size: clamp(0.85rem, 1.1vw, 1.2rem); font-weight: 900; letter-spacing: 0.05em; text-transform: uppercase; display: inline-block; align-self: flex-start; background: linear-gradient(90deg, #FFDF00, #FFA500, #FFDF00); padding: 0.4em 1em; border-radius: 50px; box-shadow: 0 0 15px rgba(255, 215, 0, 0.8), inset 0 2px 4px rgba(255,255,255,0.8); border: 2px solid #FFF; text-shadow: 1px 1px 0px rgba(255,255,255,0.5); animation: pulseGold 2s infinite;">
                                ${escapeHtml(condicion)}
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="asian-billboard__social-proof" style="margin-top: 1vh;">
                        <div class="asian-billboard__proof-item" style="flex-direction: row; gap: 0.5vw; background: rgba(255,223,0,0.1); padding: 0.4vh 0.8vw; border-radius: 8px; border: 1px solid rgba(255,223,0,0.2);">
                            <span style="color: #FFDF00;">⭐</span>
                            <span style="color: #FFDF00; font-size: clamp(0.7rem, 1vw, 0.8rem); font-weight: 800;">SELECCIÓN PREMIUM</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="luxury-ad-card__footer">
                ⚡ PRECIOS IMBATIBLES ⚡
            </div>
        </article>
    `;
}
