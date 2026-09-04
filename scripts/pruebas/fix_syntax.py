with open("src/carteleria/creador_png/panel_png_productos.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip() == "return (":
        if lines[i+1].strip() == "False,":
            if "f\"No se pudo enviar el PNG a la maestra {db_host}." in lines[i+2]:
                new_lines.extend([
                    "        return (\n",
                    "            False,\n",
                    "            f\"No se pudo enviar el PNG a la maestra {db_host}.\\n\"\n",
                    "            \"Encendé esa PC y el Servidor de Tienda (puerto 8000).\\n\"\n",
                    "            f\"{err_mostrar}\",\n",
                    "        )\n"
                ])
                skip = 6
                continue
    if skip > 0:
        skip -= 1
        continue
    new_lines.append(line)

with open("src/carteleria/creador_png/panel_png_productos.py", "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)
