import requests
import json

URL = "http://localhost:8000/api/v1/query/search"

payload = {
    "query": "git commit",
    "course_code": "CS101"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(URL, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(response.text)
except Exception as e:
    print("Error:", e)
