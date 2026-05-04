"""测试故事墙 API"""
import requests
import json

BASE_URL = 'http://localhost:8001/api'

print("=" * 60)
print("测试故事墙 API")
print("=" * 60)

form_data = {'username': 'test', 'password': 'test123'}
response = requests.post(f'{BASE_URL}/users/login', data=form_data)
data = response.json()
token = data.get('data', {}).get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print("\n1. 获取我的故事墙 (已挂载卡片)...")
response = requests.get(f'{BASE_URL}/story-card/story-wall', headers=headers)
result = response.json()
print(f"   code: {result.get('code')}")
cards = result.get('data', {}).get('cards', [])
stats = result.get('data', {}).get('stats', {})
print(f"   已挂载卡片数: {len(cards)}")
print(f"   统计: {json.dumps(stats, ensure_ascii=False)}")
for card in cards:
    print(f"   - {card['headline']} ({card['rarity_name']})")

print("\n2. 获取我的卡片列表 (全部卡片)...")
response = requests.get(
    f'{BASE_URL}/story-card/my-cards', 
    headers=headers, 
    params={'page': 1, 'page_size': 20}
)
result = response.json()
print(f"   code: {result.get('code')}")
items = result.get('data', {}).get('items', [])
total = result.get('data', {}).get('total', 0)
print(f"   总计: {total} 张")
print(f"   当前页: {len(items)} 张")
for card in items:
    status = '已挂载' if card.get('is_mounted') else '未挂载'
    print(f"   - {card['headline']} ({card['rarity_name']}) - {status}")

print("\n" + "=" * 60)
print("API 测试完成!")
print("=" * 60)
