"""
竞猜系统 API 测试脚本
测试完整的业务闭环流程
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"


def pretty_print(title, data):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if isinstance(data, dict):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data)


def test_login(username, password):
    """登录获取 token"""
    url = f"{BASE_URL}/users/login"
    data = {"username": username, "password": password}
    files = {"username": (None, username), "password": (None, password)}
    
    try:
        response = requests.post(url, files=files, timeout=10)
        result = response.json()
        pretty_print(f"登录 ({username})", result)
        
        if result.get("code") == 200 and "data" in result:
            return result["data"].get("access_token") or result["data"].get("token")
        return None
    except Exception as e:
        print(f"登录失败: {e}")
        return None


def test_get_themes(token=None):
    """获取固定主题列表"""
    url = f"{BASE_URL}/prediction/themes"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print("获取固定主题列表", result)
        return result
    except Exception as e:
        print(f"获取主题失败: {e}")
        return None


def test_get_open_predictions(token=None):
    """获取开放投票的场次"""
    url = f"{BASE_URL}/prediction/open"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print("获取开放投票场次", result)
        return result
    except Exception as e:
        print(f"获取开放场次失败: {e}")
        return None


def test_get_upcoming_predictions(token=None):
    """获取即将开始的场次"""
    url = f"{BASE_URL}/prediction/upcoming"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print("获取即将开始场次", result)
        return result
    except Exception as e:
        print(f"获取即将开始场次失败: {e}")
        return None


def test_get_prediction_detail(prediction_id, token=None):
    """获取场次详情"""
    url = f"{BASE_URL}/prediction/detail-optimized/{prediction_id}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print(f"获取场次详情 (ID: {prediction_id})", result)
        return result
    except Exception as e:
        print(f"获取场次详情失败: {e}")
        return None


def test_get_tiered_costs(prediction_id, token=None):
    """获取阶梯式付费规则"""
    url = f"{BASE_URL}/prediction/tiered-costs/{prediction_id}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print(f"获取阶梯式付费规则 (ID: {prediction_id})", result)
        return result
    except Exception as e:
        print(f"获取阶梯式规则失败: {e}")
        return None


def test_cast_vote_secure(token, prediction_id, selected_option, confidence=50, use_asset="fragment"):
    """安全投票"""
    url = f"{BASE_URL}/prediction/vote-secure"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "prediction_id": prediction_id,
        "selected_option": selected_option,
        "confidence": confidence,
        "use_asset": use_asset
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        pretty_print(f"投票 (场次: {prediction_id}, 选项: {selected_option})", result)
        return result
    except Exception as e:
        print(f"投票失败: {e}")
        return None


def test_claim_reward(token, vote_id):
    """领取奖励"""
    url = f"{BASE_URL}/prediction/claim-reward?vote_id={vote_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print(f"领取奖励 (投票ID: {vote_id})", result)
        return result
    except Exception as e:
        print(f"领取奖励失败: {e}")
        return None


def test_get_my_history(token, limit=20):
    """获取我的预测历史"""
    url = f"{BASE_URL}/prediction/my-history?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print(f"获取我的预测历史", result)
        return result
    except Exception as e:
        print(f"获取历史记录失败: {e}")
        return None


def test_get_current_user(token):
    """获取当前用户信息"""
    url = f"{BASE_URL}/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print("获取当前用户信息", result)
        return result
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None


def test_check_rate_limit(token, action_type="vote"):
    """检查限流状态"""
    url = f"{BASE_URL}/prediction/check-rate-limit?action_type={action_type}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        pretty_print("检查限流状态", result)
        return result
    except Exception as e:
        print(f"检查限流失败: {e}")
        return None


def run_full_test():
    """运行完整的测试流程"""
    print("\n" + "="*60)
    print("  竞猜系统 API 完整测试流程")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    token = None
    prediction_id = None
    vote_id = None
    
    print("\n[1/8] 测试基础接口（无需登录）")
    print("-"*60)
    
    test_get_themes()
    
    open_result = test_get_open_predictions()
    if open_result and open_result.get("code") == 200:
        predictions = open_result.get("data", {}).get("predictions", [])
        if predictions:
            prediction_id = predictions[0].get("id")
            print(f"\n找到开放场次 ID: {prediction_id}")
    
    test_get_upcoming_predictions()
    
    if prediction_id:
        test_get_prediction_detail(prediction_id)
        test_get_tiered_costs(prediction_id)
    
    print("\n[2/8] 登录测试用户")
    print("-"*60)
    
    token = test_login("testuser", "test123")
    
    if not token:
        print("\n⚠️  测试用户登录失败，尝试注册...")
        register_url = f"{BASE_URL}/users/register"
        register_data = {
            "username": "testuser",
            "password": "test123",
            "email": "testuser@example.com"
        }
        try:
            response = requests.post(register_url, json=register_data, timeout=10)
            result = response.json()
            pretty_print("注册测试用户", result)
            if result.get("code") == 200:
                token = test_login("testuser", "test123")
        except Exception as e:
            print(f"注册失败: {e}")
    
    if not token:
        print("\n❌ 无法获取有效 token，测试终止")
        return
    
    print(f"\n✅ 登录成功，Token: {token[:30]}...")
    
    print("\n[3/8] 测试用户信息接口")
    print("-"*60)
    
    user_info = test_get_current_user(token)
    
    print("\n[4/8] 测试限流检查")
    print("-"*60)
    
    test_check_rate_limit(token)
    
    print("\n[5/8] 重新获取场次信息（登录后）")
    print("-"*60)
    
    open_result = test_get_open_predictions(token)
    if open_result and open_result.get("code") == 200:
        predictions = open_result.get("data", {}).get("predictions", [])
        if predictions:
            prediction_id = predictions[0].get("id")
            print(f"\n找到开放场次 ID: {prediction_id}")
    
    if prediction_id:
        detail_result = test_get_prediction_detail(prediction_id, token)
        
        test_get_tiered_costs(prediction_id, token)
        
        print("\n[6/8] 测试投票功能")
        print("-"*60)
        
        options = ["fire", "earth", "air", "water"]
        if detail_result and detail_result.get("code") == 200:
            options_data = detail_result.get("data", {}).get("options_parsed", {})
            if options_data and "values" in options_data:
                options = options_data["values"]
        
        selected_option = options[0] if options else "fire"
        
        vote_result = test_cast_vote_secure(token, prediction_id, selected_option, 80, "fragment")
        
        if vote_result and vote_result.get("code") == 200:
            vote_data = vote_result.get("data", {})
            vote_id = vote_data.get("vote_id")
            print(f"\n✅ 投票成功，投票ID: {vote_id}")
            
            print("\n[7/8] 测试获取预测历史")
            print("-"*60)
            test_get_my_history(token)
            
            print("\n[8/8] 重新获取场次详情（查看投票记录）")
            print("-"*60)
            test_get_prediction_detail(prediction_id, token)
    
    print("\n" + "="*60)
    print("  测试流程完成！")
    print("="*60)
    print("\n📊 测试结果汇总:")
    print(f"  - 用户登录: {'✅ 成功' if token else '❌ 失败'}")
    print(f"  - 开放场次查询: {'✅ 成功' if open_result else '❌ 失败'}")
    print(f"  - 场次详情查询: {'✅ 成功' if prediction_id else '❌ 未找到'}")
    print(f"  - 投票功能: {'✅ 成功' if vote_id else '❌ 失败/未执行'}")
    print(f"  - 历史记录查询: {'✅ 已执行' if token else '❌ 未执行'}")
    
    print("\n💡 提示:")
    print("  - 要测试奖励领取功能，需要先人工结算场次")
    print("  - 结算后调用 /prediction/claim-reward 接口领取奖励")
    print("  - 管理员可调用 /prediction/admin/resolve-manual 进行人工结算")


if __name__ == "__main__":
    run_full_test()
