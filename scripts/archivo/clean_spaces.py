import os

def clean_trailing_spaces(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                new_lines = [line.rstrip() + '\n' for line in lines]
                
                if lines != new_lines:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    count += 1
    return count

print("Cleaned trailing spaces in", clean_trailing_spaces("src"), "files")
