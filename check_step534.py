import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/runs?per_page=10")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    for run in data['workflow_runs']:
        if run['run_number'] == 534:
            jobs_url = run['jobs_url']
            req2 = urllib.request.Request(jobs_url)
            with urllib.request.urlopen(req2) as resp2:
                data2 = json.loads(resp2.read().decode())
                for job in data2['jobs']:
                    for step in job['steps']:
                        if step['conclusion'] == 'failure':
                            print(f"Run 534 Failed at step: {step['name']}")
