import codecs

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

from_str = 'Qt.KeepAspectRatio, Qt.SmoothTransformation'
to_str = 'Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation'

code = code.replace(from_str, to_str)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Enums fixed!")
