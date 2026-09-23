import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

code = code.replace('next_idx = (curr_idx - 3)', 'next_idx = (curr_idx - 5)')
code = code.replace('next_idx = (curr_idx + 3)', 'next_idx = (curr_idx + 5)')

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Navigation fixed!")
