import json
with open("version.json", "r", encoding="utf-8") as f:
    data = json.load(f)
data["app_version"] = "13.2.0"
with open("version.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
