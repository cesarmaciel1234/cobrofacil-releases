import codecs
import re

with codecs.open('src/main_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace profile 4 (admin)
text = re.sub(r"4:\s+lambda:\s+__import__\('src\.admin\.admin3_reportes',?\s+fromlist=\['Admin3Reportes'\]\)\.Admin3Reportes\(\),",
              "4:  lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['JefeReportes']).JefeReportes(),",
              text)

# Replace profile 20 (jefe)
text = re.sub(r"20:\s+lambda:\s+__import__\('src\.jefe\.jefe_reportes',?\s+fromlist=\['JefeReportes'\]\)\.JefeReportes\(\),",
              "20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['JefeReportes']).JefeReportes(),",
              text)

with codecs.open('src/main_window.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated main_window.py")
