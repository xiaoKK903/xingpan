"""测试故事墙 API"""
import requests
import json
import sys

BASE_URL = 'http://localhost:8001/api'

print("=" * 60)
print("测试故事墙 API")
print("=" * 60)

# 先登录获取 token
print("\n1. 登录获取 token...")
form_data = {
    'username': 'test',
    'password': 'test123'
}
response = requests.post(f'{BASE_URL}/users/login', data=form_data)
print(f'状态码: {response.status_code}')

token = None
try:
    data = response.json()
    if data.get('code') == 200:
        token = data.get('data', {}).get('access_token')
        print(f'✓ 登录成功，token: {token[:60]}...')
    else:
        print(f'✗ 登录失败: {data.get("message")}')
        sys.exit(1)
except Exception as e:
    print(f'错误: {e}')
    print(f'响应: {response.text}')
    sys.exit(1)

headers = {
    'Authorization': f'Bearer {token}'
}

# 测试获取我的故事墙
print("\n2. 测试获取我的故事墙...")
try:
    response = requests.get(f'{BASE_URL}/story-card/story-wall', headers=headers)
    print(f'状态码: {response.status_code}')
    data = response.json()
    print(f'响应: {json.dumps(data, ensure_ascii=False, indent=2)}')
    
    if isinstance(data, dict):
        if data.get('code') == 200:
            cards = data.get('data', {}).get('cards', [])
            print(f'\n✓ 获取成功，共 {len(cards)} 张卡片')
        else:
            print(f'\n✗ API 返回错误: {data.get("message")}')
except Exception as e:
    print(f'错误: {e}')
    print(f'响应: {response.text}')

# 测试获取我的卡片列表
print("\n3. 测试获取我的卡片列表...")
try:
    response = requests.get(
        f'{BASE_URL}/story-card/my-cards', 
        headers=headers,
        params={'page': 1, 'page_size': 20}
    )
    print(f'状态码: {response.status_code}')
    data = response.json()
    print(f'响应: {json.dumps(data, ensure_ascii=False, indent=2)}')
    
    if isinstance(data, dict):
        if data.get('code') == 200:
            items = data.get('data', {}).get('items', [])
            total = data.get('data', {}).get('total', 0)
            print(f'\n✓ 获取成功，共 {total} 张卡片，当前页 {len(items)} 张')
        else:
            print(f'\n✗ API 返回错误: {data.get("message")}')
except Exception as e:
    print(f'错误: {e}')
    print(f'响应: {response.text}')

# 检查数据库中是否有 story_cards 表和数据
print("\n4. 检查数据库...")
try:
    import sqlite3
    from app.config import settings
    
    db_url = settings.DATABASE_URL
    # 从 sqlite:///./data/app.db 中提取路径
    db_path = db_url.replace('sqlite:///', '')
    
    print(f'数据库路径: {db_path}')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='story_cards'")
    table_exists = cursor.fetchone()
    print(f'story_cards 表存在: {table_exists is not None}')
    
    if table_exists:
        # 检查表结构
        cursor.execute("PRAGMA table_info(story_cards)")
        columns = cursor.fetchall()
        print(f'表列数: {len(columns)}')
        for col in columns:
            print(f'  - {col[1]} ({col[2]})')
        
        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM story_cards")
        count = cursor.fetchone()[0]
        print(f'表中数据行数: {count}')
        
        if count > 0:
            cursor.execute("SELECT id, user_id, headline, is_mounted FROM story_cards LIMIT 5")
            rows = cursor.fetchall()
            print(f'示例数据:')
            for row in rows:
                print(f'  - id={row[0]}, user_id={row[1]}, headline={row[2][:30] if row[2] else None}..., is_mounted={row[3]}')
    
    conn.close()
except Exception as e:
    print(f'检查数据库失败: {e}')
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
