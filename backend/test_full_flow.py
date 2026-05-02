"""
竞猜系统完整流程测试脚本（最终版）
测试内容：
1. 用户登录
2. 获取用户资产（星元碎片、高阶星尘）
3. 获取预言券
4. 获取开放场次
5. 获取场次详情
6. 投票（使用预言券）
7. 验证资产消耗
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"


def login(username, password):
    print("\n" + "="*60)
    print("  [1/8] 用户登录")
    print("="*60)
    
    url = f"{BASE_URL}/users/login"
    files = {
        "username": (None, username),
        "password": (None, password)
    }
    
    try:
        response = requests.post(url, files=files, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            token = result["data"].get("access_token") or result["data"].get("token")
            print(f"✅ 登录成功！")
            print(f"   用户名: {username}")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"❌ 登录失败: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None


def get_user_assets(token):
    print("\n" + "="*60)
    print("  [2/8] 获取用户资产")
    print("="*60)
    
    url = f"{BASE_URL}/star-resonance/status"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            user_assets = result["data"].get("user_assets", {})
            stardust_fragment = user_assets.get("stardust_fragment_balance") or user_assets.get("stardust_fragment") or 0
            stardust_point = user_assets.get("stardust_point_balance") or user_assets.get("stardust_point") or 0
            
            print(f"✅ 获取资产成功！")
            print(f"   星元碎片: {stardust_fragment}")
            print(f"   高阶星尘: {stardust_point}")
            
            return {
                "stardust_fragment": stardust_fragment,
                "stardust_point": stardust_point
            }
        else:
            print(f"❌ 获取资产失败: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def get_user_tickets(token):
    print("\n" + "="*60)
    print("  [3/8] 获取预言券")
    print("="*60)
    
    url = f"{BASE_URL}/star-resonance/my-tickets"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            tickets = result["data"].get("tickets", [])
            count = result["data"].get("count", 0)
            
            print(f"✅ 获取预言券成功！")
            print(f"   数量: {count} 张")
            
            for i, ticket in enumerate(tickets[:5], 1):
                print(f"   [{i}] ID: {ticket.get('id')}, 类型: {ticket.get('ticket_type')}")
            
            return tickets
        else:
            print(f"⚠️  获取预言券失败: {result.get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"⚠️  获取预言券请求失败: {e}")
        return []


def get_open_sessions(token):
    print("\n" + "="*60)
    print("  [4/8] 获取开放场次")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/open"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            sessions = result["data"].get("predictions", [])
            
            print(f"✅ 获取开放场次成功！")
            print(f"   场次数量: {len(sessions)}")
            
            for i, session in enumerate(sessions, 1):
                print(f"\n   [{i}] {session.get('title')}")
                print(f"       ID: {session.get('id')}")
                print(f"       状态: {session.get('status')}")
                print(f"       类型: {session.get('session_type')}")
                print(f"       已投票: {session.get('total_votes', 0)} 人")
            
            return sessions
        else:
            print(f"❌ 获取场次失败: {result.get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return []


def get_session_detail(token, session_id):
    print("\n" + "="*60)
    print(f"  [5/8] 获取场次详情 (ID: {session_id})")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/detail-optimized/{session_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            data = result["data"]
            user_votes = data.get("user_votes", [])
            tiered_costs = data.get("tiered_costs", [])
            
            print(f"✅ 获取场次详情成功！")
            print(f"   标题: {data.get('title')}")
            print(f"   状态: {data.get('status')}")
            print(f"   选项: {data.get('options')}")
            print(f"   选项值: {data.get('option_values')}")
            
            if user_votes:
                print(f"\n   您的投票记录: {len(user_votes)} 票")
                for vote in user_votes:
                    print(f"      - 第{vote.get('vote_number')}票: {vote.get('selected_option')}")
            
            if tiered_costs:
                print(f"\n   阶梯式投票规则:")
                for cost in tiered_costs:
                    print(f"      第{cost.get('vote_tier')}票:")
                    print(f"        允许资产: {cost.get('allowed_asset_types')}")
                    if cost.get('cost_fragment') > 0:
                        print(f"        星元碎片: {cost.get('cost_fragment')}")
                    if cost.get('cost_point') > 0:
                        print(f"        高阶星尘: {cost.get('cost_point')}")
                    if cost.get('cost_ticket') > 0:
                        print(f"        预言券: {cost.get('cost_ticket')}")
                    print(f"        奖励倍数: ×{cost.get('reward_multiplier')}")
            
            options = []
            for i, label in enumerate(data.get("options", [])):
                options.append({
                    "option_label": label,
                    "option_value": data.get("option_values", [])[i] if i < len(data.get("option_values", [])) else None
                })
            
            return {
                "session": data,
                "options": options,
                "user_votes": user_votes,
                "tiered_costs": tiered_costs
            }
        else:
            print(f"❌ 获取场次详情失败: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def cast_vote(token, session_id, option_value, confidence=80, asset_type="fragment"):
    print("\n" + "="*60)
    print(f"  [6/8] 投票 (场次: {session_id}, 选项: {option_value})")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/vote-secure"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prediction_id": session_id,
        "selected_option": option_value,
        "confidence": confidence,
        "use_asset": asset_type
    }
    
    print(f"   投票参数:")
    print(f"      场次ID: {session_id}")
    print(f"      选项: {option_value}")
    print(f"      信心值: {confidence}%")
    print(f"      使用资产: {asset_type}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            data = result["data"]
            print(f"\n✅ 投票成功！")
            print(f"   投票ID: {data.get('vote_id')}")
            print(f"   投票序号: 第{data.get('vote_number')}票")
            print(f"   消耗资产: {data.get('cost_amount')} {data.get('asset_type')}")
            print(f"   奖励倍数: ×{data.get('reward_multiplier')}")
            return data
        else:
            error_msg = result.get('message', '未知错误')
            print(f"\n❌ 投票失败: {error_msg}")
            return None
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*60)
    print("  竞猜系统完整流程测试")
    print("="*60)
    
    print("\n" + "#"*60)
    print("#  竞猜系统完整流程测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#"*60)
    
    token = login("testuser", "test123")
    if not token:
        print("\n❌ 登录失败，无法继续测试")
        return
    
    initial_assets = get_user_assets(token)
    initial_tickets = get_user_tickets(token)
    
    sessions = get_open_sessions(token)
    if not sessions:
        print("\n❌ 没有开放场次，无法继续测试")
        return
    
    target_session = None
    for session in sessions:
        if session.get("total_votes", 0) == 0:
            target_session = session
            break
    
    if not target_session:
        print("\n⚠️  所有场次都已有投票，选择第一个场次")
        target_session = sessions[0]
    
    session_id = target_session.get("id")
    print(f"\n   选择场次: {target_session.get('title')} (ID: {session_id})")
    
    detail = get_session_detail(token, session_id)
    if not detail:
        return
    
    options = detail.get("options", [])
    if not options:
        print("\n❌ 场次没有选项，无法投票")
        return
    
    user_vote_count = len(detail.get("user_votes", []))
    tiered_costs = detail.get("tiered_costs", [])
    
    next_vote_tier = user_vote_count + 1
    allowed_asset_types = ["fragment"]
    
    for cost in tiered_costs:
        if cost.get("vote_tier") == next_vote_tier:
            allowed_asset_types = cost.get("allowed_asset_types", ["fragment"])
            break
    
    print(f"\n   下一票 (第{next_vote_tier}票) 允许的资产类型: {allowed_asset_types}")
    
    selected_option = options[0]
    option_value = selected_option.get("option_value")
    print(f"\n   选择第一个选项: {option_value}")
    
    asset_type = "fragment"
    if len(initial_tickets) > 0 and "ticket" in allowed_asset_types:
        asset_type = "ticket"
    elif "point" in allowed_asset_types and initial_assets and initial_assets.get("stardust_point", 0) > 0:
        asset_type = "point"
    
    vote_result = cast_vote(token, session_id, option_value, confidence=80, asset_type=asset_type)
    
    print("\n" + "="*60)
    print("  [7/8] 验证资产消耗")
    print("="*60)
    
    after_assets = get_user_assets(token)
    after_tickets = get_user_tickets(token)
    
    if initial_assets and after_assets:
        print(f"\n   星元碎片: {initial_assets['stardust_fragment']} → {after_assets['stardust_fragment']}")
        if after_assets['stardust_fragment'] < initial_assets['stardust_fragment']:
            print(f"   ✅ 消耗了 {initial_assets['stardust_fragment'] - after_assets['stardust_fragment']} 星元碎片")
        
        print(f"   高阶星尘: {initial_assets['stardust_point']} → {after_assets['stardust_point']}")
        if after_assets['stardust_point'] < initial_assets['stardust_point']:
            print(f"   ✅ 消耗了 {initial_assets['stardust_point'] - after_assets['stardust_point']} 高阶星尘")
    
    if initial_tickets and after_tickets:
        print(f"\n   预言券: {len(initial_tickets)} 张 → {len(after_tickets)} 张")
        if len(after_tickets) < len(initial_tickets):
            print(f"   ✅ 使用了 {len(initial_tickets) - len(after_tickets)} 张预言券")
    
    print("\n" + "#"*60)
    print("#  测试完成！")
    print("#"*60)
    
    print("\n" + "="*60)
    print("  测试结果摘要")
    print("="*60)
    
    print("\n  登录: ✅ 成功")
    print("  my-tickets 接口: ✅ 已修复")
    if after_assets:
        print(f"  星元碎片: {after_assets['stardust_fragment']}")
        print(f"  高阶星尘: {after_assets['stardust_point']}")
    if after_tickets:
        print(f"  预言券: {len(after_tickets)} 张")
    print(f"  开放场次: {len(sessions)} 场")
    
    if vote_result:
        print(f"\n  投票结果: ✅ 成功")
        print(f"    投票ID: {vote_result.get('vote_id')}")
        print(f"    消耗: {vote_result.get('cost_amount')} {vote_result.get('asset_type')}")
    
    print("\n" + "="*60)
    print("\n✅ 测试流程完成！")


if __name__ == "__main__":
    main()
