const params = new URLSearchParams(location.search);
const nombreSugerido = (params.get("nombre") || "").trim();
let preset = "carteleria";
let archivo = null;
let resultado = null;
let rotationAngle = 0;
let uploadId = "";
let convertAbort = null;

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const dropLabel = document.getElementById("dropLabel");
const imgOrig = document.getElementById("imgOrig");
const imgRes = document.getElementById("imgRes");
const phRes = document.getElementById("phRes");
const busyEl = document.getElementById("busy");
const statusEl = document.getElementById("status");
const subtitulo = document.getElementById("subtitulo");
const btnConvertir = document.getElementById("btnConvertir");
const btnUsar = document.getElementById("btnUsar");
const btnCancelar = document.getElementById("btnCancelar");
const chkIa = document.getElementById("chkIa");

if (nombreSugerido) {
    const visible = nombreSugerido.replace(/_/g, " ");
    subtitulo.textContent = visible.charAt(0).toUpperCase() + visible.slice(1);
}

const styleBtns = document.querySelectorAll(".filter-btn[data-id]");
styleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        styleBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        preset = btn.dataset.id;
        updateLiveControls();
        if (resultado) triggerFastConversion();
    });
});

function mostrarOriginal(file) {
    archivo = file;
    uploadId = "";
    rotationAngle = 0;
    imgOrig.style.transform = '';
    imgOrig.src = URL.createObjectURL(file);
    imgOrig.classList.remove("hidden");
    dropLabel.classList.add("hidden");
    resultado = null;
    imgRes.classList.add("hidden");
    phRes.classList.remove("hidden");
    phRes.textContent = "Todava no hay resultado";
    btnConvertir.disabled = false;
    btnUsar.classList.add("hidden");
    document.getElementById('btnBgToggle').classList.add("hidden");
    setStatus("");
}

fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) mostrarOriginal(fileInput.files[0]);
});

imgOrig.addEventListener("click", () => fileInput.click());

["dragenter", "dragover"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropLabel.classList.add("over");
    });
});
["dragleave", "drop"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropLabel.classList.remove("over");
    });
});
dropZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) mostrarOriginal(file);
});

function setStatus(text, isError) {
    statusEl.textContent = text || "";
    statusEl.classList.toggle("error", !!isError);
}

function setBusy(on) {
    busyEl.classList.toggle("hidden", !on);
    btnConvertir.disabled = on || !archivo;
    btnUsar.disabled = on || !resultado;
}

async function convertir(isFast = false) {
    if (!archivo) return;
    if (convertAbort) convertAbort.abort();
    convertAbort = new AbortController();
    setBusy(true);
    setStatus(isFast ? "Ajustando..." : "Procesando...");
    const data = new FormData();
    if (uploadId && isFast) {
        data.append("upload_id", uploadId);
        data.append("fast", "1");
    } else {
        data.append("file", archivo);
    }
    data.append("preset", preset);
    data.append("save_as", nombreSugerido);
    data.append("rotation", String(rotationAngle || 0));
    if (sliderRocio) data.append("water_droplets_density", sliderRocio.value);
    if (chkIa.checked) data.append("use_ai", "1");
    try {
        const res = await fetch("/convert", { method: "POST", body: data, signal: convertAbort.signal });
        const json = await res.json();
        if (!res.ok || !json.success) {
            throw new Error(json.error || "No se pudo convertir");
        }
        resultado = json;
        if (json.upload_id) uploadId = json.upload_id;
        imgRes.src = json.converted_image + "?t=" + Date.now();
        imgRes.classList.remove("hidden");
        phRes.classList.add("hidden");
        btnUsar.classList.remove("hidden");
        document.getElementById('btnBgToggle').classList.remove("hidden");
        btnUsar.disabled = false;
        updateLiveControls();
        setStatus("Listo");
    } catch (err) {
        if (err.name === "AbortError") return;
        setStatus(err.message || "Error", true);
    } finally {
        setBusy(false);
    }
}

btnConvertir.addEventListener("click", convertir);
btnUsar.addEventListener("click", () => {
    if (!resultado || !resultado.filename) return;
    document.title = "CREADOR_PNG_DONE:" + resultado.filename;
});
btnCancelar.addEventListener("click", () => {
    document.title = "CREADOR_PNG_CANCEL";
});

// Background Preview Toggle
const btnBgToggle = document.getElementById('btnBgToggle');
const resBody = document.getElementById('resBody');
const backgrounds = [
    { name: 'Fondo: Transparente', css: '' }, 
    { name: 'Fondo: Pantalla TV (Oscuro)', css: 'linear-gradient(to bottom right, #0f172a, #1e293b)' },
    { name: 'Fondo: Oferta (Rojo)', css: 'linear-gradient(to bottom right, #dc2626, #991b1b)' },
    { name: 'Fondo: Web (Blanco)', css: '#ffffff' }
];
let currentBg = 0;

btnBgToggle.addEventListener('click', () => {
    currentBg = (currentBg + 1) % backgrounds.length;
    const bg = backgrounds[currentBg];
    btnBgToggle.textContent = bg.name;
    
    if (currentBg === 0) {
        resBody.style.backgroundImage = '';
        resBody.style.backgroundColor = '';
    } else {
        resBody.style.backgroundImage = bg.css.includes('gradient') ? bg.css : 'none';
        resBody.style.backgroundColor = bg.css.includes('gradient') ? '' : bg.css;
    }
});



const btnRotar = document.getElementById('btnRotar');
if (btnRotar) {
    btnRotar.addEventListener('click', () => {
        rotationAngle = (rotationAngle + 90) % 360; // rotate left to right visually usually 90deg CW but since css rotates CW we do positive or negative
        imgOrig.style.transform = 'rotate(' + rotationAngle + 'deg)';
    });
}


const liveControls = document.getElementById('liveControls');
const rocioControl = document.getElementById('rocioControl');
const sliderRocio = document.getElementById('sliderRocio');
const chkVignette = document.getElementById('chkVignette');

function updateLiveControls() {
    if (resultado) {
        liveControls.classList.remove('hidden');
        if (preset === 'frio_rocio') {
            rocioControl.classList.remove('hidden');
        } else {
            rocioControl.classList.add('hidden');
        }
    } else {
        liveControls.classList.add('hidden');
    }
}

let timeoutId;
function triggerFastConversion() {
    if (!resultado) return; // Only fast convert if we already have a base
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
        convertir(true); // pass true for fast conversion
    }, 400); // debounce
}

sliderRocio.addEventListener('input', triggerFastConversion);
chkVignette.addEventListener('change', triggerFastConversion);


