import re

with open(".github/workflows/release.yml", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith("        - name: Asegurar cara web TV"):
        skip = True
        new_lines.extend([
            "      - name: Asegurar cara web TV oculta en el paquete\n",
            "        shell: pwsh\n",
            "        run: |\n",
            "          New-Item -ItemType Directory -Force -Path \"dist/CobroFacil_POS/_internal\" | Out-Null\n",
            "          if (Test-Path \"build/tv_cara.bin\") {\n",
            "            Copy-Item -Force \"build/tv_cara.bin\" \"dist/CobroFacil_POS/_internal/tv_cara.bin\"\n",
            "          } else {\n",
            "            python src/carteleria/lanzador_tv/tv_cara_pack.py pack \"dist/CobroFacil_POS/_internal/tv_cara.bin\"\n",
            "          }\n",
            "          if (-not (Test-Path \"dist/CobroFacil_POS/_internal/tv_cara.bin\")) {\n",
            "            Write-Error \"Falta tv_cara.bin en el paquete\"\n",
            "            exit 1\n",
            "          }\n",
            "          if (Test-Path \"dist/CobroFacil_POS/src\") {\n",
            "              Remove-Item -Recurse -Force \"dist/CobroFacil_POS/src\" -ErrorAction SilentlyContinue\n",
            "          }\n",
            "          Get-ChildItem -Path dist/CobroFacil_POS -Recurse -Directory -Filter la_cara_web -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue\n",
            "          Write-Host \"OK cara web TV oculta (tv_cara.bin)\"\n"
        ])
        continue
    if skip:
        if line.startswith("        - name: Copiar version.json"):
            skip = False
            new_lines.append("      - name: Copiar version.json y launcher autónomo\n")
            continue
        elif line.startswith("      - name: Copiar version.json"):
            skip = False
            new_lines.append(line)
            continue
        else:
            continue
    new_lines.append(line)

with open(".github/workflows/release.yml", "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)
