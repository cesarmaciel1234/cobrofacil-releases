import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/issues?state=all&per_page=3")
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for issue in data:
            print(f"Issue #{issue['number']}: {issue['title']} - State: {issue['state']}")
            print(f"Body: {issue.get('body', '')[:100]}")
except Exception as e:
    print(e)
