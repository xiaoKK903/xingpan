import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

DEEPSEEK_FLASH_MODEL = "deepseek-v4-flash"
DEEPSEEK_PRO_MODEL = "deepseek-v4-pro"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


async def test_deepseek_api_simple():
    """简单测试 DeepSeek API 调用"""
    
    if not settings.DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY 未配置")
        return False
    
    print(f"✅ API Key 已配置，长度: {len(settings.DEEPSEEK_API_KEY)}")
    print(f"✅ API Key 前缀: {settings.DEEPSEEK_API_KEY[:20]}...")
    
    api_url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_payloads = [
        {
            "name": "deepseek-v4-flash (非思考模式)",
            "payload": {
                "model": DEEPSEEK_FLASH_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个友好的助手，请用中文回复。"},
                    {"role": "user", "content": "你好，请简单介绍一下你自己。"}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False
            }
        },
        {
            "name": "deepseek-v4-flash (思考模式)",
            "payload": {
                "model": DEEPSEEK_FLASH_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个友好的助手，请用中文回复。"},
                    {"role": "user", "content": "1+1等于几？请详细说明。"}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False,
                "thinking": {"type": "enabled"},
                "reasoning_effort": "high"
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for test_case in test_payloads:
            print(f"\n{'='*60}")
            print(f"测试: {test_case['name']}")
            print(f"{'='*60}")
            
            payload = test_case['payload']
            print(f"请求模型: {payload['model']}")
            print(f"thinking参数: {payload.get('thinking', '未设置')}")
            print(f"reasoning_effort: {payload.get('reasoning_effort', '未设置')}")
            
            try:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=120.0
                )
                
                print(f"\n响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ API 调用成功!")
                    
                    try:
                        content = result["choices"][0]["message"]["content"]
                        print(f"\n回复内容:")
                        print(content[:500] if len(content) > 500 else content)
                        
                        reasoning_content = result["choices"][0].get("message", {}).get("reasoning_content", "")
                        if reasoning_content:
                            print(f"\n推理过程:")
                            print(reasoning_content[:500] if len(reasoning_content) > 500 else reasoning_content)
                        
                        print(f"\n✅ {test_case['name']} 测试通过!")
                        
                    except (KeyError, IndexError) as e:
                        print(f"❌ 解析响应失败: {e}")
                        print(f"完整响应: {json.dumps(result, ensure_ascii=False, default=str)[:1000]}")
                else:
                    error_body = response.text
                    print(f"❌ API 调用失败: HTTP {response.status_code}")
                    print(f"错误响应: {error_body[:2000] if len(error_body) > 2000 else error_body}")
                    
                    try:
                        error_json = response.json()
                        error_message = error_json.get("error", {}).get("message", "")
                        if error_message:
                            print(f"错误信息: {error_message}")
                    except:
                        pass
                        
            except httpx.TimeoutException:
                print(f"❌ 请求超时 (120秒)")
            except httpx.ConnectError as e:
                print(f"❌ 网络连接错误: {e}")
            except Exception as e:
                print(f"❌ 未知错误: {e}")
                import traceback
                traceback.print_exc()


async def test_deepseek_api_via_service():
    """通过 ai_service 模块测试"""
    
    print(f"\n{'='*60}")
    print(f"测试: 通过 ai_service 调用 (call_deepseek_api)")
    print(f"{'='*60}")
    
    try:
        from app.services.ai_service import call_deepseek_api
        
        print(f"测试 fast_mode=True (使用 deepseek-v4-flash)...")
        
        response = await call_deepseek_api(
            prompt="你好，请用中文简单介绍一下你自己。",
            system_prompt="你是一个友好的助手，请用中文回复。",
            temperature=0.7,
            max_tokens=500,
            fast_mode=True
        )
        
        print(f"✅ 调用成功!")
        print(f"\n回复内容:")
        print(response[:500] if len(response) > 500 else response)
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("="*60)
    print("DeepSeek API 测试脚本")
    print("="*60)
    print(f"当前时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    print()
    
    print("步骤 1: 测试直接 API 调用...")
    await test_deepseek_api_simple()
    
    print("\n\n步骤 2: 测试通过 ai_service 调用...")
    await test_deepseek_api_via_service()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
