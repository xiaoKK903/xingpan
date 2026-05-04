"""
前世故事 - AI故事生成服务
"""
import logging
from typing import Dict, Any, List, Optional

from app.services.ai_service import call_deepseek_api, call_qwen_api

from .config import (
    PAST_LIFE_THEME_CONFIG,
    PAST_LIFE_RELATIONSHIP_CONFIG
)
from .analysis_service import safe_get

logger = logging.getLogger(__name__)

MIN_SHORT_STORY_LENGTH = 50

PAST_LIFE_SYSTEM_PROMPT = """你是一位精通宿命轮回的古风仙侠故事讲述者。
你擅长将占星学符号转化为富有画面感的前世故事。
你的语言风格是古风仙侠，优美、诗意、富有想象力。
你善于创造深刻的人物和感人的情节。
请用中文回答。"""

SYNASTRY_SYSTEM_PROMPT = """你是一位精通宿命轮回的古风仙侠故事讲述者。
你擅长将两人的合盘相位转化为富有情感的前世关系故事。
你的语言风格是古风仙侠，优美、诗意、富有想象力。
你善于刻画人物关系和情感羁绊。
请用中文回答。"""


async def _call_ai_with_fallback(
    prompt: str, 
    max_tokens: int = 1000,
    system_prompt: str = None,
    temperature: float = 0.75,
    fast_mode: bool = True
) -> Dict[str, Any]:
    """
    统一处理 AI 调用与降级
    
    优先调用 DeepSeek API，失败则降级使用千问 API
    
    返回: {"success": bool, "content": str, "error": str}
    """
    try:
        actual_system_prompt = system_prompt or PAST_LIFE_SYSTEM_PROMPT
        
        try:
            logger.info(f"调用 DeepSeek API: max_tokens={max_tokens}, fast_mode={fast_mode}, temperature={temperature}")
            result = await call_deepseek_api(
                prompt=prompt,
                system_prompt=actual_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                fast_mode=fast_mode
            )
        except Exception as e:
            logger.warning(f"DeepSeek API调用失败，尝试使用千问API: {e}")
            try:
                result = await call_qwen_api(
                    prompt=prompt,
                    max_tokens=max_tokens
                )
            except Exception as e2:
                logger.error(f"所有AI API调用失败: {e2}")
                return {
                    "success": False,
                    "content": "",
                    "error": f"AI服务暂时不可用: {str(e2)}"
                }
        
        content = result.get("content", "") if isinstance(result, dict) else str(result)
        
        if not content or not content.strip():
            logger.warning("AI返回内容为空")
            return {
                "success": False,
                "content": "",
                "error": "AI生成失败：返回内容为空"
            }
        
        return {
            "success": True,
            "content": content,
            "error": ""
        }
        
    except Exception as e:
        logger.error(f"AI调用过程发生错误: {e}", exc_info=True)
        return {
            "success": False,
            "content": "",
            "error": str(e)
        }


def _extract_short_story(story: str, min_length: int = MIN_SHORT_STORY_LENGTH) -> str:
    """
    统一处理摘要逻辑
    
    规则：
    1. 优先按句号/感叹号/换行截断
    2. 如果截断后长度 < min_length，则取前 min_length 字符
    3. 确保摘要完整可读
    
    参数:
        story: 完整故事内容
        min_length: 最小长度限制，默认 50 字符
    
    返回: 摘要内容
    """
    if not story:
        return ""
    
    story = story.strip()
    if len(story) <= min_length:
        return story
    
    first_period = story.find("。")
    first_exclaim = story.find("！")
    first_break = story.find("\n")
    first_exclaim_en = story.find("!")
    first_period_en = story.find(".")
    
    break_points = [
        p for p in [
            first_period, first_exclaim, first_break, 
            first_exclaim_en, first_period_en
        ] if p > 0
    ]
    
    if break_points:
        short_end = min(break_points) + 1
        short_story = story[:short_end].strip()
        
        if len(short_story) >= min_length:
            return short_story
    
    if len(story) > min_length + 50:
        end_idx = min_length
        while end_idx < len(story) and story[end_idx] not in ["。", "！", "！", "!", ".", "，", ","]:
            end_idx += 1
        if end_idx < len(story) and story[end_idx] in ["。", "！", "！", "!"]:
            end_idx += 1
        return story[:end_idx].strip() + "..."
    
    return story[:min_length].strip() + "..."


def _filter_valid_planets(planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    过滤空值脏数据
    
    遍历行星时判断 planet_name 为空直接跳过，避免无效内容进入 Prompt
    """
    valid_planets = []
    for p in planets:
        planet_name = p.get("name", "") or p.get("planet_name", "")
        if planet_name and planet_name.strip():
            valid_planets.append(p)
    return valid_planets


def _extract_matched_aspects(synastry_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    修正合盘数据结构，从 matched_aspects 中正确读取数据
    
    正确读取路径: matched_aspects -> planet_a / planet_b / aspect_type
    """
    matched_aspects = safe_get(synastry_data, ["matched_aspects"], [])
    
    if not matched_aspects:
        highlights = safe_get(synastry_data, ["highlights"], [])
        if highlights:
            matched_aspects = highlights
    
    valid_aspects = []
    for aspect in matched_aspects:
        planet_a = safe_get(aspect, ["planet_a"], "")
        planet_b = safe_get(aspect, ["planet_b"], "")
        aspect_type = safe_get(aspect, ["aspect_type"], "")
        
        if planet_a and planet_b:
            valid_aspects.append({
                "planet_a": planet_a,
                "planet_b": planet_b,
                "aspect_type": aspect_type,
                "influence": safe_get(aspect, ["influence"], "")
            })
    
    return valid_aspects


def build_past_life_prompt(
    theme: str,
    planets: List[Dict[str, Any]],
    chart_data: Dict[str, Any],
    is_deep: bool = False,
    name: str = ""
) -> str:
    """
    构建前世故事的AI提示词
    
    风格: 古风仙侠
    """
    theme_config = PAST_LIFE_THEME_CONFIG.get(theme, PAST_LIFE_THEME_CONFIG["adventurer"])
    
    sun_sign = safe_get(chart_data, ["sun_sign", "sign"], "未知")
    moon_sign = safe_get(chart_data, ["moon_sign", "sign"], "未知")
    ascendant = safe_get(chart_data, ["ascendant", "sign"], "未知")
    
    valid_planets = _filter_valid_planets(planets)
    
    planet_descriptions = []
    for p in valid_planets:
        planet_name = p.get("name", "")
        if not planet_name:
            continue
            
        sign = p.get("sign", "未知")
        house = p.get("house", 0)
        element = p.get("element", "")
        
        house_desc = f"在第{house}宫" if house else ""
        element_desc = f"{element}特质" if element else ""
        
        desc = f"{planet_name}落在{sign}{house_desc}，{element_desc}"
        planet_descriptions.append(desc)
    
    planets_text = "；".join(planet_descriptions) if planet_descriptions else "核心行星配置"
    user_name = name or "求问者"
    
    if is_deep:
        return f"""你是一位精通前世今生的神秘占星师，擅长用古风仙侠的文笔讲述前世故事。

求问者：{user_name}
星盘核心信息：
- 太阳星座：{sun_sign}（代表核心身份与意志）
- 月亮星座：{moon_sign}（代表内在情感与需求）
- 上升星座：{ascendant}（代表外在表现与第一印象）
- 行星位置：{planets_text}

根据以上星盘，求问者的前世主题是：【{theme_config['name']}】{theme_config['icon']}
关键词：{', '.join(theme_config['keywords'])}
描述：{theme_config['description']}

请为{user_name}撰写一个完整、细腻的前世故事，要求：

1. **故事框架**（必须包含）：
   - 【身份缘起】：前世的身份、出生背景、时代背景
   - 【核心经历】：2-3个关键人生事件，体现星盘中行星的影响力
   - 【关键人物】：1-2个重要的人物关系（如恩师、挚爱、对手）
   - 【命运转折】：一个重要的命运转折点
   - 【临终遗愿】：前世未了的心愿或遗憾
   - 【今生启示】：这份前世经历对今生的影响和启示

2. **文风要求**：
   - 古风仙侠风格，文笔优美，富有画面感
   - 融入星盘元素，但不要生硬堆砌术语
   - 情感真挚，有感染力，让用户产生共鸣
   - 适当加入一些神秘、玄幻的元素

3. **长度要求**：
   - 总字数不少于1500字
   - 每个部分要有足够的细节描写

4. **输出格式**：
   请用以下格式输出：
   
   # 前世故事：{theme_config['name']}
   
   ## 身份缘起
   [详细描述前世的身份、出生背景、时代背景，不少于300字]
   
   ## 核心经历
   [详细描述2-3个关键人生事件，体现星盘中行星的影响力，不少于500字]
   
   ## 关键人物
   [详细描述1-2个重要的人物关系，不少于300字]
   
   ## 命运转折
   [详细描述一个重要的命运转折点，不少于200字]
   
   ## 临终遗愿
   [描述前世未了的心愿或遗憾，不少于150字]
   
   ## 今生启示
   [分析这份前世经历对今生的影响和启示，不少于200字]

注意：
1. 所有内容都要用中文撰写
2. 要基于提供的星盘信息进行合理想象
3. 故事要有起承转合，情感要有起伏
4. 避免现代用语，保持古风仙侠的语境"""
    
    else:
        return f"""你是一位精通前世今生的神秘占星师，擅长用简洁优美的古文讲述前世故事。

求问者：{user_name}
星盘核心信息：
- 太阳星座：{sun_sign}
- 月亮星座：{moon_sign}
- 上升星座：{ascendant}

根据以上星盘，求问者的前世主题是：【{theme_config['name']}】{theme_config['icon']}
关键词：{', '.join(theme_config['keywords'])}

请为{user_name}撰写一个精简的前世故事，要求：
1. 古风仙侠风格，文笔优美
2. 字数控制在200-300字
3. 包含核心身份、一个关键事件、一句今生启示
4. 直接输出故事内容，不需要标题

注意：直接输出故事内容，不要用markdown格式。"""


def build_synastry_past_life_prompt(
    relationship_type: str,
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    synastry_highlights: Dict[str, Any],
    is_deep: bool = False
) -> str:
    """
    构建合盘前世关系故事的AI提示词
    
    风格: 古风仙侠
    """
    rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(
        relationship_type, 
        PAST_LIFE_RELATIONSHIP_CONFIG["stranger"]
    )
    
    name_a = person_a.get("name", "人物A")
    name_b = person_b.get("name", "人物B")
    sun_sign_a = person_a.get("sun_sign", "未知")
    sun_sign_b = person_b.get("sun_sign", "未知")
    
    matched_aspects = _extract_matched_aspects(synastry_highlights)
    
    highlight_texts = []
    for aspect in matched_aspects[:5]:
        planet_a = aspect.get("planet_a", "")
        planet_b = aspect.get("planet_b", "")
        aspect_type = aspect.get("aspect_type", "")
        influence = aspect.get("influence", "")
        
        if planet_a and planet_b:
            if influence:
                highlight_texts.append(f"{planet_a}与{planet_b}呈{aspect_type}：{influence}")
            else:
                highlight_texts.append(f"{planet_a}与{planet_b}呈{aspect_type}")
    
    highlights_text = "；".join(highlight_texts) if highlight_texts else "两人星盘具有特殊缘分"
    
    if is_deep:
        return f"""你是一位精通前世姻缘的神秘占星师，擅长用古风仙侠的文笔讲述两人的前世羁绊。

人物信息：
- {name_a}：太阳{sun_sign_a}
- {name_b}：太阳{sun_sign_b}

合盘关键相位：
{highlights_text}

根据以上合盘，两人的前世关系是：【{rel_config['name']}】{rel_config['icon']}
关键词：{', '.join(rel_config['keywords'])}
描述：{rel_config['description']}

请为{name_a}和{name_b}撰写一个完整、细腻的前世羁绊故事，要求：

1. **故事框架**（必须包含）：
   - 【初遇缘起】：两人前世是如何相遇的，当时的情境是怎样的
   - 【羁绊发展】：两人关系如何发展，经历了哪些重要时刻
   - 【关键事件】：2-3个改变两人关系命运的关键事件
   - 【关系本质】：两人在前世扮演了彼此生命中的什么角色
   - 【因果轮回】：前世未了的因果如何影响今生
   - 【今生课题】：两人今生相遇需要完成什么课题

2. **文风要求**：
   - 古风仙侠风格，文笔优美，富有画面感
   - 融入合盘相位元素，但不要生硬堆砌术语
   - 情感真挚，有感染力，展现两人之间的深刻羁绊
   - 适当加入一些神秘、玄幻的元素

3. **长度要求**：
   - 总字数不少于1200字
   - 每个部分要有足够的细节描写

4. **输出格式**：
   请用以下格式输出：
   
   # 前世羁绊：{rel_config['name']}
   
   ## 初遇缘起
   [详细描述两人前世初遇的情境，不少于250字]
   
   ## 羁绊发展
   [详细描述两人关系如何发展，不少于300字]
   
   ## 关键事件
   [详细描述2-3个改变两人关系命运的关键事件，不少于350字]
   
   ## 关系本质
   [分析两人在前世扮演的角色和关系本质，不少于150字]
   
   ## 因果轮回
   [描述前世未了的因果，不少于100字]
   
   ## 今生课题
   [分析两人今生相遇需要完成的课题，不少于150字]

注意：
1. 所有内容都要用中文撰写
2. 要基于提供的合盘信息进行合理想象
3. 故事要有起承转合，情感要有起伏
4. 避免现代用语，保持古风仙侠的语境"""
    
    else:
        return f"""你是一位精通前世姻缘的神秘占星师，擅长用简洁优美的古文讲述两人的前世羁绊。

人物信息：
- {name_a}：太阳{sun_sign_a}
- {name_b}：太阳{sun_sign_b}

根据合盘分析，两人的前世关系是：【{rel_config['name']}】{rel_config['icon']}
关键词：{', '.join(rel_config['keywords'])}

请为{name_a}和{name_b}撰写一个精简的前世羁绊故事，要求：
1. 古风仙侠风格，文笔优美
2. 字数控制在200-300字
3. 包含初遇情境、核心羁绊、一句今生启示
4. 直接输出故事内容，不需要标题

注意：直接输出故事内容，不要用markdown格式。"""


async def generate_past_life_story(
    theme: str,
    planets: List[Dict[str, Any]],
    chart_data: Dict[str, Any],
    is_deep: bool = False,
    name: str = ""
) -> Dict[str, Any]:
    """
    调用AI生成前世故事
    
    返回: {"success": bool, "story": str, "short_story": str, "error": str}
    """
    try:
        prompt = build_past_life_prompt(theme, planets, chart_data, is_deep, name)
        logger.info(f"生成{'深度版' if is_deep else '基础版'}前世故事，主题: {theme}")
        
        max_tokens = 2000 if is_deep else 1000
        temperature = 0.85 if is_deep else 0.75
        fast_mode = not is_deep
        
        result = await _call_ai_with_fallback(
            prompt=prompt,
            max_tokens=max_tokens,
            system_prompt=PAST_LIFE_SYSTEM_PROMPT,
            temperature=temperature,
            fast_mode=fast_mode
        )
        
        if not result["success"]:
            return {
                "success": False,
                "story": "",
                "short_story": "",
                "error": result["error"]
            }
        
        story = result["content"]
        short_story = _extract_short_story(story)
        
        return {
            "success": True,
            "story": story,
            "short_story": short_story
        }
        
    except Exception as e:
        logger.error(f"生成前世故事失败: {e}", exc_info=True)
        return {
            "success": False,
            "story": "",
            "short_story": "",
            "error": str(e)
        }


async def generate_synastry_past_life_story(
    relationship_type: str,
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    synastry_highlights: Dict[str, Any],
    is_deep: bool = False
) -> Dict[str, Any]:
    """
    调用AI生成合盘前世关系故事
    
    返回: {"success": bool, "story": str, "short_story": str, "error": str}
    """
    try:
        prompt = build_synastry_past_life_prompt(
            relationship_type, person_a, person_b, synastry_highlights, is_deep
        )
        logger.info(f"生成{'深度版' if is_deep else '基础版'}合盘前世故事，关系类型: {relationship_type}")
        
        max_tokens = 2000 if is_deep else 1000
        temperature = 0.85 if is_deep else 0.75
        fast_mode = not is_deep
        
        result = await _call_ai_with_fallback(
            prompt=prompt,
            max_tokens=max_tokens,
            system_prompt=SYNASTRY_SYSTEM_PROMPT,
            temperature=temperature,
            fast_mode=fast_mode
        )
        
        if not result["success"]:
            return {
                "success": False,
                "story": "",
                "short_story": "",
                "error": result["error"]
            }
        
        story = result["content"]
        short_story = _extract_short_story(story)
        
        return {
            "success": True,
            "story": story,
            "short_story": short_story
        }
        
    except Exception as e:
        logger.error(f"生成合盘前世故事失败: {e}", exc_info=True)
        return {
            "success": False,
            "story": "",
            "short_story": "",
            "error": str(e)
        }
