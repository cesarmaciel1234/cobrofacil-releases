import json

transcript_path = r"C:\Users\cesar\.gemini\antigravity\brain\7ef542c2-e200-4638-9e30-e356f963fd7a\.system_generated\logs\transcript.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            idx = data.get("step_index")
            if 1640 <= idx <= 1725:
                print(f"Step {idx} ({data.get('type')}, {data.get('source')}):")
                if 'content' in data and data['content']:
                    print(data['content'][:600])
                if 'tool_calls' in data and data['tool_calls']:
                    print("Tool Calls:", json.dumps(data['tool_calls'], indent=2)[:300])
                print("-" * 50)
        except Exception as e:
            pass
