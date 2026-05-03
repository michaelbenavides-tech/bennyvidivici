import json
import urllib.request

for url in ["http://localhost/health", "http://localhost/api/v1/projects"]:
    with urllib.request.urlopen(url, timeout=10) as response:
        print(url, response.status, json.loads(response.read() or b"{}"))
