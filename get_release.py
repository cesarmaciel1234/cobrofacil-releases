import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/workflows/release.yml/runs?per_page=1")
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    jobs_url = data['workflow_runs'][0]['jobs_url']
    req2 = urllib.request.Request(jobs_url)
    with urllib.request.urlopen(req2) as resp2:
        data2 = json.loads(resp2.read().decode())
        for job in data2['jobs']:
            print(f"Job: {job['name']}, Status: {job['status']}, Conclusion: {job['conclusion']}")
            for step in job['steps']:
                if step['conclusion'] == 'failure':
                    print(f"  Step failed: {step['name']}")
                    # let's download the logs for this job? No, logs are zipped at run level.
