import codecs

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

code = code.replace(
    'item = QListWidgetItem(f"{r[\'nombre\']} - ")',
    'item = QListWidgetItem(f"{r[\'nombre\']} - ${r[\'precio\']:.2f}  [Stock: {stk_str}]")'
)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Fixed price!")
