import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/runs?per_page=3")
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for run in data['workflow_runs']:
            print(f"Run #{run['run_number']} - {run['name']} - Status: {run['status']} - Conclusion: {run['conclusion']} - Updated: {run['updated_at']}")
except Exception as e:
    print(e)
