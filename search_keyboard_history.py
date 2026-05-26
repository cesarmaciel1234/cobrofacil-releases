import json

transcript_path = r"C:\Users\cesar\.gemini\antigravity\brain\7ef542c2-e200-4638-9e30-e356f963fd7a\.system_generated\logs\transcript.jsonl"

terms = ["horizontal", "invertido", "teclado", "paso5", "alfabeto"]
with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("type") == "USER_INPUT":
                content = data.get("content", "").lower()
                if any(t in content for t in terms):
                    print(f"Step {data.get('step_index')}: {data.get('content')}\n")
        except Exception as e:
            pass
