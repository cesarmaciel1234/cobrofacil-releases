import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

# Fix 1: 5 estrellas
text = text.replace('? NUEVO', '⭐⭐⭐⭐⭐ NUEVO')
text = text.replace('⭐ NUEVO', '⭐⭐⭐⭐⭐ NUEVO')
text = text.replace('? OFERTA', '🔥 OFERTA')

# Fix 2: Tickets
replacement = """
        // Ventas dinámicas
        const vendidosReales = item.cantidad || item.vendidos || item.cantidad_vendida || item.ventas_dia || item.ventas || item.volumen_dia || item.volumen || 0;
        const ticketsReales = item.tickets || item.veces || item.tickets_dia || item.cantidad_tickets || 0;
        let porcentaje = 0;
        let comprando = 0;
        let mostrarVendido = 0;

        // Mostrar SIEMPRE la condición (ej. Llevando 2 kilos) porque en la TV todo es precio mayorista
        const tieneCondicion = true;
        if (vendidosReales > 0) {
            comprando = ticketsReales > 0 ? ticketsReales : Math.max(1, Math.floor(vendidosReales / 2));
            mostrarVendido = Math.min(99, Math.round(vendidosReales));
"""

text = re.sub(r'\n\s*// Ventas dinámicas\s*const vendidosReales = [^\n]+;\s*let porcentaje = 0;\s*let comprando = 0;\s*let mostrarVendido = 0;\s*// Mostrar SIEMPRE[^\n]+\s*const tieneCondicion = true;\s*if \(vendidosReales > 0\) \{\s*comprando = vendidosReales;\s*mostrarVendido = Math\.min\(99, Math\.round\(vendidosReales\)\);', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
