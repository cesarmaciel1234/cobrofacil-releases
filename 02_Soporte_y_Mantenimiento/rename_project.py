import os
import glob

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip non-text files

    new_content = content
    # Exact case replacements
    new_content = new_content.replace('CobroFacil_POS', 'CobroFacil_POS')
    new_content = new_content.replace('Cobro Fácil POS', 'Cobro Fácil POS')
    new_content = new_content.replace('cobrofacil', 'cobrofacil')
    new_content = new_content.replace('CobroFacil', 'CobroFacil')

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {filepath}")

def main():
    extensions = ['*.py', '*.bat', '*.md', '*.iss', '*.json', '*.spec']
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for root, _, files in os.walk(base_dir):
        if '.venv' in root or '.git' in root or '__pycache__' in root or 'dist' in root or 'build' in root:
            continue
            
        for ext in extensions:
            for filepath in glob.glob(os.path.join(root, ext)):
                replace_in_file(filepath)

if __name__ == '__main__':
    main()
