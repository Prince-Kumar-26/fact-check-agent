import requests
resp = requests.post("http://127.0.0.1:8000/api/factcheck/stream", json={"claim": "Water boils at 100 degrees Celsius."}, stream=True)
print("Status:", resp.status_code)
for line in resp.iter_lines():
    if line:
        print(line.decode())
