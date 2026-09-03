import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/shared/plata_y_texto.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """export function esPorKg(item) {
    const cant = Number(item?.cant_oferta || 0);
    if (cant > 0 && cant < 1) return true;
    const tipo = String(item?.tipo_unidad_oferta || "").trim().toLowerCase();
    if (tipo.includes("kilo") || tipo === "kg") return true;
    
    // Inferir por nombre de corte de carne (muy preciso) antes de evaluar "UN"
    const nombre = String(item?.nombre || "").toLowerCase();
    const pesables = ["asado", "vacio", "vacío", "costilla", "matambre", "falda", "tapa", "nalga", "cuadril", "cadril", "peceto", "bola de lomo", "bife", "entraña", "chorizo", "morcilla", "chinchulin", "bondiola", "pechito", "pollo", "pata", "muslo", "alita", "suprema", "milanesa", "picada", "roast beef", "aguja", "paleta", "osobuco", "molida", "chuleta", "lomo", "tortuguita"];
    if (pesables.some(c => nombre.includes(c))) return true;

    if (tipo.includes("unidad") || tipo === "un" || tipo === "u") return false;
    const unidad = String(item?.unidad || "").trim().toUpperCase();
    if (unidad === "KG") return true;
    if (unidad === "UN" || unidad === "U" || unidad === "UNIDAD") return false;
    if (Number(item?.es_pesable || 0) === 1) return true;
    
    // Inferir por departamento/rubro
    const rubro = String(item?.departamento || item?.categoria || item?.rubro || "").trim().toLowerCase();
    if (rubro.includes("carne") || rubro.includes("pollo") || rubro.includes("cerdo") || rubro.includes("pescado") || rubro.includes("fiambre") || rubro.includes("queso") || rubro.includes("fruta") || rubro.includes("verdura") || rubro.includes("achura") || rubro.includes("granja")) {
        return true;
    }
    
    return false;
}"""

# re.sub(r'export function esPorKg\(item\).*?return false;\n\}', replacement, text, flags=re.DOTALL)
# wait, . is not matching newlines unless re.DOTALL is used.
text = re.sub(r'export function esPorKg\(item\) \{.*?return false;\n\}', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/shared/plata_y_texto.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
