import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/workflows/release.yml/runs?per_page=50")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    print(data['workflow_runs'][496 - data['workflow_runs'][-1]['run_number']]['head_commit']['message'])
