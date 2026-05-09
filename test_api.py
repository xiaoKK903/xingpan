import requests

base_url = 'http://localhost:8000/api'

print('=== 1. 用新用户登录 ===')
login_data = {'username': 'testuser2', 'password': '123456'}
r = requests.post(f'{base_url}/users/login', data=login_data)
print(f'登录: {r.status_code}')
if r.status_code == 200:
    token = r.json().get('data', {}).get('access_token', '')
    print(f'获取Token: {token[:20]}...')
else:
    print(f'登录失败: {r.text}')
    token = ''

print('\n=== 2. 计算星盘 ===')
headers = {'Authorization': f'Bearer {token}'} if token else {}
chart_data = {
    'birth_date': '2000-01-01',
    'birth_time': '12:00',
    'latitude': 39.9042,
    'longitude': 116.4074,
    'birth_place': '北京'
}
r = requests.post(f'{base_url}/astro/calculate', json=chart_data, headers=headers)
print(f'星盘计算: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'message: {data.get("message")}')
    chart = data.get('data', {}).get('chart', {})
    planets = chart.get('planets', [])
    print(f'行星数量: {len(planets)}')
    for p in planets:
        print(f"  {p.get('name')}: {p.get('zodiac', {}).get('sign')} 第{p.get('house')}宫")
else:
    print(f'错误: {r.text}')
