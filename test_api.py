import requests
import json

url = "http://localhost:8000/api/social-icebreaker/card"
data = {
    "name": "测试用户",
    "birth_date": "1990-01-01",
    "birth_time": "12:00",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "birth_place": "北京",
    "house_system": "placidus"
}

try:
    response = requests.post(url, json=data, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
