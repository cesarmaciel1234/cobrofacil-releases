import re

def main():
    file_path = r'C:\Users\cesar\OneDrive\Desktop\tpv pro 2026\src\cajero\paso5_terminal\paso5_terminal.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    matches = re.finditer(r'setStyleSheet\((.*?)\)', content, re.DOTALL)
    for m in matches:
        style = m.group(1).replace('\n', ' ').strip()
        if len(style) < 150: # Only print relatively simple ones
            print(style)

if __name__ == '__main__':
    main()
