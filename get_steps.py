import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/runs/33660803245/jobs")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    for job in data['jobs']:
        print(f"Job: {job['name']}, Status: {job['status']}, Conclusion: {job['conclusion']}")
        for step in job['steps']:
            if step['conclusion'] == 'failure':
                print(f"  Step failed: {step['name']}")
