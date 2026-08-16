"""Generador de iconos PNG del clima para cartelería TV.

Este script crea iconos básicos del clima (sol, nube, lluvia) como respaldo
en caso de que los archivos PNG originales no se copien correctamente durante
la compilación con PyInstaller.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# Configuración de iconos
ICONOS_CONFIG = {
    "sol": {
        "bg_color": (255, 200, 50),      # Amarillo brillante
        "emoji": "☀️",
        "title": "Sol"
    },
    "nube": {
        "bg_color": (200, 200, 220),    # Gris azulado claro
        "emoji": "☁️",
        "title": "Nube"
    },
    "lluvia": {
        "bg_color": (100, 150, 200),    # Azul grisáceo
        "emoji": "🌧️",
        "title": "Lluvia"
    }
}

def crear_icono_clima(nombre: str, output_path: str, size: tuple = (64, 64)):
    """Crea un icono PNG del clima con diseño básico."""
    config = ICONOS_CONFIG.get(nombre, ICONOS_CONFIG["sol"])
    
    # Crear imagen con fondo degradado
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Fondo circular con color del clima
    margin = 4
    circle_bbox = (margin, margin, size[0] - margin, size[1] - margin)
    draw.ellipse(circle_bbox, fill=config["bg_color"] + (255,))
    
    # Intentar usar emoji del sistema
    try:
        # Buscar fuente que soporte emojis
        font_size = size[0] // 2
        try:
            # Windows
            font = ImageFont.truetype("seguiemj.ttf", font_size)
        except:
            try:
                # Fuentes comunes
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Centrar emoji
        text_bbox = draw.textbbox((0, 0), config["emoji"], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (size[0] - text_width) // 2
        text_y = (size[1] - text_height) // 2 - 2
        draw.text((text_x, text_y), config["emoji"], font=font, fill=(255, 255, 255, 255))
        
    except Exception as e:
        logger.warning(f"No se pudo usar emoji para {nombre}: {e}")
        # Fallback: dibujar icono geométrico simple
        if nombre == "sol":
            # Dibujar sol simple
            center = size[0] // 2
            radius = size[0] // 4
            draw.ellipse((center - radius, center - radius, center + radius, center + radius), 
                        fill=(255, 255, 0, 255))
        elif nombre == "nube":
            # Dibujar nube simple (círculos superpuestos)
            center = size[0] // 2
            draw.ellipse((center - 20, center - 15, center - 5, center + 5), fill=(255, 255, 255, 255))
            draw.ellipse((center - 10, center - 20, center + 10, center + 5), fill=(255, 255, 255, 255))
            draw.ellipse((center + 5, center - 15, center + 20, center + 5), fill=(255, 255, 255, 255))
        elif nombre == "lluvia":
            # Dibujar nube + gotas
            center = size[0] // 2
            draw.ellipse((center - 15, center - 18, center + 15, center + 2), fill=(200, 200, 200, 255))
            # Gotas de lluvia
            for i in range(3):
                x = center - 10 + (i * 10)
                y = center + 5
                draw.ellipse((x, y, x + 3, y + 8), fill=(100, 150, 255, 255))
    
    # Guardar imagen
    img.save(output_path, 'PNG')
    logger.info(f"Icono creado: {output_path}")

def generar_todos_los_iconos():
    """Genera todos los iconos del clima en la carpeta assets."""
    try:
        from src.utils.paths import get_base_path
        base_path = get_base_path()
        assets_dir = os.path.join(base_path, "src", "carteleria", "lanzador_tv", "la_cara_web", "assets")
    except Exception:
        # Fallback si no podemos importar paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, "la_cara_web", "assets")
    
    os.makedirs(assets_dir, exist_ok=True)
    
    iconos_creados = []
    for nombre in ICONOS_CONFIG.keys():
        output_path = os.path.join(assets_dir, f"{nombre}.png")
        
        # Solo crear si no existe o está corrupto
        crear = True
        if os.path.exists(output_path):
            try:
                # Verificar que el archivo sea válido
                with Image.open(output_path) as img:
                    img.verify()
                crear = False
                logger.info(f"Icono existente válido: {output_path}")
            except Exception:
                logger.warning(f"Icono corrupto, reemplazando: {output_path}")
        
        if crear:
            try:
                crear_icono_clima(nombre, output_path)
                iconos_creados.append(output_path)
            except Exception as e:
                logger.error(f"Error creando icono {nombre}: {e}")
    
    return iconos_creados

def main():
    """Función principal para ejecutar desde línea de comandos."""
    logging.basicConfig(level=logging.INFO)
    print("Generando iconos del clima para cartelería TV...")
    iconos = generar_todos_los_iconos()
    if iconos:
        print(f"[OK] {len(iconos)} iconos creados correctamente")
    else:
        print("[OK] Todos los iconos ya existen y son validos")

if __name__ == "__main__":
    main()