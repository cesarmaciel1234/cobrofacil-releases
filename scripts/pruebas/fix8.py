import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """
        let porcentaje = 0;
        let comprando = 0;
        let mostrarVendido = 0;

        // Mostrar SIEMPRE la condición (ej. Llevando 2 kilos) porque en la TV todo es precio mayorista
        const tieneCondicion = true;

        if (vendidosReales > 0) {
            comprando = vendidosReales;
            mostrarVendido = Math.round(vendidosReales);
            const stockTotal = item.stock_inicial || (vendidosReales + (item.stock || (vendidosReales < 10 ? 20 : Math.round(vendidosReales * 1.3))));
            porcentaje = Math.min(99, Math.max(5, Math.round((vendidosReales / stockTotal) * 100)));
        } else {
            const hora = new Date().getHours();
            const dia = new Date().getDate();
            const hash = pseudoRandom(nombre + dia);
            const factorHora = Math.max(1, hora - 7);
            comprando = Math.floor((hash % 8) + (factorHora * 1.5));
            porcentaje = Math.min(96, 25 + (factorHora * 4.5) + (hash % 15));
            mostrarVendido = Math.floor(porcentaje * 1.2) + (hash % 10);
        }
"""

text = re.sub(r'\n\s*let porcentaje = 0;\s*let comprando = 0;.*?porcentaje = Math.min\(96, 25 \+ \(factorHora \* 4\.5\) \+ \(hash % 15\)\);\s*\}', replacement, text, flags=re.DOTALL)

text = text.replace('${Math.round(vendidosReales)} ${unidadProducto(item) === "kilo" ? "KILOS" : "UNID."}', '${mostrarVendido} ${unidadProducto(item) === "kilo" ? "KILOS" : "UNID."}')

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
