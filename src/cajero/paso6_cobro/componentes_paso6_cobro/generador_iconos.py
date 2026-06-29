import os

def ensure_icons():
    """Autogenera los iconos recortándolos y haciéndolos transparentes si no existen."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_dir = os.path.join(base_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        required = ["tarjeta.png", "mixto.png", "transferencia.png", "efectivo.png"]
        missing = [r for r in required if not os.path.exists(os.path.join(assets_dir, r))]
        if not missing:
            return

        # Intentar cargar PIL sólo si faltan iconos
        try:
            from PIL import Image, ImageChops
        except ImportError:
            from src.logger import logger
            logger.warning("PIL (Pillow) no está instalado. No se pueden autogenerar iconos faltantes.")
            return

        p1 = os.path.join(assets_dir, "media__1779193497248.png")
        p2 = os.path.join(assets_dir, "media__1779193546849.png")

        def process_and_save(img, save_path):
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            bg = Image.new(img.mode, img.size, (255, 255, 255, 255))
            diff = ImageChops.difference(img, bg)
            diff_rgb = diff.convert('RGB')
            bbox = diff_rgb.getbbox()
            if bbox:
                img = img.crop(bbox)
            
            datas = img.getdata()
            newData = []
            for item in datas:
                if item[0] > 235 and item[1] > 235 and item[2] > 235:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            img.putdata(newData)
            img.save(save_path, "PNG")

        if os.path.exists(p1):
            im1 = Image.open(p1)
            w, h = im1.size
            tarjeta_img = im1.crop((0, 0, int(w * 0.35), h))
            process_and_save(tarjeta_img, os.path.join(assets_dir, "tarjeta.png"))
            mixto_img = im1.crop((int(w * 0.35), 0, int(w * 0.65), h))
            process_and_save(mixto_img, os.path.join(assets_dir, "mixto.png"))
            transf_img = im1.crop((int(w * 0.65), 0, w, h))
            process_and_save(transf_img, os.path.join(assets_dir, "transferencia.png"))

        if os.path.exists(p2):
            im2 = Image.open(p2)
            process_and_save(im2, os.path.join(assets_dir, "efectivo.png"))
    except Exception as e:
        from src.logger import logger
        logger.warning(f"Error autogenerando iconos: {e}")
