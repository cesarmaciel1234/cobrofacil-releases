import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/workflows/release.yml/runs?per_page=1")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    for run in data['workflow_runs']:
        jobs_url = run['jobs_url']
        req2 = urllib.request.Request(jobs_url)
        with urllib.request.urlopen(req2) as resp2:
            data2 = json.loads(resp2.read().decode())
            print(json.dumps(data2, indent=2))
