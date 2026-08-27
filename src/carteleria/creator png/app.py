from flask import Flask, request, render_template, send_from_directory, jsonify
import os
import sys
import subprocess
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['CARTELERIA_FOLDER'] = '../Catalogos/png_productos'  # Directorio específico para cartelería
app.config['SCRIPT_PATH'] = os.path.join(os.path.dirname(__file__), 'convertir_imagen.py') # Path to your conversion script

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)
os.makedirs(app.config['CARTELERIA_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', converted_image=None)

def get_conversion_params(form_data):
    return {
        'black_threshold': int(form_data.get('black_threshold', '40')),
        'white_threshold': int(form_data.get('white_threshold', '240')),
        'sharpness_factor': float(form_data.get('sharpness_factor', '1.3')),
        'contrast_factor': float(form_data.get('contrast_factor', '1.1')),
        'saturation_factor': float(form_data.get('saturation_factor', '1.05')),
        'brightness_factor': float(form_data.get('brightness_factor', '1.05')),
        'output_size': form_data.get('output_size', '2048'),
        'shadow_offset': int(form_data.get('shadow_offset', '12')),
        'shadow_blur_radius': int(form_data.get('shadow_blur_radius', '8')),
        'shadow_alpha_start': int(form_data.get('shadow_alpha_start', '40')),
        'highlight_alpha_start': int(form_data.get('highlight_alpha_start', '30')),
        'depth_alpha_start': int(form_data.get('depth_alpha_start', '40')),
        'depth_outline_width': int(form_data.get('depth_outline_width', '5')),
        'depth_blur_radius': int(form_data.get('depth_blur_radius', '3')),
        'rim_light_alpha_start': int(form_data.get('rim_light_alpha_start', '15')),
        'rim_light_iterations': int(form_data.get('rim_light_iterations', '3')),
        'rim_light_offset_multiplier': int(form_data.get('rim_light_offset_multiplier', '2')),
        'rim_light_alpha_decrement': int(form_data.get('rim_light_alpha_decrement', '5')),
        'rim_light_outline_width': int(form_data.get('rim_light_outline_width', '2')),
        'rim_light_blur_radius': int(form_data.get('rim_light_blur_radius', '2')),
        'vignette_alpha_start': int(form_data.get('vignette_alpha_start', '20')),
        'vignette_outline_width': int(form_data.get('vignette_outline_width', '8')),
        'vignette_blur_radius': int(form_data.get('vignette_blur_radius', '6')),
        'unsharp_mask_radius': float(form_data.get('unsharp_mask_radius', '2')),
        'unsharp_mask_percent': int(form_data.get('unsharp_mask_percent', '150')),
        'unsharp_mask_threshold': float(form_data.get('unsharp_mask_threshold', '3')),
        'denoise_strength': int(form_data.get('denoise_strength', '3')),
        'smart_sharpen_amount': float(form_data.get('smart_sharpen_amount', '1.5')),
        'smart_sharpen_radius': int(form_data.get('smart_sharpen_radius', '2')),
        'smart_sharpen_threshold': int(form_data.get('smart_sharpen_threshold', '3')),
        'edge_preserve_smooth_radius': int(form_data.get('edge_preserve_smooth_radius', '1')),
        'enable_depth_effect': 'enable_depth_effect' in form_data,
        'enable_vignette_effect': 'enable_vignette_effect' in form_data,
        'enable_rim_light_effect': 'enable_rim_light_effect' in form_data,
        'output_folder': form_data.get('output_folder', 'converted')
    }

@app.route('/convert', methods=['POST'])
def convert_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_filepath)
        
        params = get_conversion_params(request.form)

        output_filename = str(uuid.uuid4()) + '.png'
        
        if params['output_folder'] == 'carteleria':
            output_dir = app.config['CARTELERIA_FOLDER']
            base_url = '/carteleria'
        else:
            output_dir = app.config['CONVERTED_FOLDER']
            base_url = '/converted'
        
        output_filepath = os.path.join(output_dir, output_filename)
        
        try:
            command = [
                sys.executable, 
                app.config['SCRIPT_PATH'], 
                input_filepath, 
                output_filepath,
                '--black_threshold', str(params['black_threshold']),
                '--white_threshold', str(params['white_threshold']),
                '--sharpness_factor', str(params['sharpness_factor']),
                '--contrast_factor', str(params['contrast_factor']),
                '--saturation_factor', str(params['saturation_factor']),
                '--brightness_factor', str(params['brightness_factor']),
                '--output_size', params['output_size'],
                '--shadow_offset', str(params['shadow_offset']),
                '--shadow_blur_radius', str(params['shadow_blur_radius']),
                '--shadow_alpha_start', str(params['shadow_alpha_start']),
                '--highlight_alpha_start', str(params['highlight_alpha_start']),
                '--depth_alpha_start', str(params['depth_alpha_start']),
                '--depth_outline_width', str(params['depth_outline_width']),
                '--depth_blur_radius', str(params['depth_blur_radius']),
                '--rim_light_alpha_start', str(params['rim_light_alpha_start']),
                '--rim_light_iterations', str(params['rim_light_iterations']),
                '--rim_light_offset_multiplier', str(params['rim_light_offset_multiplier']),
                '--rim_light_alpha_decrement', str(params['rim_light_alpha_decrement']),
                '--rim_light_outline_width', str(params['rim_light_outline_width']),
                '--rim_light_blur_radius', str(params['rim_light_blur_radius']),
                '--vignette_alpha_start', str(params['vignette_alpha_start']),
                '--vignette_outline_width', str(params['vignette_outline_width']),
                '--vignette_blur_radius', str(params['vignette_blur_radius']),
                '--unsharp_mask_radius', str(params['unsharp_mask_radius']),
                '--unsharp_mask_percent', str(params['unsharp_mask_percent']),
                '--unsharp_mask_threshold', str(params['unsharp_mask_threshold']),
                '--denoise_strength', str(params['denoise_strength']),
                '--smart_sharpen_amount', str(params['smart_sharpen_amount']),
                '--smart_sharpen_radius', str(params['smart_sharpen_radius']),
                '--smart_sharpen_threshold', str(params['smart_sharpen_threshold']),
                '--edge_preserve_smooth_radius', str(params['edge_preserve_smooth_radius']),
            ]
            if params['enable_depth_effect']: command.append('--enable_depth')
            if params['enable_vignette_effect']: command.append('--enable_vignette')
            if params['enable_rim_light_effect']: command.append('--enable_rim_light')

            print(f"DEBUG: SCRIPT_PATH: {app.config['SCRIPT_PATH']}")
            print(f"DEBUG: Script exists: {os.path.exists(app.config['SCRIPT_PATH'])}")
            print(f"DEBUG: Command: {command}")
            
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("Conversion script stdout:", result.stdout)
            print("Conversion script stderr:", result.stderr)

            if os.path.exists(output_filepath):
                return jsonify({
                    'success': True,
                    'converted_image': f'{base_url}/{output_filename}',
                    'download_url': f'{base_url}/{output_filename}',
                    'original_url': f'/uploads/{unique_filename}'
                })
            else:
                return jsonify({'error': f'Conversion failed: Output file not found. {result.stderr}'}), 500
        except subprocess.CalledProcessError as e:
            return jsonify({'error': f'Conversion script error: {e.stderr}'}), 500
        except Exception as e:
            return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/batch_convert', methods=['POST'])
def batch_convert():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part'}), 400
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400
    
    params = get_conversion_params(request.form)

    if params['output_folder'] == 'carteleria':
        output_dir = app.config['CARTELERIA_FOLDER']
        base_url = '/carteleria'
    else:
        output_dir = app.config['CONVERTED_FOLDER']
        base_url = '/converted'
    
    results = []
    
    for file in files:
        try:
            unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(input_filepath)
            
            output_filename = str(uuid.uuid4()) + '.png'
            output_filepath = os.path.join(output_dir, output_filename)
            
            command = [
                sys.executable, 
                app.config['SCRIPT_PATH'], 
                input_filepath, 
                output_filepath,
                '--black_threshold', str(params['black_threshold']),
                '--white_threshold', str(params['white_threshold']),
                '--sharpness_factor', str(params['sharpness_factor']),
                '--contrast_factor', str(params['contrast_factor']),
                '--saturation_factor', str(params['saturation_factor']),
                '--brightness_factor', str(params['brightness_factor']),
                '--output_size', params['output_size'],
                '--shadow_offset', str(params['shadow_offset']),
                '--shadow_blur_radius', str(params['shadow_blur_radius']),
                '--shadow_alpha_start', str(params['shadow_alpha_start']),
                '--highlight_alpha_start', str(params['highlight_alpha_start']),
                '--depth_alpha_start', str(params['depth_alpha_start']),
                '--depth_outline_width', str(params['depth_outline_width']),
                '--depth_blur_radius', str(params['depth_blur_radius']),
                '--rim_light_alpha_start', str(params['rim_light_alpha_start']),
                '--rim_light_iterations', str(params['rim_light_iterations']),
                '--rim_light_offset_multiplier', str(params['rim_light_offset_multiplier']),
                '--rim_light_alpha_decrement', str(params['rim_light_alpha_decrement']),
                '--rim_light_outline_width', str(params['rim_light_outline_width']),
                '--rim_light_blur_radius', str(params['rim_light_blur_radius']),
                '--vignette_alpha_start', str(params['vignette_alpha_start']),
                '--vignette_outline_width', str(params['vignette_outline_width']),
                '--vignette_blur_radius', str(params['vignette_blur_radius']),
                '--unsharp_mask_radius', str(params['unsharp_mask_radius']),
                '--unsharp_mask_percent', str(params['unsharp_mask_percent']),
                '--unsharp_mask_threshold', str(params['unsharp_mask_threshold']),
                '--denoise_strength', str(params['denoise_strength']),
                '--smart_sharpen_amount', str(params['smart_sharpen_amount']),
                '--smart_sharpen_radius', str(params['smart_sharpen_radius']),
                '--smart_sharpen_threshold', str(params['smart_sharpen_threshold']),
                '--edge_preserve_smooth_radius', str(params['edge_preserve_smooth_radius']),
            ]
            if params['enable_depth_effect']: command.append('--enable_depth')
            if params['enable_vignette_effect']: command.append('--enable_vignette')
            if params['enable_rim_light_effect']: command.append('--enable_rim_light')

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            
            if os.path.exists(output_filepath):
                results.append({
                    'success': True,
                    'original_name': file.filename,
                    'converted_image': f'{base_url}/{output_filename}',
                    'download_url': f'{base_url}/{output_filename}'
                })
            else:
                results.append({
                    'success': False,
                    'original_name': file.filename,
                    'error': 'Conversion failed'
                })
        except Exception as e:
            results.append({
                'success': False,
                'original_name': file.filename,
                'error': str(e)
            })
    
    return jsonify({'results': results})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/converted/<filename>')
def converted_file(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename)

@app.route('/carteleria/<filename>')
def carteleria_file(filename):
    return send_from_directory(app.config['CARTELERIA_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
