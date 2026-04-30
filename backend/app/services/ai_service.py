import httpx
import json
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

DASHSCOPE_OPENAI_COMPATIBLE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEEPSEEK_OPENAI_COMPATIBLE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "qwen3.6-plus"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
FAST_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_QWEN_FAST_MODEL = "qwen-plus"

SYSTEM_PROMPT = """你是一位专业的占星师，拥有深厚的占星学知识和丰富的解读经验。请根据用户提供的星盘配置，用中文进行专业、深入且易于理解的解读。

解读要求：
1. 分析要专业但不晦涩，使用通俗易懂的语言
2. 结合行星、星座、宫位和相位进行综合分析
3. 解读要分模块：性格特质、事业发展、感情婚姻、运势趋势
4. 每个模块下要有具体的分析点，段落清晰
5. 语气要积极、建设性，避免负面断言
6. 解读要具体，避免空泛的描述

星盘配置解析：
- 行星：太阳(自我、意志)、月亮(情感、内心)、水星(思维、沟通)、金星(爱情、审美)、火星(行动、欲望)、木星(幸运、扩张)、土星(责任、限制)、天王星(变革、突破)、海王星(梦想、灵性)、冥王星(转化、重生)
- 星座：白羊座、金牛座、双子座、巨蟹座、狮子座、处女座、天秤座、天蝎座、射手座、摩羯座、水瓶座、双鱼座
- 宫位：第1宫(自我)、第2宫(财富)、第3宫(沟通)、第4宫(家庭)、第5宫(创造)、第6宫(健康)、第7宫(伴侣)、第8宫(资源)、第9宫(探索)、第10宫(事业)、第11宫(社交)、第12宫(潜意识)
- 相位：合相(0°)、六分相(60°)、四分相(90°)、三分相(120°)、对分相(180°)

请按照以下格式输出解读内容：

## 一、性格特质分析
[分析内容，包含太阳、月亮、上升等关键配置的解读]

## 二、事业发展分析
[分析内容，包含第10宫、第6宫、行星与事业相关的配置解读]

## 三、感情婚姻分析
[分析内容，包含第7宫、第5宫、金星、月亮等相关配置解读]

## 四、运势趋势分析
[分析内容，结合当前行运和本命盘的整体能量趋势]

请确保内容丰富、专业，每个部分至少包含2-3个具体的分析点。"""


def get_api_key_status() -> Dict[str, Any]:
    """检查API key状态，用于调试"""
    if not settings.DASHSCOPE_API_KEY:
        return {
            "configured": False,
            "key_length": 0,
            "key_prefix": None,
            "message": "DASHSCOPE_API_KEY 未配置"
        }
    
    key = settings.DASHSCOPE_API_KEY
    return {
        "configured": True,
        "key_length": len(key),
        "key_prefix": key[:10] + "..." if len(key) > 10 else key,
        "message": "API key 已配置"
    }


async def call_qwen_api(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 4000
) -> str:
    """
    调用阿里云千问大模型API（OpenAI兼容模式）
    
    Args:
        prompt: 用户提示词
        model: 模型名称（默认 qwen3.6-plus）
        temperature: 温度参数
        max_tokens: 最大token数
    
    Returns:
        模型生成的文本内容
    """
    api_status = get_api_key_status()
    logger.info(f"API key 状态: {api_status}")
    
    if not settings.DASHSCOPE_API_KEY:
        error_msg = "API key 未配置。请在 backend/.env 文件中设置 DASHSCOPE_API_KEY"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    use_model = model or DEFAULT_MODEL
    logger.info(f"使用模型: {use_model}")
    
    payload = {
        "model": use_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    logger.info(f"开始调用千问API（OpenAI兼容模式）")
    logger.info(f"请求URL: {DASHSCOPE_OPENAI_COMPATIBLE_URL}")
    logger.info(f"请求负载: model={use_model}, messages={len(payload['messages'])}条")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                DASHSCOPE_OPENAI_COMPATIBLE_URL,
                headers=headers,
                json=payload
            )
            
            logger.info(f"API响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"API调用失败: {response.status_code}")
                logger.error(f"错误响应: {error_body[:1000] if len(error_body) > 1000 else error_body}")
                
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", "") or error_json.get("message", "") or error_body
                    
                    if response.status_code == 401:
                        raise Exception(f"API认证失败: 请检查API key是否正确。错误信息: {error_message}")
                    elif response.status_code == 403:
                        raise Exception(f"API访问被拒绝: 可能是账户余额不足或权限问题。错误信息: {error_message}")
                    elif response.status_code == 429:
                        raise Exception(f"API调用频率超限: 请稍后再试。错误信息: {error_message}")
                    elif response.status_code == 500:
                        raise Exception(f"API服务器内部错误: 请稍后再试。错误信息: {error_message}")
                    else:
                        raise Exception(f"API调用失败 (HTTP {response.status_code}): {error_message}")
                        
                except json.JSONDecodeError:
                    raise Exception(f"API调用失败 (HTTP {response.status_code}): {error_body}")
            
            result = response.json()
            logger.info("API响应解析成功")
            logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False, default=str)[:2000]}")
            
            try:
                content = result["choices"][0]["message"]["content"]
                logger.info(f"成功获取AI回复，长度: {len(content)} 字符")
                return content
            except (KeyError, IndexError) as e:
                logger.error(f"解析API响应失败: {str(e)}")
                logger.error(f"响应结构: {json.dumps(result, ensure_ascii=False, default=str)}")
                raise Exception(f"解析API响应失败: 响应格式不符合预期。请检查API文档。")
                
    except httpx.ConnectError as e:
        logger.error(f"网络连接错误: {str(e)}")
        raise Exception(f"网络连接失败: 无法连接到阿里云API服务器。请检查网络连接。")
    except httpx.TimeoutException:
        logger.error("API请求超时")
        raise Exception(f"API请求超时: 服务器响应时间过长。请稍后重试。")
    except Exception as e:
        logger.error(f"API调用异常: {str(e)}")
        raise


def build_chart_prompt(chart_data: Dict[str, Any], name: str = "用户") -> str:
    """
    根据星盘数据构建提示词
    
    Args:
        chart_data: 星盘计算结果
        name: 姓名
    
    Returns:
        构建好的提示词
    """
    planets = chart_data.get("planets", [])
    houses = chart_data.get("houses", {})
    aspects = chart_data.get("aspects", [])
    ascendant = chart_data.get("ascendant", {})
    
    prompt_parts = [
        f"请为{name}的星盘进行专业解读。以下是星盘配置信息：\n",
    ]
    
    if ascendant:
        sign = ascendant.get("sign", "未知")
        degree = ascendant.get("dms", {}).get("formatted", "")
        prompt_parts.append(f"【上升点】{sign} {degree}")
    
    prompt_parts.append("\n【行星位置】")
    main_planets = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    for planet in planets:
        name_cn = planet.get("name", "")
        if name_cn not in main_planets:
            continue
        zodiac = planet.get("zodiac", {})
        sign = zodiac.get("sign", "未知")
        degree = zodiac.get("dms", {}).get("formatted", "")
        house = planet.get("house", "未知")
        retrograde = planet.get("is_retrograde", False)
        retro_str = " (逆行)" if retrograde else ""
        prompt_parts.append(f"- {name_cn}：{sign} {degree}，第{house}宫{retro_str}")
    
    prompt_parts.append("\n【主要相位】")
    if aspects:
        for aspect in aspects[:15]:
            p1 = aspect.get("planet1", "")
            p2 = aspect.get("planet2", "")
            aspect_type = aspect.get("aspect", "")
            orb = aspect.get("orb", 0)
            prompt_parts.append(f"- {p1} {aspect_type} {p2} (容许度 {orb}°)")
    else:
        prompt_parts.append("无主要相位")
    
    prompt_parts.append("\n\n请根据以上星盘配置，按照指定的格式进行详细解读：")
    prompt_parts.append("1. 性格特质分析")
    prompt_parts.append("2. 事业发展分析")
    prompt_parts.append("3. 感情婚姻分析")
    prompt_parts.append("4. 运势趋势分析")
    
    return "\n".join(prompt_parts)


async def generate_ai_interpretation(
    chart_data: Dict[str, Any],
    name: str = "用户"
) -> Dict[str, Any]:
    """
    生成AI星盘解读
    
    Args:
        chart_data: 星盘数据
        name: 姓名
    
    Returns:
        包含解读内容的字典
    """
    logger.info(f"开始生成AI星盘解读，用户: {name}")
    
    if not chart_data:
        error_msg = "星盘数据为空"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_type": "invalid_input",
            "content": None,
            "sections": None
        }
    
    planets = chart_data.get("planets", [])
    if not planets:
        error_msg = "星盘数据不完整：缺少行星信息"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "error_type": "invalid_input",
            "content": None,
            "sections": None
        }
    
    try:
        prompt = build_chart_prompt(chart_data, name)
        logger.info(f"提示词构建完成，长度: {len(prompt)} 字符")
        
        content = await call_qwen_api(
            prompt=prompt,
            model=DEFAULT_MODEL,
            temperature=0.7,
            max_tokens=4000
        )
        
        if not content or not content.strip():
            error_msg = "AI返回内容为空"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "empty_response",
                "content": None,
                "sections": None
            }
        
        sections = parse_interpretation_sections(content)
        logger.info(f"解读解析完成，共 {len(sections)} 个板块")
        
        return {
            "success": True,
            "content": content,
            "sections": sections
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"配置错误: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "error_type": "configuration_error",
            "content": None,
            "sections": None
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"生成AI解读失败: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "error_type": "api_error",
            "content": None,
            "sections": None
        }


def parse_interpretation_sections(content: str) -> Dict[str, str]:
    """
    解析解读内容，按模块分段
    
    Args:
        content: 原始解读内容
    
    Returns:
        按模块分类的字典
    """
    sections = {}
    
    section_patterns = [
        ("personality", ["一、性格特质分析", "性格特质", "性格分析", "## 一", "1. 性格特质分析"]),
        ("career", ["二、事业发展分析", "事业发展", "事业分析", "## 二", "2. 事业发展分析"]),
        ("love", ["三、感情婚姻分析", "感情婚姻", "感情分析", "## 三", "3. 感情婚姻分析"]),
        ("fortune", ["四、运势趋势分析", "运势趋势", "运势分析", "## 四", "4. 运势趋势分析"]),
    ]
    
    lines = content.split("\n")
    current_section = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        found_new_section = False
        for section_key, patterns in section_patterns:
            for pattern in patterns:
                if line_stripped.startswith(pattern):
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content).strip()
                    current_section = section_key
                    current_content = []
                    found_new_section = True
                    break
            if found_new_section:
                break
        
        if not found_new_section and current_section:
            if line_stripped:
                current_content.append(line)
    
    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()
    
    if not sections and content:
        sections["raw"] = content
    
    return sections


def get_deepseek_api_key_status() -> Dict[str, Any]:
    """检查DeepSeek API key状态"""
    if not settings.DEEPSEEK_API_KEY:
        return {
            "configured": False,
            "key_length": 0,
            "key_prefix": None,
            "message": "DEEPSEEK_API_KEY 未配置"
        }
    
    key = settings.DEEPSEEK_API_KEY
    return {
        "configured": True,
        "key_length": len(key),
        "key_prefix": key[:15] + "..." if len(key) > 15 else key,
        "message": "DeepSeek API key 已配置"
    }


async def call_deepseek_api(
    prompt: str,
    system_prompt: str = "你是一位专业的故事讲述者和占星师，请用中文为用户提供人生剧本风格的解读。",
    model: str = None,
    temperature: float = 0.85,
    max_tokens: int = 4000,
    reasoning_effort: str = "high",
    fast_mode: bool = False
) -> str:
    """
    调用 DeepSeek API（OpenAI 兼容模式）
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        model: 模型名称（默认使用配置中的 DEEPSEEK_MODEL）
        temperature: 温度参数
        max_tokens: 最大token数
        reasoning_effort: 推理努力程度（high/medium/low）
        fast_mode: 快速模式 - 使用更快的模型，禁用 thinking，减少超时时间
    
    Returns:
        模型生成的文本内容
    """
    api_status = get_deepseek_api_key_status()
    logger.info(f"DeepSeek API key 状态: {api_status}")
    
    if not settings.DEEPSEEK_API_KEY:
        error_msg = "DeepSeek API key 未配置。请在 backend/.env 文件中设置 DEEPSEEK_API_KEY"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    base_url = settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com"
    api_url = f"{base_url}/chat/completions"
    
    if fast_mode:
        use_model = FAST_DEEPSEEK_MODEL
        timeout = 120.0
        use_reasoning = False
        logger.info(f"快速模式启用，使用模型: {use_model}，超时: {timeout}秒")
    else:
        use_model = model or settings.DEEPSEEK_MODEL or DEFAULT_DEEPSEEK_MODEL
        timeout = 300.0
        use_reasoning = True
        logger.info(f"使用 DeepSeek 模型: {use_model}，超时: {timeout}秒")
    
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": use_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    
    if use_reasoning and reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
        payload["extra_body"] = {
            "thinking": {
                "type": "enabled"
            }
        }
    
    logger.info(f"开始调用 DeepSeek API")
    logger.info(f"请求URL: {api_url}")
    logger.info(f"请求负载: model={use_model}, 提示词长度={len(prompt)}字符, max_tokens={max_tokens}")
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload
            )
            
            logger.info(f"DeepSeek API 响应状态码: {response.status_code}")
            
            if response.status_code != 200:
                error_body = response.text
                logger.error(f"DeepSeek API 调用失败: {response.status_code}")
                logger.error(f"错误响应: {error_body[:2000] if len(error_body) > 2000 else error_body}")
                
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", "") or error_json.get("message", "") or error_body
                    
                    if response.status_code == 401:
                        raise Exception(f"DeepSeek API 认证失败: 请检查 API key 是否正确。错误信息: {error_message}")
                    elif response.status_code == 403:
                        raise Exception(f"DeepSeek API 访问被拒绝: 可能是账户余额不足或权限问题。错误信息: {error_message}")
                    elif response.status_code == 429:
                        raise Exception(f"DeepSeek API 调用频率超限: 请稍后再试。错误信息: {error_message}")
                    elif response.status_code == 500:
                        raise Exception(f"DeepSeek API 服务器内部错误: 请稍后再试。错误信息: {error_message}")
                    else:
                        raise Exception(f"DeepSeek API 调用失败 (HTTP {response.status_code}): {error_message}")
                        
                except json.JSONDecodeError:
                    raise Exception(f"DeepSeek API 调用失败 (HTTP {response.status_code}): {error_body}")
            
            result = response.json()
            logger.info("DeepSeek API 响应解析成功")
            
            try:
                content = result["choices"][0]["message"]["content"]
                logger.info(f"成功获取 DeepSeek AI 回复，长度: {len(content)} 字符")
                
                thinking_content = result["choices"][0].get("message", {}).get("reasoning_content", "")
                if thinking_content:
                    logger.debug(f"DeepSeek 推理过程: {thinking_content[:500]}...")
                
                return content
            except (KeyError, IndexError) as e:
                logger.error(f"解析 DeepSeek API 响应失败: {str(e)}")
                logger.error(f"响应结构: {json.dumps(result, ensure_ascii=False, default=str)}")
                raise Exception(f"解析 DeepSeek API 响应失败: 响应格式不符合预期。")
                
    except httpx.ConnectError as e:
        logger.error(f"DeepSeek API 网络连接错误: {str(e)}")
        raise Exception(f"网络连接失败: 无法连接到 DeepSeek API 服务器。请检查网络连接。")
    except httpx.TimeoutException:
        logger.error("DeepSeek API 请求超时")
        if fast_mode:
            raise Exception(f"API 请求超时: DeepSeek 快速模式仍超时。请检查网络或稍后重试。")
        else:
            raise Exception(f"API 请求超时: DeepSeek 服务器响应时间过长。可以尝试使用快速模式。")
    except Exception as e:
        logger.error(f"DeepSeek API 调用异常: {str(e)}")
        raise
