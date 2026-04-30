from typing import Dict, List, Any, Optional
import logging
import json
import asyncio

from app.services.profile_extractor_service import extract_tag_matrix
from app.services.conflict_resolution_service import generate_conflict_aware_personality
from app.services.ai_service import call_qwen_api

logger = logging.getLogger(__name__)


SOUL_KEYWORDS_TEMPLATES = {
    "白羊座": ["勇敢先锋", "无畏战士", "热情之火", "行动派"],
    "金牛座": ["稳健磐石", "感官艺术家", "质感追求者", "务实梦想家"],
    "双子座": ["思维精灵", "信息收集者", "社交蝴蝶", "好奇宝宝"],
    "巨蟹座": ["温暖港湾", "情感守护者", "记忆收藏家", "家族纽带"],
    "狮子座": ["光芒中心", "王者之风", "创意源头", "慷慨之心"],
    "处女座": ["完美工匠", "细节大师", "服务精神", "分析高手"],
    "天秤座": ["和谐使者", "优雅外交家", "审美裁判", "平衡艺术家"],
    "天蝎座": ["深渊探索者", "灵魂猎手", "转化大师", "神秘力量"],
    "射手座": ["自由灵魂", "真理追寻者", "乐观探险家", "哲学旅人"],
    "摩羯座": ["攀登者", "时间建筑师", "责任担当", "隐忍智者"],
    "水瓶座": ["未来使者", "独立先锋", "人道主义者", "创新思想家"],
    "双鱼座": ["梦幻诗人", "灵性使者", "共情艺术家", "边界消融者"],
}

AVOID_TOPICS_BY_SIGN = {
    "白羊座": ["被质疑能力", "等待太久", "被指挥"],
    "金牛座": ["突然改变", "品质低劣", "被催促"],
    "双子座": ["无聊话题", "重复内容", "被限制"],
    "巨蟹座": ["家庭矛盾", "被忽略", "旧事重提"],
    "狮子座": ["被忽视", "当众批评", "没面子"],
    "处女座": ["混乱无序", "马马虎虎", "被挑剔"],
    "天秤座": ["冲突争吵", "做决定", "不公平"],
    "天蝎座": ["被看穿", "不信任", "浅尝辄止"],
    "射手座": ["被束缚", "悲观消极", "循规蹈矩"],
    "摩羯座": ["不负责任", "浪费时间", "空想空谈"],
    "水瓶座": ["墨守成规", "从众压力", "被定义"],
    "双鱼座": ["残酷现实", "被指责", "无梦想"],
}

RECOMMENDED_TOPICS_BY_SIGN = {
    "白羊座": ["最新挑战", "运动竞技", "创业想法", "冒险经历"],
    "金牛座": ["美食体验", "艺术鉴赏", "投资理财", "品质生活"],
    "双子座": ["新奇事物", "热门话题", "旅行见闻", "有趣八卦"],
    "巨蟹座": ["家庭故事", "美食烹饪", "怀旧话题", "情感分享"],
    "狮子座": ["成就展示", "创意项目", "娱乐八卦", "赞美话题"],
    "处女座": ["效率提升", "健康养生", "技能学习", "细节讨论"],
    "天秤座": ["艺术文化", "时尚潮流", "人际关系", "和谐话题"],
    "天蝎座": ["深度话题", "心理学", "神秘现象", "灵魂对话"],
    "射手座": ["旅行计划", "哲学思考", "海外文化", "乐观故事"],
    "摩羯座": ["职业规划", "长期目标", "责任话题", "成就分享"],
    "水瓶座": ["科技创新", "社会议题", "未来趋势", "独特见解"],
    "双鱼座": ["艺术创作", "灵性话题", "梦境解析", "浪漫故事"],
}

ELEMENT_STYLES = {
    "火": {"style": "热情直接", "avoid": "冷处理"},
    "土": {"style": "务实稳重", "avoid": "空谈"},
    "风": {"style": "轻松幽默", "avoid": "沉闷"},
    "水": {"style": "温柔共情", "avoid": "冷漠"},
}


def generate_soul_keywords(
    big_three: Dict[str, Any],
    stelliums: List[Dict[str, Any]],
    resolved_tags: List[Dict[str, Any]],
    dominant_element: str,
    dominant_quality: str
) -> List[Dict[str, Any]]:
    """
    生成灵魂关键词
    """
    keywords = []
    used_sources = set()
    
    sun_sign = big_three.get("sun", {}).get("sign", "")
    if sun_sign and sun_sign in SOUL_KEYWORDS_TEMPLATES:
        template_keywords = SOUL_KEYWORDS_TEMPLATES[sun_sign]
        if template_keywords:
            keywords.append({
                "word": template_keywords[0],
                "source": f"太阳{sun_sign}",
                "type": "核心特质",
                "weight": 10,
            })
            used_sources.add(sun_sign)
    
    moon_sign = big_three.get("moon", {}).get("sign", "")
    if moon_sign and moon_sign in SOUL_KEYWORDS_TEMPLATES:
        template_keywords = SOUL_KEYWORDS_TEMPLATES[moon_sign]
        if len(template_keywords) >= 2:
            keywords.append({
                "word": template_keywords[1],
                "source": f"月亮{moon_sign}",
                "type": "内在需求",
                "weight": 9,
            })
            used_sources.add(moon_sign)
    
    asc_sign = big_three.get("ascendant", {}).get("sign", "")
    if asc_sign and asc_sign in SOUL_KEYWORDS_TEMPLATES:
        template_keywords = SOUL_KEYWORDS_TEMPLATES[asc_sign]
        if len(template_keywords) >= 3:
            keywords.append({
                "word": template_keywords[2],
                "source": f"上升{asc_sign}",
                "type": "外在表现",
                "weight": 8,
            })
            used_sources.add(asc_sign)
    
    for stellium in stelliums:
        sign = stellium.get("sign", "")
        if sign and sign not in used_sources and sign in SOUL_KEYWORDS_TEMPLATES:
            template_keywords = SOUL_KEYWORDS_TEMPLATES[sign]
            count = stellium.get("count", 0)
            if template_keywords:
                keywords.append({
                    "word": template_keywords[-1] if len(template_keywords) > 0 else sign,
                    "source": f"群星{sign}({count}颗)",
                    "type": "能量集中",
                    "weight": min(5 + count, 10),
                })
                used_sources.add(sign)
    
    for tag in resolved_tags:
        if tag.get("is_resolved"):
            keywords.append({
                "word": tag.get("name", ""),
                "source": tag.get("source", ""),
                "type": "对冲整合",
                "weight": tag.get("intensity", 7),
            })
    
    element_style = ELEMENT_STYLES.get(dominant_element, {})
    if element_style.get("style"):
        keywords.append({
            "word": element_style["style"],
            "source": f"{dominant_element}象主导",
            "type": "元素风格",
            "weight": 7,
        })
    
    keywords.sort(key=lambda x: x.get("weight", 0), reverse=True)
    
    unique_keywords = []
    seen_words = set()
    for kw in keywords:
        word = kw.get("word", "")
        if word and word not in seen_words:
            unique_keywords.append(kw)
            seen_words.add(word)
    
    logger.info(f"生成了 {len(unique_keywords)} 个灵魂关键词")
    return unique_keywords[:8]


def generate_avoid_guide(
    big_three: Dict[str, Any],
    aspects: List[Dict[str, Any]],
    resolved_tags: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    生成避雷指南
    """
    avoid_topics = []
    added_topics = set()
    
    sun_sign = big_three.get("sun", {}).get("sign", "")
    if sun_sign and sun_sign in AVOID_TOPICS_BY_SIGN:
        for topic in AVOID_TOPICS_BY_SIGN[sun_sign]:
            if topic not in added_topics:
                avoid_topics.append({
                    "topic": topic,
                    "severity": "高",
                    "reason": f"太阳{sun_sign}的核心雷区",
                    "source": f"太阳{sun_sign}",
                })
                added_topics.add(topic)
    
    moon_sign = big_three.get("moon", {}).get("sign", "")
    if moon_sign and moon_sign in AVOID_TOPICS_BY_SIGN:
        for topic in AVOID_TOPICS_BY_SIGN[moon_sign][:2]:
            if topic not in added_topics:
                avoid_topics.append({
                    "topic": topic,
                    "severity": "中",
                    "reason": f"月亮{moon_sign}的情感雷区",
                    "source": f"月亮{moon_sign}",
                })
                added_topics.add(topic)
    
    for aspect in aspects:
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_type = aspect.get("aspect", "")
        aspect_type_type = aspect.get("type", "")
        
        if aspect_type_type in ["紧张", "对立"]:
            if p1 == "火星" or p2 == "火星":
                topic = "无端挑衅"
                if topic not in added_topics:
                    avoid_topics.append({
                        "topic": topic,
                        "severity": "高",
                        "reason": f"{p1}{aspect_type}{p2}容易引发冲突",
                        "source": f"{p1}{aspect_type}{p2}",
                    })
                    added_topics.add(topic)
            
            if p1 == "冥王星" or p2 == "冥王星":
                topic = "不信任试探"
                if topic not in added_topics:
                    avoid_topics.append({
                        "topic": topic,
                        "severity": "高",
                        "reason": f"{p1}{aspect_type}{p2}对信任敏感",
                        "source": f"{p1}{aspect_type}{p2}",
                    })
                    added_topics.add(topic)
            
            if p1 == "土星" or p2 == "土星":
                topic = "不负责任"
                if topic not in added_topics:
                    avoid_topics.append({
                        "topic": topic,
                        "severity": "中",
                        "reason": f"{p1}{aspect_type}{p2}重视责任感",
                        "source": f"{p1}{aspect_type}{p2}",
                    })
                    added_topics.add(topic)
    
    for tag in resolved_tags:
        if tag.get("category") == "内在冲突":
            source = tag.get("source", "")
            if "火星" in source and "土星" in source:
                topic = "过度压制"
                if topic not in added_topics:
                    avoid_topics.append({
                        "topic": topic,
                        "severity": "中",
                        "reason": "冲动但克制的性格需要合理释放",
                        "source": source,
                    })
                    added_topics.add(topic)
    
    logger.info(f"生成了 {len(avoid_topics)} 个避雷指南条目")
    return avoid_topics[:6]


def generate_recommended_topics(
    big_three: Dict[str, Any],
    stelliums: List[Dict[str, Any]],
    dominant_element: str
) -> List[Dict[str, Any]]:
    """
    生成推荐共同话题
    """
    recommended = []
    added_topics = set()
    
    sun_sign = big_three.get("sun", {}).get("sign", "")
    if sun_sign and sun_sign in RECOMMENDED_TOPICS_BY_SIGN:
        for i, topic in enumerate(RECOMMENDED_TOPICS_BY_SIGN[sun_sign][:2]):
            if topic not in added_topics:
                recommended.append({
                    "topic": topic,
                    "interest_level": "高",
                    "reason": f"太阳{sun_sign}的核心兴趣",
                    "source": f"太阳{sun_sign}",
                    "conversation_starters": _generate_conversation_starters(topic, sun_sign),
                })
                added_topics.add(topic)
    
    moon_sign = big_three.get("moon", {}).get("sign", "")
    if moon_sign and moon_sign in RECOMMENDED_TOPICS_BY_SIGN:
        for topic in RECOMMENDED_TOPICS_BY_SIGN[moon_sign][:2]:
            if topic not in added_topics:
                recommended.append({
                    "topic": topic,
                    "interest_level": "中高",
                    "reason": f"月亮{moon_sign}的情感共鸣点",
                    "source": f"月亮{moon_sign}",
                    "conversation_starters": _generate_conversation_starters(topic, moon_sign),
                })
                added_topics.add(topic)
    
    for stellium in stelliums:
        sign = stellium.get("sign", "")
        if sign and sign in RECOMMENDED_TOPICS_BY_SIGN:
            for topic in RECOMMENDED_TOPICS_BY_SIGN[sign][:1]:
                if topic not in added_topics:
                    count = stellium.get("count", 0)
                    recommended.append({
                        "topic": topic,
                        "interest_level": "高",
                        "reason": f"群星{sign}({count}颗)能量聚焦",
                        "source": f"群星{sign}",
                        "conversation_starters": _generate_conversation_starters(topic, sign),
                    })
                    added_topics.add(topic)
    
    element_style = ELEMENT_STYLES.get(dominant_element, {})
    if element_style.get("style"):
        element_topic = _get_element_topic(dominant_element)
        if element_topic and element_topic not in added_topics:
            recommended.append({
                "topic": element_topic,
                "interest_level": "中",
                "reason": f"{dominant_element}象主导的沟通风格",
                "source": f"{dominant_element}象元素",
                "conversation_starters": _generate_element_conversation_starters(dominant_element),
            })
            added_topics.add(element_topic)
    
    logger.info(f"生成了 {len(recommended)} 个推荐话题")
    return recommended[:6]


def _generate_conversation_starters(topic: str, sign: str) -> List[str]:
    """
    生成话题开场白
    """
    starters = []
    
    topic_starters = {
        "最新挑战": ["最近有没有什么让你兴奋的挑战？", "你平时喜欢什么样的运动或活动？"],
        "美食体验": ["你最近发现什么好吃的了吗？", "你喜欢什么类型的美食？"],
        "新奇事物": ["最近有什么新鲜事让你感兴趣吗？", "你平时喜欢关注什么类型的资讯？"],
        "家庭故事": ["你家人有没有什么有趣的故事？", "你小时候印象最深的是什么？"],
        "成就展示": ["最近有没有什么让你感到自豪的成就？", "你平时喜欢做什么来展现自己？"],
        "效率提升": ["你有没有什么提高效率的小技巧？", "你平时是怎么规划时间的？"],
        "艺术文化": ["你最近看了什么展览或演出吗？", "你喜欢什么类型的艺术？"],
        "深度话题": ["你对人性有什么看法？", "你相信直觉吗？"],
        "旅行计划": ["你最想去哪里旅行？", "你印象最深的一次旅行是？"],
        "职业规划": ["你对未来有什么规划？", "你理想中的工作是什么样的？"],
        "科技创新": ["你最近关注什么科技动态吗？", "你觉得未来会是什么样子？"],
        "艺术创作": ["你平时喜欢做什么 creative 的事情？", "你最近有什么灵感吗？"],
    }
    
    if topic in topic_starters:
        starters = topic_starters[topic]
    else:
        starters = [
            f"你对{topic}有什么看法吗？",
            f"你平时喜欢聊{topic}相关的话题吗？",
        ]
    
    return starters


def _get_element_topic(element: str) -> str:
    """
    获取元素对应的话题
    """
    element_topics = {
        "火": "激情与动力",
        "土": "现实与规划",
        "风": "想法与交流",
        "水": "情感与感受",
    }
    return element_topics.get(element, "")


def _generate_element_conversation_starters(element: str) -> List[str]:
    """
    生成元素话题开场白
    """
    element_starters = {
        "火": ["什么事情能让你真正充满热情？", "你平时是怎么保持动力的？"],
        "土": ["你最近有什么具体的计划吗？", "你觉得安全感来自哪里？"],
        "风": ["你最近有什么有趣的想法吗？", "你喜欢和什么样的人聊天？"],
        "水": ["你最近有什么触动你的事情吗？", "你觉得什么能让你感到被理解？"],
    }
    return element_starters.get(element, [])


SOCIAL_CARD_AI_PROMPT = """你是一位社交破冰专家，擅长将占星学数据转化为生动、口语化、网感强的社交文案。

任务：根据用户的星盘配置，生成一段用于社交破冰的个性化介绍文案。

要求：
1. 风格：网感强、口语化、生动有趣，拒绝刻板印象和套话
2. 长度：约150-200字
3. 内容：结合以下信息，用生活化的语言描述
   - 三巨头配置（太阳、月亮、上升）
   - 灵魂关键词
   - 性格对冲整合（如果有的话）

输出格式：
直接输出文案内容，不要用markdown格式，不要加标题。

星盘配置信息：
{chart_info}

请用生动有趣的方式描述这个人的社交特质，让别人一眼就能get到TA的特点，同时有想要了解更多的欲望。"""


async def generate_ai_social_intro(
    chart_data: Dict[str, Any],
    soul_keywords: List[Dict[str, Any]],
    resolution_summary: str,
    name: str = "用户"
) -> str:
    """
    调用AI生成社交介绍文案
    """
    big_three = chart_data.get("ascendant", {})
    planets = chart_data.get("planets", [])
    
    sun_info = None
    moon_info = None
    asc_info = None
    
    for planet in planets:
        if planet.get("name") == "太阳":
            sun_info = planet.get("zodiac", {})
        elif planet.get("name") == "月亮":
            moon_info = planet.get("zodiac", {})
    
    ascendant = chart_data.get("ascendant", {})
    if ascendant:
        asc_info = ascendant
    
    chart_info_parts = []
    chart_info_parts.append(f"姓名: {name}")
    
    if sun_info:
        chart_info_parts.append(f"太阳星座: {sun_info.get('sign', '未知')}")
    if moon_info:
        chart_info_parts.append(f"月亮星座: {moon_info.get('sign', '未知')}")
    if asc_info:
        chart_info_parts.append(f"上升星座: {asc_info.get('sign', '未知')}")
    
    if soul_keywords:
        keywords_str = "、".join([kw.get("word", "") for kw in soul_keywords[:5]])
        chart_info_parts.append(f"灵魂关键词: {keywords_str}")
    
    if resolution_summary and "对冲" in resolution_summary:
        chart_info_parts.append(f"性格整合: {resolution_summary}")
    
    chart_info = "\n".join(chart_info_parts)
    
    prompt = SOCIAL_CARD_AI_PROMPT.format(chart_info=chart_info)
    
    try:
        logger.info("开始调用AI生成社交文案")
        ai_response = await call_qwen_api(
            prompt=prompt,
            temperature=0.8,
            max_tokens=500
        )
        
        if ai_response and ai_response.strip():
            logger.info(f"AI社交文案生成成功，长度: {len(ai_response)}")
            return ai_response.strip()
        
    except Exception as e:
        logger.error(f"AI生成社交文案失败: {str(e)}")
    
    return _generate_fallback_intro(soul_keywords, resolution_summary, name)


def _generate_fallback_intro(
    soul_keywords: List[Dict[str, Any]],
    resolution_summary: str,
    name: str
) -> str:
    """
    AI调用失败时的备用文案
    """
    keywords = [kw.get("word", "") for kw in soul_keywords[:3]] if soul_keywords else []
    
    if keywords:
        intro = f"✨ {name}是一个{'、'.join(keywords)}的人"
    else:
        intro = f"✨ {name}是一个独特的灵魂"
    
    if resolution_summary and "对冲" in resolution_summary:
        intro += f"，{resolution_summary}"
    
    intro += "。来认识一下吧！"
    
    return intro


async def generate_social_card(
    chart_data: Dict[str, Any],
    name: str = "用户"
) -> Dict[str, Any]:
    """
    主函数：生成完整的社交名片
    """
    logger.info(f"开始为 {name} 生成社交名片")
    
    if not chart_data:
        logger.error("星盘数据为空")
        return {
            "success": False,
            "error": "星盘数据为空",
            "error_type": "invalid_input",
        }
    
    planets = chart_data.get("planets", [])
    aspects = chart_data.get("aspects", [])
    
    if not planets:
        logger.error("星盘数据不完整：缺少行星信息")
        return {
            "success": False,
            "error": "星盘数据不完整：缺少行星信息",
            "error_type": "invalid_input",
        }
    
    tag_matrix = extract_tag_matrix(chart_data)
    conflict_analysis = generate_conflict_aware_personality(chart_data, tag_matrix)
    
    config = tag_matrix.get("configuration", {})
    big_three = config.get("big_three", {})
    stelliums = config.get("stelliums", [])
    key_aspects = config.get("key_aspects", [])
    
    distribution = tag_matrix.get("distribution", {})
    dominant_element = distribution.get("dominant_element", "火")
    dominant_quality = distribution.get("dominant_quality", "开创")
    
    resolved_tags = []
    resolved_matrix = conflict_analysis.get("resolved_tags_matrix", {})
    for category, tags in resolved_matrix.items():
        for tag in tags:
            resolved_tags.append(tag)
    
    soul_keywords = generate_soul_keywords(
        big_three=big_three,
        stelliums=stelliums,
        resolved_tags=resolved_tags,
        dominant_element=dominant_element,
        dominant_quality=dominant_quality
    )
    
    avoid_guide = generate_avoid_guide(
        big_three=big_three,
        aspects=key_aspects,
        resolved_tags=resolved_tags
    )
    
    recommended_topics = generate_recommended_topics(
        big_three=big_three,
        stelliums=stelliums,
        dominant_element=dominant_element
    )
    
    resolution_summary = conflict_analysis.get("resolution_summary", "")
    
    try:
        ai_intro = await generate_ai_social_intro(
            chart_data=chart_data,
            soul_keywords=soul_keywords,
            resolution_summary=resolution_summary,
            name=name
        )
    except Exception as e:
        logger.error(f"生成AI社交文案时出错: {str(e)}")
        ai_intro = _generate_fallback_intro(soul_keywords, resolution_summary, name)
    
    sun_sign = big_three.get("sun", {}).get("sign", "")
    moon_sign = big_three.get("moon", {}).get("sign", "")
    asc_sign = big_three.get("ascendant", {}).get("sign", "")
    
    result = {
        "success": True,
        "social_card": {
            "name": name,
            "big_three": {
                "sun": big_three.get("sun"),
                "moon": big_three.get("moon"),
                "ascendant": big_three.get("ascendant"),
                "summary": f"太阳{sun_sign} · 月亮{moon_sign} · 上升{asc_sign}",
            },
            "ai_intro": ai_intro,
            "soul_keywords": soul_keywords,
            "avoid_guide": avoid_guide,
            "recommended_topics": recommended_topics,
            "distribution": {
                "elements": distribution.get("elements", {}),
                "qualities": distribution.get("qualities", {}),
                "dominant_element": dominant_element,
                "dominant_quality": dominant_quality,
            },
        },
        "conflict_analysis": {
            "has_conflicts": conflict_analysis.get("has_resolved_conflicts", False),
            "resolution_summary": resolution_summary,
            "conflicts_count": conflict_analysis.get("conflicts_detected", {}).get("total_count", 0),
        },
    }
    
    logger.info(f"社交名片生成成功: {name}")
    return result
