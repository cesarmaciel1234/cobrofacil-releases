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

def remover_fondo(img, black_threshold=BLACK_THRESHOLD, white_threshold=WHITE_THRESHOLD, use_ai=False):
    """
    Remueve el fondo. Si use_ai es True, usa rembg. Si no, usa el método básico por colores.
    """
    if use_ai:
        try:
            from rembg import remove, new_session
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Usamos u2netp (versión ultraligera de 4MB) para que sea rapidísimo y no tarde descargando
            session = new_session('u2netp')
            result = remove(img, session=session)
            return result
        except ImportError:
            import sys
            print("ADVERTENCIA: rembg no está instalado. Fallback a método básico por colores.", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Error al usar rembg: {e}. Fallback a método básico por colores.")
            import traceback
            traceback.print_exc()

    # MÉTODO BÁSICO (Threshold)
    # Convertir a RGBA si no lo está para asegurar el canal alfa
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
        
        # Intentar usar numpy para un procesamiento más rápido si está disponible
        try:
            import numpy as np
            data = np.array(img)
            
            # Crear máscara para píxeles oscuros (negro) basándose en los umbrales
            mask_black = (data[:, :, 0] < black_threshold) & (data[:, :, 1] < black_threshold) & (data[:, :, 2] < black_threshold)
            
            # Crear máscara para píxeles claros (blanco) basándose en los umbrales
            mask_white = (data[:, :, 0] > white_threshold) & (data[:, :, 1] > white_threshold) & (data[:, :, 2] > white_threshold)
            
            # Combinar ambas máscaras para identificar los píxeles a hacer transparentes
            mask = mask_black | mask_white
            
            # Establecer el canal alfa a 0 (transparente) para los píxeles en la máscara
            data[mask, 3] = 0  # Alpha = 0 para transparente
            
            # Convertir la matriz numpy de vuelta a un objeto PIL Image
            img = Image.fromarray(data, 'RGBA')
            
        except ImportError:
            # Fallback si numpy no está instalado, usando iteración de píxeles (más lento)
            pixels = img.getdata()
            new_pixels = []
            
            for p in pixels:
                r, g, b, a = p
                # Si el píxel es negro/muy oscuro o blanco/muy claro, hacerlo transparente
                if (r < black_threshold and g < black_threshold and b < black_threshold) or \
                   (r > white_threshold and g > white_threshold and b > white_threshold):
                    new_pixels.append((0, 0, 0, 0))  # Transparente
                else:
                    new_pixels.append(p)
            
            img.putdata(new_pixels)
        
        return img

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

def enhance_colors(img, saturation=1.2, brightness=1.05):
    """
    Mejora los colores de la imagen ajustando la saturación y el brillo.
    """
    # Convertir a RGB si es necesario
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Ajustar Saturación
    enhancer_s = ImageEnhance.Color(img)
    img = enhancer_s.enhance(saturation)
    
    # Ajustar Brillo
    enhancer_b = ImageEnhance.Brightness(img)
    img = enhancer_b.enhance(brightness)
    
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
                             enable_depth_effect=True, enable_vignette_effect=True, enable_rim_light_effect=True, use_ai=False):
    """
    Convierte imagen a PNG con fondo transparente y efectos 3D personalizables.
    """
    try:
        print(f"INFO: Iniciando procesamiento de imagen: {input_path}")
        # Abrir imagen original
        img = Image.open(input_path)
        print("INFO: Imagen abierta. Tamaño original:", img.size)
        
        # Remover fondo negro y blanco con umbrales dinámicos
        img = remover_fondo(img, black_threshold=black_threshold, white_threshold=white_threshold, use_ai=use_ai)
        print("INFO: Fondo removido.")
        
        # Redimensionar a tamaño objetivo con alta calidad (si se especifica)
        if target_size:
            print(f"INFO: Redimensionando imagen a {target_size[0]}x{target_size[1]}px.")
            # Mantener aspect ratio para evitar distorsión
            original_width, original_height = img.size
            target_width, target_height = target_size
            
            # Calcular ratios
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            ratio = min(width_ratio, height_ratio)
            
            # Calcular nuevas dimensiones manteniendo aspect ratio
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # Redimensionar con alta calidad manteniendo aspect ratio
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Crear canvas del tamaño objetivo con fondo transparente
            canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
            
            # Centrar la imagen en el canvas
            offset_x = (target_width - new_width) // 2
            offset_y = (target_height - new_height) // 2
            
            # Asegurar que la imagen tenga canal alpha para el paste
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Usar el canal alpha de la imagen como máscara
            canvas.paste(img, (offset_x, offset_y), img)
            
            img = canvas
        
        # Mejorar calidad de imagen base con técnicas avanzadas
        print("INFO: Aplicando mejoras de calidad de imagen (denoise, sharpen, smooth, color)...")
        # Guardar el canal alpha para restaurarlo después
        has_alpha = img.mode == 'RGBA'
        alpha_channel = None
        if has_alpha:
            alpha_channel = img.split()[3]
            img = img.convert('RGB') # Convertir temporalmente a RGB para procesamiento de color
        
        # 1. Denoising para eliminar ruido
        img = denoise_image(img, strength=denoise_strength)
        
        # 2. Smart sharpening en lugar de sharpening básico
        img = smart_sharpen(img, amount=smart_sharpen_amount, radius=smart_sharpen_radius, threshold=smart_sharpen_threshold)
        
        # 3. Edge-preserving smoothing
        img = edge_preserve_smooth(img, radius=edge_preserve_smooth_radius)
        
        # 4. Mejoras de color avanzadas
        img = enhance_colors(img, saturation=saturation_factor, brightness=brightness_factor)
        
        # 5. Contraste básico
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)
        
        # Restaurar canal alpha si existía
        if has_alpha and alpha_channel is not None:
            img = img.convert('RGBA')
            img.putalpha(alpha_channel)
        
        # Crear imagen base para efectos 3D
        width, height = img.size
        result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Asegurarse de que la imagen tenga canal alpha para alpha_composite
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print("INFO: Aplicando efectos 3D (sombra, iluminación, profundidad, rim light, viñeta)...")
        # 1. Crear sombra realista con blur
        shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Extraer canal alpha de la imagen principal para usarlo como máscara de sombra
        alpha = img.split()[3]
        shadow_mask = alpha.copy()
        
        # Crear una capa de sombra desplazada con color y opacidad definidos
        shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        # El color de la sombra se define con RGB y un alpha dinámico
        shadow_color_dynamic = (SHADOW_COLOR_ALPHA[0], SHADOW_COLOR_ALPHA[1], SHADOW_COLOR_ALPHA[2], shadow_alpha_start)
        shadow_layer.paste(shadow_color_dynamic, (shadow_offset, shadow_offset), shadow_mask)
        
        # Aplicar desenfoque a la sombra para un efecto más realista
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur_radius))
        
        # 2. Crear efecto de iluminación superior (light source de arriba-izquierda)
        highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        highlight_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0)) # Crear una capa transparente para el highlight
        
        # Aplicar brillo gradual en el área superior izquierda para simular una fuente de luz
        draw = ImageDraw.Draw(highlight_layer)
        gradient_steps = HIGHLIGHT_GRADIENT_STEPS
        for i in range(gradient_steps):
            # Calcular la opacidad y el radio del elipse para el gradiente
            alpha = int(highlight_alpha_start * (1 - i / gradient_steps))
            # Ajustar el radio para que el highlight se concentre en el centro-superior
            radius_x = int(width * HIGHLIGHT_RADIUS_FACTOR * (1 - i / gradient_steps))
            radius_y = int(height * HIGHLIGHT_RADIUS_FACTOR * (1 - i / gradient_steps))
            
            # Dibujar un elipse transparente con un gradiente de opacidad
            draw.ellipse([width//2 - radius_x, height//2 - radius_y, 
                          width//2 + radius_x, height//2 + radius_y], 
                         fill=(255, 255, 255, alpha))
        
        highlight = highlight_layer.filter(ImageFilter.GaussianBlur(radius=HIGHLIGHT_BLUR_RADIUS)) # Desenfoque para suavizar el highlight

        # 3. Crear efecto de profundidad con gradientes circulares
        if enable_depth_effect:
            depth = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(depth)
            
            # Gradiente radial para simular un efecto de profundidad o bulto
            center_x, center_y = width // 2, height // 2
            max_radius = min(width, height) // 2
            
            for i in range(max_radius, 0, -DEPTH_GRADIENT_STEP):
                # Calcular la opacidad y dibujar elipse para el efecto de contorno de profundidad
                alpha = int(depth_alpha_start * (1 - i / max_radius))
                draw.ellipse([center_x - i, center_y - i, 
                             center_x + i, center_y + i], 
                            outline=(0, 0, 0, alpha), width=depth_outline_width)
            
            depth = depth.filter(ImageFilter.GaussianBlur(radius=depth_blur_radius))

        # 4. Aplicar efecto de borde brillante (rim light)
        if enable_rim_light_effect:
            rim_light_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            
            # Extraer los bordes de la imagen para aplicar el rim light sobre ellos
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges = edges.filter(ImageFilter.GaussianBlur(radius=rim_light_blur_radius)) # Suavizar los bordes
            
            draw = ImageDraw.Draw(rim_light_img)
            # Iterar para crear múltiples capas de rim light con opacidad decreciente
            for i in range(rim_light_iterations):
                offset = i * rim_light_offset_multiplier
                # Dibujar un rectángulo alrededor de la imagen con opacidad decreciente
                draw.rectangle([offset, offset, width-offset, height-offset], 
                            outline=(255, 255, 255, rim_light_alpha_start - i*rim_light_alpha_decrement), width=rim_light_outline_width)
            
            rim_light_img = rim_light_img.filter(ImageFilter.GaussianBlur(radius=rim_light_blur_radius)) # Desenfoque final del rim light
        
        # 5. Combinar todos los efectos
        # Primero la sombra para que esté detrás de la imagen
        result = Image.alpha_composite(result, shadow_layer)
        
        # Luego la imagen original con mejoras aplicadas
        enhanced_img = img.copy()
        
        # Aplicar viñeta sutil (si está habilitada)
        if enable_vignette_effect:
            vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(vignette)
            
            # Gradiente radial inverso para el efecto de viñeta (oscurecer bordes)
            center_x, center_y = width // 2, height // 2
            max_radius = min(width, height) // 2
            
            for i in range(max_radius, 0, -VIGNETTE_GRADIENT_STEP):
                # Dibujar elipses concéntricas para crear el efecto de viñeta
                alpha = int(vignette_alpha_start * (1 - i / max_radius))
                draw.ellipse([center_x - i, center_y - i, 
                             center_x + i, center_y + i], 
                            outline=(0, 0, 0, alpha), width=vignette_outline_width)
            vignette = vignette.filter(ImageFilter.GaussianBlur(radius=vignette_blur_radius))
            enhanced_img = Image.alpha_composite(enhanced_img, vignette)

        result = Image.alpha_composite(result, enhanced_img)
        
        # Agregar highlights sobre la imagen mejorada
        result = Image.alpha_composite(result, highlight)
        
        # Agregar efecto de profundidad (si está habilitado)
        if enable_depth_effect:
            result = Image.alpha_composite(result, depth)
        
        # Agregar rim light (si está habilitado)
        if enable_rim_light_effect:
            result = Image.alpha_composite(result, rim_light_img) # Usar rim_light_img
        
        # 6. Aplicar toque final de nitidez con Unsharp Mask
        print("INFO: Aplicando máscara de enfoque final.")
        result = result.filter(ImageFilter.UnsharpMask(radius=unsharp_mask_radius, percent=unsharp_mask_percent, threshold=unsharp_mask_threshold))
        
        # Asegurar que el directorio de salida existe antes de guardar el archivo
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Guardar la imagen final como PNG con los DPI especificados y optimización
        result.save(output_path, 'PNG', dpi=(dpi, dpi), optimize=True)
        
        print("OK: Proceso de conversión y efectos completado exitosamente.")
        print("Tamaño: " + str(target_size[0]) + "x" + str(target_size[1]) + " px")
        print("DPI: " + str(dpi))
        print("Efectos: Sombra realista, iluminación, profundidad, brillo de bordes, viñeta (según configuración)")
        
        return True
        
    except Exception as e:
        print("ERROR: Error crítico durante el procesamiento de imagen: " + str(e))
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Convierte imagen a PNG con fondo transparente y efectos 3D personalizables.")
    parser.add_argument("input_path", help="Ruta de la imagen de entrada.")
    parser.add_argument("output_path", help="Ruta de la imagen de salida (PNG).")
    parser.add_argument("--black_threshold", type=int, default=BLACK_THRESHOLD, help="Umbral para detectar negro (0-255).")
    parser.add_argument("--white_threshold", type=int, default=WHITE_THRESHOLD, help="Umbral para detectar blanco (0-255).")
    parser.add_argument("--sharpness_factor", type=float, default=SHARPNESS_FACTOR, help="Factor de nitidez para smart_sharpen (ej. 1.5).")
    parser.add_argument("--contrast_factor", type=float, default=CONTRAST_FACTOR, help="Factor de contraste para ImageEnhance.Contrast (ej. 1.1).")
    parser.add_argument("--saturation_factor", type=float, default=COLOR_FACTOR, help="Factor de saturación para enhance_colors (ej. 1.2).")
    parser.add_argument("--brightness_factor", type=float, default=1.05, help="Factor de brillo para enhance_colors (ej. 1.05).")
    parser.add_argument("--output_size", type=str, default="2048", help="Tamaño de salida (ej. '512', '1024', '2048' o 'original').")
    parser.add_argument("--shadow_offset", type=int, default=SHADOW_OFFSET, help="Desplazamiento de la sombra en píxeles.")
    parser.add_argument("--shadow_blur_radius", type=int, default=SHADOW_BLUR_RADIUS, help="Radio de desenfoque de la sombra.")
    parser.add_argument("--shadow_alpha_start", type=int, default=SHADOW_COLOR_ALPHA[3], help="Transparencia inicial de la sombra (0-255).")
    parser.add_argument("--highlight_alpha_start", type=int, default=HIGHLIGHT_ALPHA_START, help="Transparencia inicial del highlight (0-255).")
    parser.add_argument("--depth_alpha_start", type=int, default=DEPTH_ALPHA_START, help="Transparencia inicial del efecto de profundidad (0-255).")
    parser.add_argument("--depth_outline_width", type=int, default=DEPTH_OUTLINE_WIDTH, help="Ancho del contorno del efecto de profundidad.")
    parser.add_argument("--depth_blur_radius", type=int, default=DEPTH_BLUR_RADIUS, help="Radio de desenfoque del efecto de profundidad.")
    parser.add_argument("--rim_light_alpha_start", type=int, default=RIM_LIGHT_ALPHA_START, help="Transparencia inicial del rim light (0-255).")
    parser.add_argument("--rim_light_iterations", type=int, default=RIM_LIGHT_ITERATIONS, help="Número de iteraciones para el rim light.")
    parser.add_argument("--rim_light_offset_multiplier", type=int, default=RIM_LIGHT_OFFSET_MULTIPLIER, help="Multiplicador de offset para el rim light.")
    parser.add_argument("--rim_light_alpha_decrement", type=int, default=RIM_LIGHT_ALPHA_DECREMENT, help="Decremento de transparencia para el rim light por iteración.")
    parser.add_argument("--rim_light_outline_width", type=int, default=RIM_LIGHT_OUTLINE_WIDTH, help="Ancho del contorno para el rim light.")
    parser.add_argument("--rim_light_blur_radius", type=int, default=RIM_LIGHT_BLUR_RADIUS, help="Radio de desenfoque del rim light.")
    parser.add_argument("--vignette_alpha_start", type=int, default=VIGNETTE_ALPHA_START, help="Transparencia inicial de la viñeta (0-255).")
    parser.add_argument("--vignette_outline_width", type=int, default=VIGNETTE_OUTLINE_WIDTH, help="Ancho del contorno de la viñeta.")
    parser.add_argument("--vignette_blur_radius", type=int, default=VIGNETTE_BLUR_RADIUS, help="Radio de desenfoque de la viñeta.")
    parser.add_argument("--unsharp_mask_radius", type=int, default=UNSHARP_MASK_RADIUS, help="Radio para UnsharpMask.")
    parser.add_argument("--unsharp_mask_percent", type=int, default=UNSHARP_MASK_PERCENT, help="Porcentaje para UnsharpMask.")
    parser.add_argument("--unsharp_mask_threshold", type=int, default=UNSHARP_MASK_THRESHOLD, help="Umbral para UnsharpMask.")
    parser.add_argument("--denoise_strength", type=int, default=3, help="Fuerza de denoising (ej. 3 para ligero, 5 para moderado).")
    parser.add_argument("--smart_sharpen_amount", type=float, default=1.5, help="Cantidad de smart sharpen (ej. 1.5).")
    parser.add_argument("--smart_sharpen_radius", type=int, default=2, help="Radio de smart sharpen.")
    parser.add_argument("--smart_sharpen_threshold", type=int, default=3, help="Umbral de smart sharpen.")
    parser.add_argument("--edge_preserve_smooth_radius", type=int, default=1, help="Radio de suavizado con preservación de bordes.")
    parser.add_argument("--enable_depth", type=bool, default=True, help="Habilita el efecto de profundidad.")
    parser.add_argument("--enable_vignette", type=bool, default=True, help="Habilita el efecto de viñeta.")
    parser.add_argument("--enable_rim_light", type=bool, default=False, help="Habilita el efecto de rim light.")
    parser.add_argument("--use_ai", action='store_true', help="Usar rembg (IA) para eliminar el fondo.")
    
    args = parser.parse_args()
    
    # Configurar codificación para Windows (si es necesario)
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    # Verificar que el archivo de entrada existe
    if not os.path.exists(args.input_path):
        print("ERROR: El archivo de entrada no existe: " + args.input_path)
        sys.exit(1) # Salir con código de error
    
    # Determinar tamaño de salida
    target_size = None
    if args.output_size.lower() != "original":
        try:
            size = int(args.output_size)
            target_size = (size, size)
        except ValueError:
            print("ERROR: El tamaño de salida debe ser un número entero o 'original'.")
            sys.exit(1)

    success = crear_efecto_3d_realista(
        args.input_path, 
        args.output_path,
        use_ai=args.use_ai,
        target_size=target_size,
        sharpness_factor=args.sharpness_factor,
        contrast_factor=args.contrast_factor,
        saturation_factor=args.saturation_factor,
        brightness_factor=args.brightness_factor,
        shadow_offset=args.shadow_offset,
        shadow_blur_radius=args.shadow_blur_radius,
        highlight_alpha_start=args.highlight_alpha_start,
        depth_alpha_start=args.depth_alpha_start,
        depth_outline_width=args.depth_outline_width,
        depth_blur_radius=args.depth_blur_radius,
        rim_light_alpha_start=args.rim_light_alpha_start,
        rim_light_iterations=args.rim_light_iterations,
        rim_light_offset_multiplier=args.rim_light_offset_multiplier,
        rim_light_alpha_decrement=args.rim_light_alpha_decrement,
        rim_light_outline_width=args.rim_light_outline_width,
        rim_light_blur_radius=args.rim_light_blur_radius,
        vignette_alpha_start=args.vignette_alpha_start,
        vignette_outline_width=args.vignette_outline_width,
        vignette_blur_radius=args.vignette_blur_radius,
        unsharp_mask_radius=args.unsharp_mask_radius,
        unsharp_mask_percent=args.unsharp_mask_percent,
        unsharp_mask_threshold=args.unsharp_mask_threshold,
        shadow_alpha_start=args.shadow_alpha_start,
        black_threshold=args.black_threshold,
        white_threshold=args.white_threshold,
        denoise_strength=args.denoise_strength,
        smart_sharpen_amount=args.smart_sharpen_amount,
        smart_sharpen_radius=args.smart_sharpen_radius,
        smart_sharpen_threshold=args.smart_sharpen_threshold,
        edge_preserve_smooth_radius=args.edge_preserve_smooth_radius,
        enable_depth_effect=args.enable_depth,
        enable_vignette_effect=args.enable_vignette,
        enable_rim_light_effect=args.enable_rim_light
    )
    
    if success:
        print("Proceso completado con exito!")
    else:
        print("Proceso fallido")
        sys.exit(1) # Salir con código de error si falla el proceso

if __name__ == "__main__":
    main()
