import sys
import requests

r = requests.post("http://localhost:8000", json={"label": "healthcheck"})
if (r.status_code == 200):
    sys.exit(0)
else:
    sys.exit(1)
