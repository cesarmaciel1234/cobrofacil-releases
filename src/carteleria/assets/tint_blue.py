from PIL import Image

def tint_blue(path):
    img = Image.open(path).convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        r, g, b, a = item
        if a > 0:
            # If it's a bright pixel (like a white/grey cloud), tint it light blue
            if r > 180 and g > 180 and b > 180:
                new_data.append((100, 180, 255, a))
            else:
                new_data.append(item)
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(path, "PNG")

tint_blue(r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\vistas\assets\nube.png")
tint_blue(r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\vistas\assets\lluvia.png")
print("Tinted clouds to blue successfully!")
