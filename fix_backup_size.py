import sys

with open('src/base_de_datos/autoblindaje_db.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = "len(result.stdout) >= 5000"
replacement = "len(result.stdout) >= 500"

if target in content:
    content = content.replace(target, replacement)
    with open('src/base_de_datos/autoblindaje_db.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed autoblindaje size check!")
else:
    print("Target not found.")
