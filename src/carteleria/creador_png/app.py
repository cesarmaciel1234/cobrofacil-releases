import os
import sys
import tempfile
import threading
import uuid

if getattr(sys, "frozen", False):
    try:
        import importlib.metadata as _md

        _orig_ver = _md.version

        def _version_ok(name):
            try:
                return _orig_ver(name)
            except _md.PackageNotFoundError:
                return "0"

        _md.version = _version_ok
    except Exception:
        pass

from flask import Flask, request, render_template, send_from_directory, jsonify

try:
    from src.carteleria.creador_png.presets import PRESETS
except ImportError:
    from presets import PRESETS


def _dir_recursos():
    rel = os.path.join("src", "carteleria", "creador_png")
    candidatos = [os.path.dirname(os.path.abspath(__file__))]
    try:
        from src.utils.paths import get_resource_path, get_base_path
        candidatos.extend([
            get_resource_path(rel),
            os.path.join(get_base_path(), "_internal", rel),
            os.path.join(get_base_path(), rel),
        ])
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", "")
            exe_dir = os.path.dirname(sys.executable)
            candidatos.extend([
                os.path.join(meipass, rel) if meipass else "",
                os.path.join(exe_dir, "_internal", rel),
            ])
    except Exception:
        pass
    for path in candidatos:
        if path and os.path.isdir(os.path.join(path, "templates")):
            return path
    return candidatos[0]


def _dir_writable(nombre):
    try:
        from src.utils.paths import get_base_path
        base = os.path.join(get_base_path(), "creador_png_tmp", nombre)
    except Exception:
        base = os.path.join(tempfile.gettempdir(), "tpv_creador_png", nombre)
    os.makedirs(base, exist_ok=True)
    return base


def _dir_png_productos():
    try:
        from src.carteleria.assets_paths import png_productos_dir
        return png_productos_dir()
    except Exception:
        dest = os.path.join(_dir_writable("png_productos"))
        os.makedirs(dest, exist_ok=True)
        return dest


_convert_lock = threading.Lock()
_DIR = _dir_recursos()

app = Flask(
    __name__,
    template_folder=os.path.join(_DIR, "templates"),
    static_folder=os.path.join(_DIR, "static"),
)
app.config["UPLOAD_FOLDER"] = _dir_writable("uploads")
app.config["CONVERTED_FOLDER"] = _dir_writable("converted")
app.config["CARTELERIA_FOLDER"] = _dir_png_productos()
app.config["SCRIPT_PATH"] = os.path.join(_DIR, "convertir_imagen.py")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["CONVERTED_FOLDER"], exist_ok=True)
os.makedirs(app.config["CARTELERIA_FOLDER"], exist_ok=True)


@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "app": "creador_png"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_carteleria_png", methods=["POST"])
def upload_carteleria_png():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = file.filename
    filepath = os.path.join(app.config["CARTELERIA_FOLDER"], filename)
    file.save(filepath)
    return jsonify({"success": True, "filename": filename})


def _nombre_archivo(save_as, output_dir):
    raw = (save_as or "").strip()
    if not raw:
        return str(uuid.uuid4()) + ".png"
    for ch in '/\\:*?"<>|':
        raw = raw.replace(ch, "")
    raw = raw.replace(" ", "_").strip("._") or "producto"
    if not raw.lower().endswith(".png"):
        raw += ".png"
    if not os.path.exists(os.path.join(output_dir, raw)):
        return raw
    stem, ext = os.path.splitext(raw)
    n = 1
    while os.path.exists(os.path.join(output_dir, f"{stem}_{n}{ext}")):
        n += 1
    return f"{stem}_{n}{ext}"


def get_conversion_params(form_data):
    presets = PRESETS
    preset_name = (form_data.get("preset") or "carteleria").strip().lower()
    base = dict(presets.get(preset_name) or presets["carteleria"])
    params = {
        "black_threshold": int(form_data.get("black_threshold", base["black_threshold"])),
        "white_threshold": int(form_data.get("white_threshold", base["white_threshold"])),
        "sharpness_factor": float(form_data.get("sharpness_factor", base["sharpness_factor"])),
        "contrast_factor": float(form_data.get("contrast_factor", base["contrast_factor"])),
        "saturation_factor": float(form_data.get("saturation_factor", base["saturation_factor"])),
        "brightness_factor": float(form_data.get("brightness_factor", base["brightness_factor"])),
        "output_size": form_data.get("output_size", base["output_size"]),
        "shadow_offset": int(form_data.get("shadow_offset", "12")),
        "shadow_blur_radius": int(form_data.get("shadow_blur_radius", "8")),
        "shadow_alpha_start": int(form_data.get("shadow_alpha_start", "40")),
        "highlight_alpha_start": int(form_data.get("highlight_alpha_start", "30")),
        "depth_alpha_start": int(form_data.get("depth_alpha_start", "40")),
        "depth_outline_width": int(form_data.get("depth_outline_width", "5")),
        "depth_blur_radius": int(form_data.get("depth_blur_radius", "3")),
        "rim_light_alpha_start": int(form_data.get("rim_light_alpha_start", "15")),
        "rim_light_iterations": int(form_data.get("rim_light_iterations", "3")),
        "rim_light_offset_multiplier": int(form_data.get("rim_light_offset_multiplier", "2")),
        "rim_light_alpha_decrement": int(form_data.get("rim_light_alpha_decrement", "5")),
        "rim_light_outline_width": int(form_data.get("rim_light_outline_width", "2")),
        "rim_light_blur_radius": int(form_data.get("rim_light_blur_radius", "2")),
        "vignette_alpha_start": int(form_data.get("vignette_alpha_start", "20")),
        "vignette_outline_width": int(form_data.get("vignette_outline_width", "8")),
        "vignette_blur_radius": int(form_data.get("vignette_blur_radius", "6")),
        "unsharp_mask_radius": float(form_data.get("unsharp_mask_radius", "2")),
        "unsharp_mask_percent": int(form_data.get("unsharp_mask_percent", "150")),
        "unsharp_mask_threshold": float(form_data.get("unsharp_mask_threshold", "3")),
        "denoise_strength": int(form_data.get("denoise_strength", "3")),
        "smart_sharpen_amount": float(form_data.get("smart_sharpen_amount", "1.5")),
        "smart_sharpen_radius": int(form_data.get("smart_sharpen_radius", "2")),
        "smart_sharpen_threshold": int(form_data.get("smart_sharpen_threshold", "3")),
        "edge_preserve_smooth_radius": int(form_data.get("edge_preserve_smooth_radius", "1")),
        "enable_depth_effect": base["enable_depth_effect"],
        "enable_vignette_effect": base["enable_vignette_effect"],
        "enable_rim_light_effect": base["enable_rim_light_effect"],
        "output_folder": form_data.get("output_folder", base["output_folder"]),
        "temperature": float(form_data.get("temperature", base["temperature"])),
        "wet_shine_intensity": float(form_data.get("wet_shine_intensity", base["wet_shine_intensity"])),
        "water_droplets_density": int(float(form_data.get("water_droplets_density", base["water_droplets_density"]))),
        "use_ai": form_data.get("use_ai") in ("1", "true", "on", "yes"),
        "save_as": form_data.get("save_as", ""),
        "rotation": int(form_data.get("rotation", 0) or 0),
    }
    return params


def _exe_worker():
    if not getattr(sys, "frozen", False):
        return ""
    exe_dir = os.path.dirname(sys.executable)
    candidatos = (
        os.path.join(exe_dir, "worker", "Creador_PNG_Worker.exe"),
        os.path.join(exe_dir, "Creador_PNG_Worker.exe"),
    )
    for path in candidatos:
        if path and os.path.isfile(path):
            return path
    return ""


def _args_convert(params, input_filepath, output_filepath, size, rapido):
    args = [
        input_filepath,
        output_filepath,
        "--black_threshold", str(params["black_threshold"]),
        "--white_threshold", str(params["white_threshold"]),
        "--sharpness_factor", str(params["sharpness_factor"]),
        "--contrast_factor", str(params["contrast_factor"]),
        "--saturation_factor", str(params["saturation_factor"]),
        "--brightness_factor", str(params["brightness_factor"]),
        "--output_size", str(size),
        "--temperature", str(params["temperature"]),
        "--wet_shine_intensity", str(params["wet_shine_intensity"]),
        "--water_droplets_density", str(params["water_droplets_density"]),
        "--rotation", str(params["rotation"]),
    ]
    if params.get("use_ai"):
        args.append("--use_ai")
    if params.get("enable_depth_effect"):
        args.append("--enable_depth_effect")
    if params.get("enable_vignette_effect"):
        args.append("--enable_vignette_effect")
    if params.get("enable_rim_light_effect"):
        args.append("--enable_rim_light_effect")
    if rapido:
        args.append("--use_cached_cutout")
    return args


def _convertir(params, input_filepath, output_filepath, size, rapido):
    worker = _exe_worker()
    if worker:
        import subprocess
        cmd = [worker] + _args_convert(params, input_filepath, output_filepath, size, rapido)
        kwargs = {"capture_output": True, "text": True}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x08000000
        proc = subprocess.run(cmd, **kwargs)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "worker error").strip())
        return os.path.isfile(output_filepath)

    from src.carteleria.creador_png.convertir_imagen import crear_efecto_3d_realista
    return bool(crear_efecto_3d_realista(
        input_filepath,
        output_filepath,
        target_size=(size, size),
        black_threshold=params["black_threshold"],
        white_threshold=params["white_threshold"],
        sharpness_factor=params["sharpness_factor"],
        contrast_factor=params["contrast_factor"],
        saturation_factor=params["saturation_factor"],
        brightness_factor=params["brightness_factor"],
        use_ai=params["use_ai"],
        temperature=params["temperature"],
        wet_shine_intensity=params["wet_shine_intensity"],
        water_droplets_density=params["water_droplets_density"],
        rotation=params["rotation"],
        enable_depth_effect=params["enable_depth_effect"],
        enable_vignette_effect=params["enable_vignette_effect"],
        enable_rim_light_effect=params["enable_rim_light_effect"],
        use_cached_cutout=rapido,
    ))


def _upload_seguro(nombre):
    nombre = os.path.basename(nombre or "")
    if not nombre or ".." in nombre:
        return None
    path = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    if not os.path.isfile(path):
        return None
    return path


@app.route("/convert", methods=["POST"])
def convert_image():
    params = get_conversion_params(request.form)
    upload_id = (request.form.get("upload_id") or "").strip()
    input_filepath = _upload_seguro(upload_id) if upload_id else None

    if input_filepath is None:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        upload_id = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        input_filepath = os.path.join(app.config["UPLOAD_FOLDER"], upload_id)
        file.save(input_filepath)

    if params["output_folder"] == "carteleria":
        output_dir = app.config["CARTELERIA_FOLDER"]
        base_url = "/carteleria"
    else:
        output_dir = app.config["CONVERTED_FOLDER"]
        base_url = "/converted"

    output_filename = _nombre_archivo(params.get("save_as"), output_dir)
    output_filepath = os.path.join(output_dir, output_filename)
    size = int(params["output_size"] or 1024)
    rapido = request.form.get("fast") in ("1", "true", "on")

    try:
        with _convert_lock:
            ok = _convertir(params, input_filepath, output_filepath, size, rapido)
        if ok and os.path.exists(output_filepath):
            return jsonify({
                "success": True,
                "converted_image": f"{base_url}/{output_filename}",
                "download_url": f"{base_url}/{output_filename}",
                "original_url": f"/uploads/{upload_id}",
                "filename": output_filename,
                "upload_id": upload_id,
            })
        return jsonify({"error": "Conversion failed: Output file not found."}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/converted/<filename>")
def converted_file(filename):
    return send_from_directory(app.config["CONVERTED_FOLDER"], filename)


@app.route("/carteleria/<filename>")
def carteleria_file(filename):
    return send_from_directory(app.config["CARTELERIA_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)












