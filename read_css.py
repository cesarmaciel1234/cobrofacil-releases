with open("src/carteleria/lanzador_tv/la_cara_web/css/themes/premium/estilos.css", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i in range(470, 495):
    print(f"{i}: {lines[i].strip()}")
