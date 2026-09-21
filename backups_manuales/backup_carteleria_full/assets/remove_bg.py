from PIL import Image

def remove_white_bg(input_path, output_path, tolerance=50):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # Check if the pixel is close to white
        if item[0] > 255 - tolerance and item[1] > 255 - tolerance and item[2] > 255 - tolerance:
            # Make it transparent
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved {output_path}")

input_file = r"C:\Users\cesar\.gemini\antigravity\brain\b37b66f0-14e0-4a0f-b0b6-504ca8c04142\chef_lobo_sentado_1781239319688.png"
output_file = r"c:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\vistas\assets\chef_lobo_volador.png"
remove_white_bg(input_file, output_file)
