/* Aviso de licencia: texto flotante 3 días antes. Ya no es titular. */

const DIAS_AVISO = 3;
const CICLO_LICENCIA = 30;

function diasLicenciaRestantes(config) {
    const directo = Number(config?.licencia_dias);
    if (Number.isFinite(directo)) return directo;
    const iso = String(config?.install_date || "").trim();
    if (!iso) return CICLO_LICENCIA;
    const inicio = new Date(iso);
    if (Number.isNaN(inicio.getTime())) return CICLO_LICENCIA;
    const usados = Math.floor((Date.now() - inicio.getTime()) / 86400000);
    return CICLO_LICENCIA - usados;
}

function textoAviso(dias) {
    if (dias <= 0) return "Renovación de licencia pendiente";
    if (dias === 1) return "Renová la licencia: queda 1 día";
    return `Renová la licencia: quedan ${dias} días`;
}

export function renderMensajeZocalo(config, root) {
    if (!root) return;
    const dias = diasLicenciaRestantes(config);
    const activo = dias <= DIAS_AVISO;
    document.body.classList.toggle("has-aviso-licencia", activo);
    if (!activo) {
        root.hidden = true;
        root.textContent = "";
        return;
    }
    root.hidden = false;
    root.textContent = textoAviso(dias);
}
