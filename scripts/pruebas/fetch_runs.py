import urllib.request, json
url = "https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/actions/runs"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    for r in data.get("workflow_runs", [])[:10]:
        print(f"{r['name']} - {r['status']} - {r['conclusion']} - {r['jobs_url']}")
        if r['name'] == 'Build y Release Windows' and r['conclusion'] == 'failure':
            job_req = urllib.request.Request(r['jobs_url'], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(job_req) as jresp:
                jdata = json.loads(jresp.read().decode())
                for j in jdata.get("jobs", []):
                    print(f"  Job: {j['name']} - {j['conclusion']}")
                    for step in j.get("steps", []):
                        if step['conclusion'] == 'failure':
                            print(f"    Failed Step: {step['name']}")
