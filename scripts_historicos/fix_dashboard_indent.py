import codecs
import re

text = codecs.open('src/jefe/jefe0_dashboard.py', 'r', encoding='utf-8').read()

# The issue is we commented out 'L = {' but left the rest of the dictionary uncommented, causing an indentation error
# Let's completely remove the old L dictionary.

# First, restore the old L dictionary just to easily match it if it's broken
text = text.replace('from src.jefe.theme_pro import THEME_PRO as L\n# L = {', 'L = {')

# Now find the L = { ... } block and replace it entirely
match = re.search(r'L = \{.*?\}', text, re.DOTALL)
if match:
    text = text.replace(match.group(0), 'from src.jefe.theme_pro import THEME_PRO as L')

codecs.open('src/jefe/jefe0_dashboard.py', 'w', encoding='utf-8').write(text)
print('Fixed Indentation Error!')
