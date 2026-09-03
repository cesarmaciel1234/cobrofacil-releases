import re

with open(".github/workflows/release.yml", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """        - name: Asegurar cara web TV oculta en el paquete
          shell: pwsh
          run: |
            try {
              New-Item -ItemType Directory -Force -Path "dist/CobroFacil_POS/_internal" | Out-Null
              if (Test-Path "build/tv_cara.bin") {
                Copy-Item -Force "build/tv_cara.bin" "dist/CobroFacil_POS/_internal/tv_cara.bin"
              }
              $out = python src/carteleria/lanzador_tv/tv_cara_pack.py dist dist/CobroFacil_POS 2>&1
              if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR EN PYTHON:"
                Write-Host $out
                Write-Error "Python script failed"
                exit 1
              }
              if (-not (Test-Path "dist/CobroFacil_POS/_internal/tv_cara.bin")) {
                Write-Error "Falta tv_cara.bin en el paquete"
                exit 1
              }
              Write-Host "OK cara web TV oculta (tv_cara.bin)"
            } catch {
              Write-Host "CATCH ERROR:"
              Write-Host $_
              exit 1
            }"""

text = re.sub(r'        - name: Asegurar cara web TV oculta en el paquete.*?Write-Host "OK cara web TV oculta \(tv_cara\.bin\)"', replacement, text, flags=re.DOTALL)

with open(".github/workflows/release.yml", "w", encoding="utf-8", newline="") as f:
    f.write(text)
