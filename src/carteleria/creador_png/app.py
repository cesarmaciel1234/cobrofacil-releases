from flask import Flask, request, render_template, send_from_directory, jsonify
import os
import threading
import uuid

try:
    from src.carteleria.creador_png.presets import PRESETS
except ImportError:
    from presets import PRESETS

_convert_lock = threading.Lock()

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_DIR, "..", "..", ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(_DIR, "templates"),
    static_folder=os.path.join(_DIR, "static"),
)
app.config["UPLOAD_FOLDER"] = os.path.join(_DIR, "uploads")
app.config["CONVERTED_FOLDER"] = os.path.join(_DIR, "converted")
app.config["CARTELERIA_FOLDER"] = os.path.join(_ROOT, "Catalogos", "png_productos")
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
        import subprocess
        import sys
        
        worker_exe = os.path.join(os.path.dirname(sys.executable), "worker", "Creador_PNG_Worker.exe")
        if os.path.exists(worker_exe):
            base_cmd = [worker_exe]
        else:
            base_cmd = [sys.executable, "--run-png-creator"]
            
        args = base_cmd + [
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
        if params["use_ai"]: args.append("--use_ai")
        if params["enable_depth_effect"]: args.append("--enable_depth_effect")
        if params["enable_vignette_effect"]: args.append("--enable_vignette_effect")
        if params["enable_rim_light_effect"]: args.append("--enable_rim_light_effect")
        if rapido: args.append("--use_cached_cutout")
        
        with _convert_lock:
            proc = subprocess.run(args, capture_output=True, creationflags=0x08000000)
            ok = proc.returncode == 0
        if ok and os.path.exists(output_filepath):
            return jsonify({
                "success": True,
                "converted_image": f"{base_url}/{output_filename}",
                "download_url": f"{base_url}/{output_filename}",
                "original_url": f"/uploads/{upload_id}",
                "filename": output_filename,
                "upload_id": upload_id,
            })
        err_txt = proc.stderr.decode("utf-8", "replace") if not ok else "File missing"
        return jsonify({"error": f"Conversion failed. {err_txt}"}), 500
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












