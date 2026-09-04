import re

with open(".github/workflows/release.yml", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """        - name: Asegurar cara web TV oculta en el paquete
          shell: pwsh
          run: |
            New-Item -ItemType Directory -Force -Path "dist/CobroFacil_POS/_internal" | Out-Null
            if (Test-Path "build/tv_cara.bin") {
              Copy-Item -Force "build/tv_cara.bin" "dist/CobroFacil_POS/_internal/tv_cara.bin"
            } else {
              python src/carteleria/lanzador_tv/tv_cara_pack.py pack "dist/CobroFacil_POS/_internal/tv_cara.bin"
            }
            
            if (-not (Test-Path "dist/CobroFacil_POS/_internal/tv_cara.bin")) {
              Write-Error "Falta tv_cara.bin en el paquete"
              exit 1
            }
            
            if (Test-Path "dist/CobroFacil_POS/src") {
                Remove-Item -Recurse -Force "dist/CobroFacil_POS/src" -ErrorAction SilentlyContinue
            }
            Get-ChildItem -Path dist/CobroFacil_POS -Recurse -Directory -Filter la_cara_web -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            
            Write-Host "OK cara web TV oculta (tv_cara.bin)"
"""

text = re.sub(r'        - name: Asegurar cara web TV oculta en el paquete\n          shell: pwsh\n          run: \|\n            New-Item -ItemType Directory -Force -Path "dist/CobroFacil_POS/_internal" \| Out-Null.*?Write-Host "OK cara web TV oculta \(tv_cara\.bin\)"\n', replacement, text, flags=re.DOTALL)

with open(".github/workflows/release.yml", "w", encoding="utf-8", newline="") as f:
    f.write(text)
