import os
from PIL import Image, ImageDraw, ImageFont

# Crear una imagen 256x256 con fondo azul transparente y un texto/icono
img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Circulo azul
draw.ellipse((10, 10, 246, 246), fill=(41, 98, 255), outline=(20, 50, 150), width=10)

# Texto "CP"
try:
    font = ImageFont.truetype("arialbd.ttf", 100)
except:
    font = ImageFont.load_default()

draw.text((128, 128), "CP", fill="white", font=font, anchor="mm")

# Guardar como logo.ico
img.save("logo.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
print("logo.ico creado")
