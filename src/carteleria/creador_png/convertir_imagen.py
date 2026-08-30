# -*- coding: utf-8 -*-
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageOps, ImageChops
import os
import sys
import math
import argparse

# Constantes globales para remover_fondo (se pueden sobrescribir)
BLACK_THRESHOLD = 40
WHITE_THRESHOLD = 240

# Constantes para crear_efecto_3d_realista
SHARPNESS_FACTOR = 1.3
CONTRAST_FACTOR = 1.1
COLOR_FACTOR = 1.05 # Se convertirá en saturation_factor

SHADOW_OFFSET = 12
SHADOW_COLOR_ALPHA = (20, 20, 20, 40) # R, G, B, Alpha
SHADOW_BLUR_RADIUS = 8

HIGHLIGHT_GRADIENT_STEPS = 50
HIGHLIGHT_ALPHA_START = 30
HIGHLIGHT_RADIUS_FACTOR = 0.4
HIGHLIGHT_BLUR_RADIUS = 4

DEPTH_GRADIENT_STEP = 2
DEPTH_ALPHA_START = 40 # Aumentado
DEPTH_OUTLINE_WIDTH = 5 # Aumentado
DEPTH_BLUR_RADIUS = 3

RIM_LIGHT_ITERATIONS = 3
RIM_LIGHT_OFFSET_MULTIPLIER = 2
RIM_LIGHT_ALPHA_START = 15
RIM_LIGHT_ALPHA_DECREMENT = 5
RIM_LIGHT_OUTLINE_WIDTH = 2
RIM_LIGHT_BLUR_RADIUS = 2

VIGNETTE_GRADIENT_STEP = 4
VIGNETTE_ALPHA_START = 20 # Aumentado
VIGNETTE_OUTLINE_WIDTH = 8 # Aumentado
VIGNETTE_BLUR_RADIUS = 6

UNSHARP_MASK_RADIUS = 2
UNSHARP_MASK_PERCENT = 150
UNSHARP_MASK_THRESHOLD = 3

def _refinar_mascara(img):
    """Saca mesadas/bandejas grises que la IA deja pegadas y recorta al producto."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    try:
        import numpy as np
        data = np.array(img)
        rgb = data[:, :, :3].astype(np.float32)
        # Limpieza de alpha (bordes semi-transparentes muy suaves que dejan halo)
        data[data[:, :, 3] < 24, 3] = 0
        img = Image.fromarray(data, 'RGBA')
    except ImportError:
        pass
    bbox = img.getbbox()
    if bbox:
        pad = 24
        left, top, right, bottom = bbox
        img = img.crop((
            max(0, left - pad),
            max(0, top - pad),
            min(img.width, right + pad),
            min(img.height, bottom + pad),
        ))
    return img


_REMBG_SESSION = None
_MAX_LADO_TRABAJO = 1280


def _limitar_lado(img, max_lado=_MAX_LADO_TRABAJO):
    w, h = img.size
    lado = max(w, h)
    if lado <= max_lado:
        return img
    ratio = max_lado / lado
    return img.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.Resampling.BILINEAR)


def _sesion_rembg():
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        from rembg import new_session
        _REMBG_SESSION = new_session('u2net')
    return _REMBG_SESSION


def remover_fondo(img, black_threshold=BLACK_THRESHOLD, white_threshold=WHITE_THRESHOLD, use_ai=False):
    """
    Remueve el fondo. Si use_ai es True, usa rembg. Si no, usa el método básico por colores.
    """
    img = _limitar_lado(img)
    if use_ai:
        try:
            from rembg import remove
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            result = remove(img, session=_sesion_rembg())
            return _refinar_mascara(result)
        except ImportError:
            import sys
            print("ADVERTENCIA: rembg no está instalado. Fallback a método básico por colores.", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Error al usar rembg: {e}. Fallback a método básico por colores.")
            import traceback
            traceback.print_exc()

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    try:
        import numpy as np
        data = np.array(img)
        mask_black = (data[:, :, 0] < black_threshold) & (data[:, :, 1] < black_threshold) & (data[:, :, 2] < black_threshold)
        mask_white = (data[:, :, 0] > white_threshold) & (data[:, :, 1] > white_threshold) & (data[:, :, 2] > white_threshold)
        data[mask_black | mask_white, 3] = 0
        img = Image.fromarray(data, 'RGBA')
    except ImportError:
        pixels = img.getdata()
        new_pixels = []
        for p in pixels:
            r, g, b, a = p
            if (r < black_threshold and g < black_threshold and b < black_threshold) or \
               (r > white_threshold and g > white_threshold and b > white_threshold):
                new_pixels.append((0, 0, 0, 0))
            else:
                new_pixels.append(p)
        img.putdata(new_pixels)

    return _refinar_mascara(img)

def smart_sharpen(img, amount=1.5, radius=2, threshold=3):
    """
    Aplica un enfoque inteligente a la imagen, realzando los bordes sin amplificar el ruido.
    Utiliza una aproximación de máscara de desenfoque.
    """
    # Convertir a RGB si es necesario para asegurar el procesamiento correcto de los colores
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Aplicar desenfoque Gaussiano para obtener una versión suavizada de la imagen
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    
    # Calcular la diferencia entre la imagen original y la desenfocada para encontrar los bordes
    diff = ImageChops.subtract(img, blurred)
    
    # Función para aplicar un umbral a la diferencia y controlar la amplificación del ruido
    def threshold_func(x):
        if x <= threshold:
            return 0  # No enfocar si la diferencia es pequeña (posible ruido)
        return int((x - threshold) * amount) # Amplificar la diferencia (bordes) por el factor 'amount'
    
    # Aplicar la función de umbral a cada píxel de la diferencia
    diff = diff.point(threshold_func)
    
    # Sumar los bordes enfocados de vuelta a la imagen original
    result = ImageChops.add(img, diff)
    
    return result

def enhance_colors(img, saturation=1.2, brightness=1.05, temperature=0):
    """
    Mejora los colores de la imagen ajustando la saturación, brillo y temperatura.
    temperature: negativo = frío (azulado), positivo = cálido (amarillento/rojizo)
    """
    if img.mode != 'RGB':
        img = img.convert('RGB')

    if temperature != 0:
        try:
            import numpy as np
            data = np.array(img, dtype=np.float32)
            if temperature > 0:
                data[:, :, 0] = np.clip(data[:, :, 0] * (1 + temperature * 0.1), 0, 255)
                data[:, :, 2] = np.clip(data[:, :, 2] * (1 - temperature * 0.05), 0, 255)
            else:
                data[:, :, 0] = np.clip(data[:, :, 0] * (1 + temperature * 0.05), 0, 255)
                data[:, :, 2] = np.clip(data[:, :, 2] * (1 - temperature * 0.1), 0, 255)
            img = Image.fromarray(data.astype(np.uint8), 'RGB')
        except ImportError:
            r, g, b = img.split()
            if temperature > 0:
                r = r.point(lambda x: min(255, int(x * (1 + temperature * 0.1))))
                b = b.point(lambda x: int(x * (1 - temperature * 0.05)))
            else:
                r = r.point(lambda x: int(x * (1 + temperature * 0.05)))
                b = b.point(lambda x: min(255, int(x * (1 - temperature * 0.1))))
            img = Image.merge('RGB', (r, g, b))

    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    return img

def denoise_image(img, strength=5):
    """
    Reduce el ruido de la imagen utilizando un filtro de mediana y mezcla con el original para preservar detalles.
    """
    # Aplicar filtro de mediana para reducir el ruido
    denoised = img.filter(ImageFilter.MedianFilter(size=strength))
    
    # Mezclar la imagen denoised con la original para preservar la nitidez de los detalles
    result = Image.blend(img, denoised, 0.3)
    
    return result

def edge_preserve_smooth(img, radius=2):
    """
    Suavizado que intenta preservar los bordes utilizando una aproximación de filtro bilateral.
    """
    # Aplicar desenfoque Gaussiano para suavizar la imagen general
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    # Encontrar los bordes en la imagen original
    edges = img.filter(ImageFilter.FIND_EDGES)
    
    # Crear una máscara de bordes: blanco donde hay bordes fuertes, negro en otro lugar
    # Convertir a escala de grises y luego aplicar un umbral para binarizar los bordes
    edge_mask = edges.convert('L').point(lambda x: 255 if x > 50 else 0)
    
    # Mezclar la imagen original con la desenfocada usando la máscara de bordes.
    # Donde hay bordes (blanco en edge_mask), se mantiene la imagen original.
    # Donde no hay bordes (negro en edge_mask), se usa la imagen desenfocada.
    result = Image.composite(img, blurred, edge_mask)
    
    return result

def _intensidad_rocio(density):
    """Normaliza el control de rocío a 0–1 (0–1 directo, o 0–100 del slider)."""
    try:
        value = float(density)
    except (TypeError, ValueError):
        return 0.0
    if value <= 0:
        return 0.0
    if value <= 1:
        return value
    return min(1.0, value / 100.0)


def add_wet_shine(img, intensity=0.3):
    """Brillo húmedo: el producto se ve frío, brillante, como con condensación."""
    intensity = _intensidad_rocio(intensity) if intensity > 1 else max(0.0, min(1.0, float(intensity)))
    if intensity <= 0:
        return img
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    w, h = img.size
    try:
        import numpy as np
        data = np.array(img).astype(np.float32)
        alpha = data[:, :, 3]
        mask = alpha > 140
        lum = (0.299 * data[:, :, 0] + 0.587 * data[:, :, 1] + 0.114 * data[:, :, 2]) / 255.0
        boost = np.clip((lum - 0.38) * 2.2, 0, 1) * intensity
        data[:, :, 0] = np.where(mask, np.clip(data[:, :, 0] + boost * 35, 0, 255), data[:, :, 0])
        data[:, :, 1] = np.where(mask, np.clip(data[:, :, 1] + boost * 55, 0, 255), data[:, :, 1])
        data[:, :, 2] = np.where(mask, np.clip(data[:, :, 2] + boost * 80, 0, 255), data[:, :, 2])
        yy, xx = np.ogrid[0:h, 0:w]
        spec = np.clip(1.0 - (((xx / max(w, 1) - 0.28) ** 2) + ((yy / max(h, 1) - 0.20) ** 2)) * 5.5, 0, 1)
        spec = spec * intensity * 0.32 * (alpha / 255.0)
        data[:, :, 0] = np.clip(data[:, :, 0] + spec * 28, 0, 255)
        data[:, :, 1] = np.clip(data[:, :, 1] + spec * 42, 0, 255)
        data[:, :, 2] = np.clip(data[:, :, 2] + spec * 62, 0, 255)
        return Image.fromarray(data.astype(np.uint8), 'RGBA')
    except ImportError:
        overlay = Image.new('RGBA', (w, h), (210, 230, 255, int(50 * intensity)))
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(w, h) // 8 or 1))
        alpha = img.split()[3]
        overlay.putalpha(ImageChops.multiply(overlay.split()[3], alpha))
        return Image.alpha_composite(img, overlay)


def add_water_droplets(img, density=50, size_range=(2, 5)):
    """
    Rocío / sudor: gotas de agua fría pegadas al producto (lata helada, fruta con rocío).
    density: 0–100.
    """
    intensity = _intensidad_rocio(density)
    if intensity <= 0:
        return img
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    import random

    w, h = img.size
    alpha = img.split()[3]
    scale = max(w, h) / 1024.0
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    try:
        import numpy as np
        a = np.array(alpha)
        ys, xs = np.where(a > 140)
        if len(xs) < 40:
            return img

        def pick():
            i = random.randrange(len(xs))
            return int(xs[i]), int(ys[i])
    except ImportError:
        puntos = []
        step = max(2, int(4 / max(scale, 0.5)))
        for y in range(0, h, step):
            for x in range(0, w, step):
                if alpha.getpixel((x, y)) > 140:
                    puntos.append((x, y))
        if len(puntos) < 40:
            return img

        def pick():
            return puntos[random.randrange(len(puntos))]

    n_micro = int((280 + 420 * intensity) * (scale ** 2))
    n_drops = int((12 + 36 * intensity) * (scale ** 2))
    n_drips = int((1 + 4 * intensity) * scale)

    for _ in range(n_micro):
        x, y = pick()
        r = max(1, int(random.uniform(0.5, 1.5) * scale))
        fill_a = random.randint(15, 45)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(230, 245, 255, fill_a))

    for _ in range(n_drops):
        x, y = pick()
        rw = max(2, int(random.uniform(2, 6) * scale))
        rh = max(rw, int(rw * random.uniform(1.0, 1.3)))
        draw.ellipse([x - rw + 1, y - rh + 1, x + rw + 1, y + rh + 1], fill=(20, 40, 60, 15))
        draw.ellipse([x - rw, y - rh, x + rw, y + rh], fill=(200, 230, 255, 45))
        hr = max(1.5, rw / 2.5)
        hx, hy = x - rw / 3.0, y - rh / 2.5
        draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(255, 255, 255, 130))

    for _ in range(n_drips):
        x, y = pick()
        length = max(10, int(random.randint(10, 25) * scale))
        wd = max(1, int(random.randint(1, 3) * scale))
        draw.ellipse([x - wd, y, x + wd, y + length], fill=(200, 230, 255, 30))
        bulb = max(wd + 1, int(wd * 1.5))
        draw.ellipse(
            [x - bulb, y + length - bulb, x + bulb, y + length + bulb],
            fill=(210, 235, 255, 60),
        )
        draw.ellipse([x - 1, y + 1, x + 1, y + max(3, int(4 * scale))], fill=(255, 255, 255, 140))

    layer = layer.filter(ImageFilter.GaussianBlur(radius=1))
    masked = ImageChops.multiply(layer.split()[3], alpha)
    layer.putalpha(masked)
    return Image.alpha_composite(img, layer)

def crear_efecto_3d_realista(input_path, output_path, target_size=(2048, 2048), dpi=150,
                             sharpness_factor=SHARPNESS_FACTOR, contrast_factor=CONTRAST_FACTOR,
                             saturation_factor=COLOR_FACTOR, brightness_factor=1.05, 
                             shadow_offset=SHADOW_OFFSET, shadow_blur_radius=SHADOW_BLUR_RADIUS, 
                             highlight_alpha_start=HIGHLIGHT_ALPHA_START, 
                             depth_alpha_start=DEPTH_ALPHA_START, depth_outline_width=DEPTH_OUTLINE_WIDTH, depth_blur_radius=DEPTH_BLUR_RADIUS,
                             rim_light_alpha_start=RIM_LIGHT_ALPHA_START, rim_light_iterations=RIM_LIGHT_ITERATIONS, rim_light_offset_multiplier=RIM_LIGHT_OFFSET_MULTIPLIER, rim_light_alpha_decrement=RIM_LIGHT_ALPHA_DECREMENT, rim_light_outline_width=RIM_LIGHT_OUTLINE_WIDTH, rim_light_blur_radius=RIM_LIGHT_BLUR_RADIUS,
                             vignette_alpha_start=VIGNETTE_ALPHA_START, vignette_outline_width=VIGNETTE_OUTLINE_WIDTH, vignette_blur_radius=VIGNETTE_BLUR_RADIUS,
                             unsharp_mask_radius=UNSHARP_MASK_RADIUS, unsharp_mask_percent=UNSHARP_MASK_PERCENT, unsharp_mask_threshold=UNSHARP_MASK_THRESHOLD,
                             shadow_alpha_start=SHADOW_COLOR_ALPHA[3], black_threshold=BLACK_THRESHOLD, 
                             white_threshold=WHITE_THRESHOLD,
                             denoise_strength=3, smart_sharpen_amount=1.5, smart_sharpen_radius=2, smart_sharpen_threshold=3,
                             edge_preserve_smooth_radius=1,
                             enable_depth_effect=False, enable_vignette_effect=False, enable_rim_light_effect=False, use_ai=False,
                             temperature=0, wet_shine_intensity=0, water_droplets_density=0, rotation=0, use_cached_cutout=False):
    """
    Convierte imagen a PNG con fondo transparente y efectos 3D personalizables.
    """
    try:
        print(f"INFO: Iniciando procesamiento de imagen: {input_path}")
        cutout_path = input_path + '.cutout.png'
        if use_cached_cutout and __import__('os').path.exists(cutout_path):
            img = Image.open(cutout_path).convert('RGBA')
            import time; time.sleep(0.02); print('INFO: Usando mascara de IA en cache.')
        else:
            img = Image.open(input_path)
            if rotation:
                img = img.rotate(-rotation, expand=True)
            import time; time.sleep(0.02); print('INFO: Imagen abierta. Tamaño original:', img.size)
            img = remover_fondo(img, black_threshold=black_threshold, white_threshold=white_threshold, use_ai=use_ai)
            if use_ai:
                img.save(cutout_path)
        import time; time.sleep(0.02); print('INFO: Fondo removido/cargado.')
        
        # Redimensionar a tamaño objetivo con alta calidad (si se especifica)
        if target_size:
            original_width, original_height = img.size
            target_width, target_height = target_size
            
            # Calcular ratio para mantener aspect ratio
            ratio = min(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # Redimensionar manteniendo aspect ratio
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crear canvas transparente del tamaño objetivo
            canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
            
            # Centrar la imagen en el canvas
            offset_x = (target_width - new_width) // 2
            offset_y = (target_height - new_height) // 2
            
            # Pegar la imagen en el canvas con el canal alpha como máscara
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Usar el canal alpha de la imagen como máscara
            canvas.paste(img, (offset_x, offset_y), img)
            
            img = canvas
        
        import time; time.sleep(0.02); print("INFO: Aplicando color y nitidez...")
        has_alpha = img.mode == 'RGBA'
        alpha_channel = None
        if has_alpha:
            alpha_channel = img.split()[3]
            img = img.convert('RGB')

        img = enhance_colors(img, saturation=saturation_factor, brightness=brightness_factor, temperature=temperature)
        img = ImageEnhance.Contrast(img).enhance(contrast_factor)
        if sharpness_factor and sharpness_factor != 1:
            img = ImageEnhance.Sharpness(img).enhance(sharpness_factor)
        
        # Restaurar canal alpha para aplicar rocío solo sobre el producto
        if has_alpha and alpha_channel is not None:
            img = img.convert('RGBA')
            img.putalpha(alpha_channel)
        elif img.mode != 'RGBA':
            img = img.convert('RGBA')

        if wet_shine_intensity > 0:
            import time; time.sleep(0.02); print("INFO: Aplicando brillo húmedo...")
            img = add_wet_shine(img, intensity=wet_shine_intensity)

        if water_droplets_density > 0:
            import time; time.sleep(0.02); print("INFO: Agregando rocío / sudor de agua...")
            img = add_water_droplets(img, density=water_droplets_density)
        
        # Crear imagen base para efectos 3D
        width, height = img.size
        result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Asegurarse de que la imagen tenga canal alpha para alpha_composite
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        alpha = img.split()[3]
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        shadow.paste((20, 20, 20, shadow_alpha_start), (shadow_offset, shadow_offset), alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur_radius))
        import time; time.sleep(0.05)

        highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(highlight)
        radius = int(min(width, height) * HIGHLIGHT_RADIUS_FACTOR)
        draw.ellipse([-radius // 3, -radius // 3, radius * 2, radius * 2], fill=(255, 255, 255, highlight_alpha_start))
        highlight = highlight.filter(ImageFilter.GaussianBlur(radius=HIGHLIGHT_BLUR_RADIUS + 8))
        import time; time.sleep(0.05)

        result = Image.alpha_composite(result, shadow)
        result = Image.alpha_composite(result, img)
        result = Image.alpha_composite(result, highlight)

        if enable_vignette_effect:
            try:
                import numpy as np
                yy, xx = np.ogrid[:height, :width]
                dist = np.sqrt((xx - width / 2.0) ** 2 + (yy - height / 2.0) ** 2)
                norm = dist / (dist.max() or 1)
                a = np.clip(norm ** 2 * vignette_alpha_start, 0, 255).astype(np.uint8)
                layer = np.zeros((height, width, 4), dtype=np.uint8)
                layer[:, :, 3] = a
                result = Image.alpha_composite(result, Image.fromarray(layer, 'RGBA'))
            except ImportError:
                pass
        
        # Guardar resultado
        result.save(output_path, 'PNG', dpi=(dpi, dpi))
        print(f"INFO: Imagen procesada guardada en: {output_path}")
        return True
    except Exception as e:
        print(f"ERROR: Error procesando imagen: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Convierte imágenes a PNG con fondo transparente y efectos 3D.')
    parser.add_argument('input', help='Ruta de la imagen de entrada')
    parser.add_argument('output', help='Ruta de la imagen de salida')
    parser.add_argument('--black_threshold', type=int, default=BLACK_THRESHOLD, help='Umbral para negro (0-100)')
    parser.add_argument('--white_threshold', type=int, default=WHITE_THRESHOLD, help='Umbral para blanco (200-255)')
    parser.add_argument('--sharpness_factor', type=float, default=SHARPNESS_FACTOR, help='Factor de nitidez')
    parser.add_argument('--contrast_factor', type=float, default=CONTRAST_FACTOR, help='Factor de contraste')
    parser.add_argument('--saturation_factor', type=float, default=COLOR_FACTOR, help='Factor de saturación')
    parser.add_argument('--brightness_factor', type=float, default=1.05, help='Factor de brillo')
    parser.add_argument('--output_size', type=int, default=1024, help='Tamaño de salida (cuadrado)')
    parser.add_argument('--use_ai', action='store_true', help='Usar rembg para remoción de fondo con IA')
    parser.add_argument('--temperature', type=float, default=0, help='Temperatura de color (-5 a 5)')
    parser.add_argument('--wet_shine_intensity', type=float, default=0, help='Brillo húmedo (0-1)')
    parser.add_argument('--water_droplets_density', type=int, default=0, help='Rocío / sudor de agua (0-100)')
    parser.add_argument('--rotation', type=int, default=0, help='Rotacion en grados')
    parser.add_argument('--enable_depth_effect', action='store_true')
    parser.add_argument('--enable_vignette_effect', action='store_true')
    parser.add_argument('--enable_rim_light_effect', action='store_true')
    parser.add_argument('--use_cached_cutout', action='store_true')
    args = parser.parse_args()
    
    target_size = (args.output_size, args.output_size)
    
    success = crear_efecto_3d_realista(
        args.input, 
        args.output, 
        target_size=target_size,
        black_threshold=args.black_threshold,
        white_threshold=args.white_threshold,
        sharpness_factor=args.sharpness_factor,
        contrast_factor=args.contrast_factor,
        saturation_factor=args.saturation_factor,
        brightness_factor=args.brightness_factor,
        use_ai=args.use_ai,
        temperature=args.temperature,
        wet_shine_intensity=args.wet_shine_intensity,
        water_droplets_density=args.water_droplets_density,
        rotation=args.rotation,
    )
    
    if success:
        print("SUCCESS: Imagen procesada exitosamente.")
        sys.exit(0)
    else:
        print("ERROR: Falló el procesamiento de la imagen.")
        sys.exit(1)

if __name__ == '__main__':
    main()













