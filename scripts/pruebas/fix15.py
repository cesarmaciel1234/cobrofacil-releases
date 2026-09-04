with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna1/tarjetas/tarjeta_ranking.js", "r", encoding="utf-8") as f:
    text = f.read()

target = """function textoFamilias(item) {
    const detalle = String(item.detalle || "");
    if (detalle && !/ticket/i.test(detalle)) return detalle;
    let n = Math.round(Number(item.cantidad || 0));
    if (n < 1) {
        const match = detalle.match(/(\d+)/);
        n = match ? Number(match[1]) : 1;
    }
    if (n <= 1) return "1 familia lo eligi";
    return `${n}+ familias lo eligieron`;
}"""

replacement = """function textoFamilias(item) {
    const detalle = String(item.detalle || "");
    if (detalle && !/ticket/i.test(detalle)) return detalle;
    
    // Primero, buscar tickets reales
    let n = Number(item.tickets || item.veces || item.tickets_dia || item.cantidad_tickets || 0);
    
    // Si no hay info de tickets real, inferirlo
    if (n < 1) {
        let vol = Math.round(Number(item.cantidad || 0));
        n = Math.max(1, Math.floor(vol / 2));
        const match = detalle.match(/(\\d+)/);
        if (vol < 1 && match) n = Number(match[1]);
    }

    if (n <= 1) return "1 familia lo eligió";
    return `${n}+ familias lo eligieron`;
}"""

import re
# Just replace the whole block using regex but a lambda for replacement to avoid escape issues
text = re.sub(r'function textoFamilias\(item\)\s*\{.*?return `\$\{n\}\+ familias lo eligieron`;\s*\}', lambda _: replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna1/tarjetas/tarjeta_ranking.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
