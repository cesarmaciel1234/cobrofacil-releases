/* Columna 4: lobo chef + clima + recomendación del momento. */

import { htmlPronosticoClima } from "./tarjetas/tarjeta_chef.js";
import { nombreVitrina } from "../shared/plata_y_texto.js";

function esNoche() {
    const hora = new Date().getHours();
    return hora >= 18 || hora < 6;
}

function climaVisible(climaData, ia) {
    if (climaData?.producto_recomendado) return climaData;
    const pollo = (ia || []).find((item) => /pollo entero/i.test(item.nombre || ""));
    return {
        temperatura: climaData?.temperatura || "22°C",
        mensaje: esNoche()
            ? "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
            : "PARA ESTE MOMENTO DEL DÍA, TE RECOMENDAMOS LLEVAR",
        producto_recomendado: pollo?.nombre || "POLLO ENTERO",
        precio: pollo?.precio || 4900,
    };
}

export function renderColumna4(ia, root, climaData = null, productos = []) {
    const data = { ...climaVisible(climaData, ia) };
    const clave = nombreVitrina(data.producto_recomendado).toLowerCase();
    const hit = (productos || []).find((item) => nombreVitrina(item.nombre).toLowerCase() === clave);
    if (hit) {
        data.icono_url = hit.icono_url || data.icono_url;
        data.departamento = hit.departamento || hit.categoria || data.departamento;
    }
    root.innerHTML = htmlPronosticoClima(data);
}
