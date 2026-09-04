import os
import sys

with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'self._kiosk_profile = os.path.join(tempfile.gettempdir(), "tpv-carteleria-kiosk")'
new = '''import time
        self._kiosk_profile = os.path.join(tempfile.gettempdir(), f"tpv-carteleria-kiosk-{int(time.time())}")'''

content = content.replace(old, new)

with open('src/carteleria/lanzador_tv/cerebro_lanzador_tv.py', 'w', encoding='utf-8') as f:
    f.write(content)
