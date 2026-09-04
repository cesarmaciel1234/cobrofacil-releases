import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/shared/plata_y_texto.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """export function esPorKg(item) {
    // 1. Prioridad máxima: lo que dicte el motor del inventario (es_pesable)
    if (Number(item?.es_pesable || 0) === 1) return true;
    
    // 2. Revisar si la cantidad de oferta es fraccional
    const cant = Number(item?.cant_oferta || 0);
    if (cant > 0 && cant < 1) return true;
    
    // 3. Revisar el tipo de unidad de oferta
    const tipo = String(item?.tipo_unidad_oferta || "").trim().toLowerCase();
    if (tipo.includes("kilo") || tipo === "kg") return true;
    if (tipo.includes("unidad") || tipo === "un" || tipo === "u") return false;
    
    // 4. Inferir por nombre de corte de carne (muy preciso)
    const nombre = String(item?.nombre || "").toLowerCase();
    const pesables = ["asado", "vacio", "vacío", "costilla", "matambre", "falda", "tapa", "nalga", "cuadril", "cadril", "peceto", "bola de lomo", "bife", "entraña", "chorizo", "morcilla", "chinchulin", "bondiola", "pechito", "pollo", "pata", "muslo", "alita", "suprema", "milanesa", "picada", "roast beef", "aguja", "paleta", "osobuco", "molida", "chuleta", "lomo", "tortuguita"];
    if (pesables.some(c => nombre.includes(c))) return true;

    // 5. Revisar la unidad general (suele estar mal configurada como UN)
    const unidad = String(item?.unidad || "").trim().toUpperCase();
    if (unidad === "KG") return true;
    if (unidad === "UN" || unidad === "U" || unidad === "UNIDAD") return false;
    
    // 6. Inferir por departamento/rubro
    const rubro = String(item?.departamento || item?.categoria || item?.rubro || "").trim().toLowerCase();
    if (rubro.includes("carne") || rubro.includes("pollo") || rubro.includes("cerdo") || rubro.includes("pescado") || rubro.includes("fiambre") || rubro.includes("queso") || rubro.includes("fruta") || rubro.includes("verdura") || rubro.includes("achura") || rubro.includes("granja")) {
        return true;
    }
    
    return false;
}"""

text = re.sub(r'export function esPorKg\(item\) \{.*?return false;\n\}', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/shared/plata_y_texto.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
