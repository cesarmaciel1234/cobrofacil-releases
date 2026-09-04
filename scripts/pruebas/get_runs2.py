import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/workflows/release.yml/runs?per_page=40")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    for run in data['workflow_runs']:
        print(f"Run #{run['run_number']} - {run['conclusion']}")
