/* Publicidad estilo asiático para cartelería - elementos de venta impactantes */

import { escapeHtml, formatMoney, precioVigente, esOferta, textoValidezOferta } from "../../shared/plata_y_texto.js";

export function htmlTarjetaPublicidad(item) {
    const nombre = item?.nombre || "Destacado";
    const precio = precioVigente(item);
    const precioAnterior = item?.precio_anterior || 0;
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
    
    const condicion = esOferta(item) ? textoValidezOferta(item) : "";
    
    return `
        <article class="asian-billboard-card ${esHot ? 'asian-billboard-card--hot' : ''} ${esOfertaEspecial ? 'asian-billboard-card--special' : ''}" ${!imagen ? 'style="grid-template-columns: 1fr;"' : ''}>
            <!-- Corner Badges estilo asiático -->
            <div class="asian-billboard__badges">
                ${esHot ? '<span class="asian-badge asian-badge--hot">🔥 HOT</span>' : ''}
                ${esOfertaEspecial ? '<span class="asian-badge asian-badge--special">⭐ OFERTA</span>' : ''}
                ${tieneDescuento ? `<span class="asian-badge asian-badge--discount">-${descuentoPorcentaje}%</span>` : ''}
            </div>
            
            <!-- Layout principal: imagen + contenido -->
            <div class="asian-billboard__main">
                <!-- Sección de imagen cuadrada (SOLO SI HAY IMAGEN) -->
                ${imagen ? `
                <div class="asian-billboard__image-section">
                    <div class="asian-billboard__image-container">
                        <img class="asian-billboard__image" src="${escapeHtml(imagen)}" alt="${escapeHtml(nombre)}" />
                        <div class="asian-billboard__image-overlay">
                            <span class="asian-billboard__overlay-text">OFERTA</span>
                        </div>
                    </div>
                </div>
                ` : ''}
                
                <!-- Sección de contenido -->
                <div class="asian-billboard__content">
                    <!-- Nombre del producto -->
                    <h4 class="asian-billboard__title" ${!imagen ? 'style="font-size: clamp(1.4rem, 2.2vw, 1.8rem);"' : ''}>${escapeHtml(nombre)}</h4>
                    
                    <!-- Sección de precios estilo asiático -->
                    <div class="asian-billboard__price-section">
                        <div class="asian-billboard__price-display">
                            ${precioAnterior > 0 && precioAnterior > precio ? `
                                <span class="asian-billboard__price-before">${formatMoney(precioAnterior)}</span>
                            ` : ''}
                            <span class="asian-billboard__price-now">${formatMoney(precio)}</span>
                        </div>
                        ${tieneDescuento && precioAnterior > 0 ? `
                            <span class="asian-billboard__savings">AHORRÓ ${formatMoney(precioAnterior - precio)}</span>
                        ` : ''}
                        
                        <!-- Condiciones de oferta -->
                        ${condicion ? `
                            <div style="margin-top: 0.5vh; background: linear-gradient(90deg, #F59E0B, #D97706); color: white; padding: 0.4vh 0.8vw; border-radius: 6px; font-weight: 800; font-size: clamp(0.7rem, 1vw, 0.9rem); display: inline-block; align-self: flex-start; text-transform: uppercase; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                                ${escapeHtml(condicion)}
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Social proof estilo asiático -->
                    <div class="asian-billboard__social-proof">
                        ${vendido > 0 ? `
                            <div class="asian-billboard__proof-item">
                                <span class="asian-billboard__proof-number">${vendido}</span>
                                <span class="asian-billboard__proof-label">vendidos</span>
                            </div>
                        ` : `
                            <div class="asian-billboard__proof-item" style="flex-direction: row; gap: 0.5vw; background: rgba(255,255,255,0.1); padding: 0.4vh 0.8vw; border-radius: 8px;">
                                <span class="asian-billboard__proof-number" style="color: #60A5FA;">⭐</span>
                                <span class="asian-billboard__proof-label" style="color: #E2E8F0; font-size: clamp(0.7rem, 1vw, 0.8rem);">DESTACADO</span>
                            </div>
                        `}
                        ${porcentajeVendido > 0 ? `
                            <div class="asian-billboard__proof-item">
                                <span class="asian-billboard__proof-number">${porcentajeVendido}%</span>
                                <span class="asian-billboard__proof-label">popular</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Barra de progreso estilo asiático -->
                    ${porcentajeVendido > 0 ? `
                        <div class="asian-billboard__progress-bar">
                            <div class="asian-billboard__progress-fill" style="width: ${porcentajeVendido}%"></div>
                            <span class="asian-billboard__progress-text">${porcentajeVendido}% vendido</span>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Footer con mensaje de venta -->
            <div class="asian-billboard__footer">
                <span class="asian-billboard__footer-text">⚡ PRECIOS IMBATIBLES ⚡</span>
            </div>
        </article>
    `;
}
