import re

with open("src/carteleria/lanzador_tv/tv_cara_pack.py", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'(    except Exception as e:\n        import traceback\n        traceback.print_exc\(\)\n        raise e\n)+', r'\1', text)

with open("src/carteleria/lanzador_tv/tv_cara_pack.py", "w", encoding="utf-8", newline="") as f:
    f.write(text)
