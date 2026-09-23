import json
path = 'version.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
data['app_version'] = 'v16.31'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
