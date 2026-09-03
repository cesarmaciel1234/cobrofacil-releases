import urllib.request
import json
req = urllib.request.Request("https://api.github.com/repos/cesarmaciel1234/cobrofacil-releases/releases/tags/v13.2.2")
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Release: {data['name']}")
        for asset in data.get('assets', []):
            print(f"Asset: {asset['name']} - {asset['state']}")
except Exception as e:
    print(e)
