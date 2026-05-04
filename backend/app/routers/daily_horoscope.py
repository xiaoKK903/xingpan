from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy.orm import Session
import json

from app.schemas import ApiResponse
from app.database import get_db
from app.models import User, Chart
from app.routers.users import get_current_user, get_current_user_optional

router = APIRouter()

ZODIAC_SIGNS = [
    "白羊座", "金牛座", "双子座", "巨蟹座",
    "狮子座", "处女座", "天秤座", "天蝎座",
    "射手座", "摩羯座", "水瓶座", "双鱼座"
]

ZODIAC_SYMBOLS = [
    "♈", "♉", "♊", "♋",
    "♌", "♍", "♎", "♏",
    "♐", "♑", "♒", "♓"
]

ZODIAC_COLORS = [
    "#ef4444", "#22c55e", "#eab308", "#3b82f6",
    "#f97316", "#22c55e", "#ec4899", "#ef4444",
    "#f97316", "#6b7280", "#06b6d4", "#3b82f6"
]

ELEMENTS = ["火", "土", "风", "水"]
ELEMENT_NAMES = ["火象", "土象", "风象", "水象"]

QUALITIES = ["开创", "固定", "变动"]


class PersonalizedHoroscope(BaseModel):
    sign: str = Field(..., description="星座名称")
    symbol: str = Field(..., description="星座符号")
    date: str = Field(..., description="运势日期")
    
    sun_sign: Optional[str] = Field(None, description="用户太阳星座")
    moon_sign: Optional[str] = Field(None, description="用户月亮星座")
    ascendant_sign: Optional[str] = Field(None, description="用户上升星座")
    is_personalized: bool = Field(False, description="是否为个性化运势")
    
    overall_score: int = Field(..., description="整体运势评分 0-100")
    
    love_score: int = Field(..., description="感情运势评分")
    love_opportunity: str = Field(..., description="感情今日机遇")
    love_challenge: str = Field(..., description="感情今日挑战")
    love_advice: str = Field(..., description="感情今日建议")
    
    career_score: int = Field(..., description="事业运势评分")
    career_opportunity: str = Field(..., description="事业今日机遇")
    career_challenge: str = Field(..., description="事业今日挑战")
    career_advice: str = Field(..., description="事业今日建议")
    
    wealth_score: int = Field(..., description="财运评分")
    wealth_opportunity: str = Field(..., description="财运今日机遇")
    wealth_challenge: str = Field(..., description="财运今日挑战")
    wealth_advice: str = Field(..., description="财运今日建议")
    
    health_score: int = Field(..., description="健康运势评分")
    health_opportunity: str = Field(..., description="健康今日机遇")
    health_challenge: str = Field(..., description="健康今日挑战")
    health_advice: str = Field(..., description="健康今日建议")
    
    keywords: List[str] = Field(..., description="今日关键词")
    lucky_tips: List[str] = Field(..., description="开运小建议")
    
    lucky_color: str = Field(..., description="今日幸运色")
    lucky_number: int = Field(..., description="今日幸运数字")
    lucky_zodiac: str = Field(..., description="贵人星座")
    cautious_zodiac: str = Field(..., description="提防星座")
    lucky_time: str = Field(..., description="幸运时间段")
    lucky_direction: str = Field(..., description="幸运方位")


def get_sign_index(sign_name: str) -> int:
    try:
        return ZODIAC_SIGNS.index(sign_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的星座名称: {sign_name}")


def get_element(sign_index: int) -> int:
    return sign_index % 4


def get_quality(sign_index: int) -> int:
    return sign_index % 3


def get_daily_seed(current_date: date, sign_index: int) -> int:
    date_str = current_date.strftime("%Y%m%d")
    return int(date_str) + sign_index * 1000


def pseudo_random(seed: int, min_val: int, max_val: int, offset: int = 0) -> int:
    a = 1103515245
    c = 12345
    m = 2**31
    seed = (a * (seed + offset) + c) % m
    return min_val + (seed % (max_val - min_val + 1))


def get_element_opportunity(element_name: str, category: str) -> List[str]:
    opportunities = {
        "火象": {
            "love": [
                "你的热情会吸引他人注意，适合主动表达心意",
                "今日魅力四射，单身者有机会遇到心动对象",
                "热情洋溢的你容易获得他人好感，适合增进感情",
                "你的自信和活力会让你在感情中更有吸引力"
            ],
            "career": [
                "行动力强，适合启动新项目或推进重要工作",
                "领导能力得到展现，有机会承担更重要的任务",
                "竞争中占据优势，适合谈判和争取资源",
                "创意迸发，适合提出新想法和解决方案"
            ],
            "wealth": [
                "投资直觉敏锐，适合稳健型投资",
                "有机会获得额外收入或奖金",
                "商业合作顺利，财运向好",
                "理财思路清晰，适合规划财务目标"
            ],
            "health": [
                "精力充沛，适合运动健身",
                "新陈代谢旺盛，身体状态良好",
                "适合户外活动，呼吸新鲜空气",
                "体力充沛，可以尝试新的运动方式"
            ]
        },
        "土象": {
            "love": [
                "稳重可靠的你更容易获得对方信任",
                "适合处理感情中的实际问题，关系更加稳固",
                "务实的态度有助于感情的长远发展",
                "耐心和坚持会让感情开花结果"
            ],
            "career": [
                "细致认真，适合处理细节工作和复杂事务",
                "责任感强，工作成果容易获得认可",
                "适合财务规划和长期项目推进",
                "执行力强，计划能稳步推进"
            ],
            "wealth": [
                "理财能力出色，适合稳健投资",
                "有机会获得稳定收益",
                "储蓄意识增强，适合积累财富",
                "适合长期财务规划，眼光独到"
            ],
            "health": [
                "身体状况稳定，适合规律作息",
                "抵抗力较强，但仍需注意保暖",
                "适合养生调理，身体状态良好",
                "适合慢运动，如瑜伽、太极"
            ]
        },
        "风象": {
            "love": [
                "沟通顺畅，适合化解误会和深入交流",
                "思维活跃，约会时话题丰富有趣",
                "社交能力增强，容易结识新朋友",
                "机智幽默的你会给对方留下好印象"
            ],
            "career": [
                "思维敏捷，适合创意工作和问题解决",
                "沟通能力出色，适合会议和演讲",
                "社交网络活跃，有机会获得新机会",
                "学习能力强，适合新技能培训"
            ],
            "wealth": [
                "信息获取能力强，投资判断准确",
                "有机会通过社交获得财务机会",
                "理财思路灵活，适合多元化投资",
                "商业嗅觉敏锐，发现新机会"
            ],
            "health": [
                "思维活跃，适合脑力活动",
                "呼吸顺畅，适合有氧运动",
                "心情愉悦，心理健康良好",
                "适合社交活动，保持身心愉悦"
            ]
        },
        "水象": {
            "love": [
                "敏感细腻，能够感知对方情绪变化",
                "浪漫指数上升，适合浪漫约会",
                "直觉准确，能够把握感情机会",
                "温柔体贴的你让感情更加甜蜜"
            ],
            "career": [
                "直觉敏锐，能够察觉他人需求和市场变化",
                "同理心强，适合团队协作和客户服务",
                "艺术灵感涌现，适合创意工作",
                "善于观察细节，发现隐藏机会"
            ],
            "wealth": [
                "直觉投资可能带来惊喜",
                "有意外收获的机会",
                "适合与他人合作的投资项目",
                "财务直觉敏锐，把握机会"
            ],
            "health": [
                "情绪敏感，需要保持心情舒畅",
                "适合静心冥想，缓解压力",
                "睡眠质量重要，注意休息",
                "适合游泳等水中运动"
            ]
        }
    }
    return opportunities.get(element_name, {}).get(category, ["今日运势平稳"])


def get_element_challenge(element_name: str, category: str) -> List[str]:
    challenges = {
        "火象": {
            "love": [
                "过于冲动可能让对方感到压力",
                "耐心不足，容易因小事争吵",
                "需要学会倾听，不要急于表达",
                "控制欲可能让对方感到束缚"
            ],
            "career": [
                "过于急躁可能忽略细节",
                "容易因冲动做出错误决定",
                "耐心不足，项目推进可能遇到阻碍",
                "竞争心态太强，影响团队协作"
            ],
            "wealth": [
                "冲动消费可能超支",
                "投资过于激进风险增加",
                "需要控制购物欲望",
                "财务计划可能被打乱"
            ],
            "health": [
                "过度消耗可能导致疲劳",
                "需要注意休息，避免过度运动",
                "火气旺盛，注意清火",
                "避免熬夜，保证充足睡眠"
            ]
        },
        "土象": {
            "love": [
                "过于保守可能错过机会",
                "表达情感不够直接，对方可能误解",
                "过于现实可能忽略浪漫",
                "固执己见，容易产生分歧"
            ],
            "career": [
                "过于谨慎可能错失良机",
                "适应变化较慢，需要调整心态",
                "过于追求完美可能延误进度",
                "需要开放心态接受新想法"
            ],
            "wealth": [
                "过于保守可能错过投资机会",
                "对风险过度担忧",
                "需要适度尝试新的理财方式",
                "财务规划可能过于僵化"
            ],
            "health": [
                "过于劳累可能引发肩颈问题",
                "需要注意放松，避免久坐",
                "消化系统需要呵护，注意饮食",
                "压力可能导致身体不适"
            ]
        },
        "风象": {
            "love": [
                "过于理性可能让对方感受不到热情",
                "想法多变可能让对方感到不安",
                "需要更多实际行动，不要只说不做",
                "可能忽略对方的真实感受"
            ],
            "career": [
                "注意力容易分散，需要提高专注力",
                "想法太多可能难以聚焦",
                "执行力度不够，计划可能停滞",
                "需要更多耐心和坚持"
            ],
            "wealth": [
                "想法多变可能导致投资不稳定",
                "需要更稳健的财务规划",
                "避免跟风投资",
                "信息过载可能导致决策困难"
            ],
            "health": [
                "思维过度活跃可能影响睡眠",
                "需要学会放松，避免过度思考",
                "呼吸系统需要注意",
                "适当运动释放能量"
            ]
        },
        "水象": {
            "love": [
                "过于敏感可能误解对方意图",
                "情绪波动可能影响感情",
                "需要学会表达，不要憋在心里",
                "可能因过度分析产生不必要的担忧"
            ],
            "career": [
                "情绪波动可能影响工作效率",
                "过于敏感可能过度解读他人意见",
                "需要更多理性思考",
                "避免过度担忧，保持积极心态"
            ],
            "wealth": [
                "情绪可能影响财务决策",
                "避免情绪化消费",
                "投资时需要更理性分析",
                "避免因他人影响改变计划"
            ],
            "health": [
                "情绪敏感容易导致失眠",
                "需要学会调节情绪",
                "注意水分补充",
                "避免过度思虑，保持心情平静"
            ]
        }
    }
    return challenges.get(element_name, {}).get(category, ["今日需要保持冷静"])


def get_element_advice(element_name: str, category: str) -> List[str]:
    advices = {
        "火象": {
            "love": [
                "放慢脚步，给对方一些空间和时间",
                "学会倾听，多关注对方的感受",
                "用行动表达爱意，而不仅仅是言语",
                "保持热情的同时增加耐心"
            ],
            "career": [
                "三思而后行，避免冲动决策",
                "关注细节，不要只看大局",
                "与团队合作，学会倾听他人意见",
                "制定详细计划，稳步推进"
            ],
            "wealth": [
                "控制消费欲望，理性购物",
                "制定预算，避免超支",
                "投资前做好调研，不要盲目跟风",
                "建立应急储蓄，应对不时之需"
            ],
            "health": [
                "劳逸结合，避免过度消耗",
                "保证充足睡眠，给身体恢复时间",
                "饮食清淡，避免上火",
                "适当做些舒缓运动，如散步"
            ]
        },
        "土象": {
            "love": [
                "适当表达情感，不要过于含蓄",
                "增加浪漫元素，让感情更有活力",
                "学会变通，不要过于固执",
                "倾听对方想法，尊重差异"
            ],
            "career": [
                "适当冒险，不要过于保守",
                "拥抱变化，适应新环境",
                "尝试新方法，不要固守旧习惯",
                "保持务实同时增加一些灵活性"
            ],
            "wealth": [
                "适度尝试新的投资方式",
                "分散投资，降低风险",
                "关注长期收益，不要只看眼前",
                "定期复盘财务状况"
            ],
            "health": [
                "定期运动，避免久坐",
                "注意放松，缓解压力",
                "规律作息，保证睡眠",
                "适当做些按摩，缓解肌肉紧张"
            ]
        },
        "风象": {
            "love": [
                "用行动证明心意，不要只说不做",
                "增加稳定性，让对方感到安心",
                "更多关注对方的实际需求",
                "保持沟通同时增加行动"
            ],
            "career": [
                "提高专注力，一次只做一件事",
                "制定明确目标，避免分心",
                "坚持执行，不要轻易改变计划",
                "将想法落实到行动中"
            ],
            "wealth": [
                "制定稳定的财务计划",
                "不要频繁改变投资策略",
                "筛选信息，避免信息过载",
                "定期储蓄，建立财务安全网"
            ],
            "health": [
                "睡前放松，避免过度思考",
                "适当运动释放过剩精力",
                "保持规律作息",
                "练习专注力，如冥想"
            ]
        },
        "水象": {
            "love": [
                "直接表达想法，不要让对方猜测",
                "学会理性分析，不要过度敏感",
                "保持积极心态，避免过度担忧",
                "相信自己值得被爱"
            ],
            "career": [
                "保持情绪稳定，不要受外界影响",
                "理性分析问题，不要被情绪左右",
                "学会释放压力，保持积极心态",
                "相信自己的直觉，同时增加理性"
            ],
            "wealth": [
                "避免情绪化决策",
                "制定冷静期，冲动消费前先思考",
                "记录收支，了解财务状况",
                "寻求专业建议，不要独自决策"
            ],
            "health": [
                "学会调节情绪，保持心情愉悦",
                "适当社交，不要独处太久",
                "保证充足睡眠，避免熬夜",
                "练习冥想或瑜伽，平复情绪"
            ]
        }
    }
    return advices.get(element_name, {}).get(category, ["保持积极心态"])


def get_keywords(sign_index: int, seed: int) -> List[str]:
    all_keywords = [
        ["突破", "创新", "勇气", "行动", "热情"],
        ["稳定", "收获", "务实", "坚持", "耐心"],
        ["交流", "智慧", "灵活", "学习", "社交"],
        ["情感", "直觉", "温柔", "关怀", "滋养"],
        ["自信", "光芒", "领导", "荣耀", "创造"],
        ["细致", "服务", "健康", "分析", "整理"],
        ["和谐", "关系", "美学", "平衡", "合作"],
        ["深度", "转化", "力量", "重生", "洞察"],
        ["探索", "自由", "哲学", "远方", "乐观"],
        ["责任", "成就", "自律", "目标", "耐心"],
        ["独立", "改革", "创新", "未来", "突破"],
        ["梦想", "灵性", "艺术", "直觉", "慈悲"]
    ]
    
    keywords = all_keywords[sign_index]
    count = pseudo_random(seed, 2, 4, 0)
    result = []
    used = set()
    for i in range(count):
        idx = pseudo_random(seed + i, 0, len(keywords) - 1, i + 10)
        if idx not in used:
            used.add(idx)
            result.append(keywords[idx])
    
    if not result:
        result = keywords[:3]
    
    return result


def get_lucky_tips(sign_index: int, seed: int) -> List[str]:
    all_tips = [
        "穿着明亮颜色的衣服提升运势",
        "在上午9点前完成最重要的任务",
        "随身携带一小块水晶或玉石",
        "向帮助过你的人表达感谢",
        "在窗边摆放绿色植物",
        "听一首让你心情愉悦的歌曲",
        "写下今天想要实现的三个目标",
        "为自己泡一杯热茶或咖啡",
        "在镜子前给自己一个微笑",
        "整理桌面，让环境更整洁",
        "抽时间呼吸新鲜空气",
        "与朋友分享你的想法",
        "尝试做一件以前没做过的小事",
        "给自己一个放松的时刻",
        "回顾昨天的收获，感恩生活"
    ]
    
    count = pseudo_random(seed, 3, 4, 0)
    result = []
    used = set()
    for i in range(count):
        idx = pseudo_random(seed + i, 0, len(all_tips) - 1, i + 20)
        if idx not in used:
            used.add(idx)
            result.append(all_tips[idx])
    
    if not result:
        result = all_tips[:3]
    
    return result


def generate_horoscope(
    sign_name: str, 
    current_date: date,
    sun_sign: Optional[str] = None,
    moon_sign: Optional[str] = None,
    ascendant_sign: Optional[str] = None
) -> PersonalizedHoroscope:
    sign_index = get_sign_index(sign_name)
    seed = get_daily_seed(current_date, sign_index)
    
    element_index = get_element(sign_index)
    element_name = ELEMENT_NAMES[element_index]
    
    quality_index = get_quality(sign_index)
    quality_name = QUALITIES[quality_index]
    
    overall_score = pseudo_random(seed, 60, 95, 0)
    love_score = pseudo_random(seed, 55, 95, 1)
    career_score = pseudo_random(seed, 55, 95, 2)
    wealth_score = pseudo_random(seed, 55, 95, 3)
    health_score = pseudo_random(seed, 60, 95, 4)
    
    love_opportunities = get_element_opportunity(element_name, "love")
    love_challenges = get_element_challenge(element_name, "love")
    love_advices = get_element_advice(element_name, "love")
    
    career_opportunities = get_element_opportunity(element_name, "career")
    career_challenges = get_element_challenge(element_name, "career")
    career_advices = get_element_advice(element_name, "career")
    
    wealth_opportunities = get_element_opportunity(element_name, "wealth")
    wealth_challenges = get_element_challenge(element_name, "wealth")
    wealth_advices = get_element_advice(element_name, "wealth")
    
    health_opportunities = get_element_opportunity(element_name, "health")
    health_challenges = get_element_challenge(element_name, "health")
    health_advices = get_element_advice(element_name, "health")
    
    love_idx = pseudo_random(seed, 0, len(love_opportunities) - 1, 10)
    career_idx = pseudo_random(seed, 0, len(career_opportunities) - 1, 11)
    wealth_idx = pseudo_random(seed, 0, len(wealth_opportunities) - 1, 12)
    health_idx = pseudo_random(seed, 0, len(health_opportunities) - 1, 13)
    
    lucky_colors = ["红色", "绿色", "黄色", "蓝色", "橙色", "粉色", "紫色", "黑色", "金色", "灰色", "青色", "白色"]
    lucky_numbers = [3, 7, 8, 4, 9, 2, 5, 6, 1, 10, 11, 12]
    
    lucky_color_idx = pseudo_random(seed, 0, 11, 20)
    lucky_number_idx = pseudo_random(seed, 0, 11, 21)
    lucky_zodiac_idx = pseudo_random(seed, 0, 11, 22)
    cautious_zodiac_idx = pseudo_random(seed, 0, 11, 23)
    
    while lucky_zodiac_idx == sign_index:
        lucky_zodiac_idx = (lucky_zodiac_idx + 1) % 12
    
    while cautious_zodiac_idx == sign_index or cautious_zodiac_idx == lucky_zodiac_idx:
        cautious_zodiac_idx = (cautious_zodiac_idx + 1) % 12
    
    time_slots = ["09:00-11:00", "13:00-15:00", "17:00-19:00", "20:00-22:00"]
    directions = ["正东", "正南", "正西", "正北", "东南", "东北", "西南", "西北"]
    
    lucky_time_idx = pseudo_random(seed, 0, 3, 24)
    lucky_direction_idx = pseudo_random(seed, 0, 7, 25)
    
    keywords = get_keywords(sign_index, seed)
    lucky_tips = get_lucky_tips(sign_index, seed)
    
    is_personalized = sun_sign is not None
    
    return PersonalizedHoroscope(
        sign=sign_name,
        symbol=ZODIAC_SYMBOLS[sign_index],
        date=current_date.strftime("%Y年%m月%d日"),
        
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        ascendant_sign=ascendant_sign,
        is_personalized=is_personalized,
        
        overall_score=overall_score,
        
        love_score=love_score,
        love_opportunity=love_opportunities[love_idx],
        love_challenge=love_challenges[love_idx],
        love_advice=love_advices[love_idx],
        
        career_score=career_score,
        career_opportunity=career_opportunities[career_idx],
        career_challenge=career_challenges[career_idx],
        career_advice=career_advices[career_idx],
        
        wealth_score=wealth_score,
        wealth_opportunity=wealth_opportunities[wealth_idx],
        wealth_challenge=wealth_challenges[wealth_idx],
        wealth_advice=wealth_advices[wealth_idx],
        
        health_score=health_score,
        health_opportunity=health_opportunities[health_idx],
        health_challenge=health_challenges[health_idx],
        health_advice=health_advices[health_idx],
        
        keywords=keywords,
        lucky_tips=lucky_tips,
        
        lucky_color=lucky_colors[lucky_color_idx],
        lucky_number=lucky_numbers[lucky_number_idx],
        lucky_zodiac=ZODIAC_SIGNS[lucky_zodiac_idx],
        cautious_zodiac=ZODIAC_SIGNS[cautious_zodiac_idx],
        lucky_time=time_slots[lucky_time_idx],
        lucky_direction=directions[lucky_direction_idx]
    )


def get_user_astrology_info(current_user: User, db: Session) -> Optional[dict]:
    charts = db.query(Chart).filter(
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).order_by(Chart.created_at.desc()).all()
    
    if not charts:
        return None
    
    latest_chart = charts[0]
    
    try:
        chart_data = json.loads(latest_chart.chart_data)
        
        sun_sign = chart_data.get('sun_sign', {}).get('sign')
        moon_sign = chart_data.get('moon_sign', {}).get('sign')
        ascendant_sign = chart_data.get('ascendant', {}).get('sign')
        
        return {
            'sun_sign': sun_sign,
            'moon_sign': moon_sign,
            'ascendant_sign': ascendant_sign
        }
    except Exception as e:
        print(f"Error parsing chart data: {e}")
        return None


@router.get("/today", response_model=ApiResponse)
def get_daily_horoscope(
    sign: str = Query(..., description="星座名称，如：白羊座、金牛座等"),
    date: Optional[str] = Query(None, description="日期，格式 YYYY-MM-DD，默认今天"),
    use_personal: bool = Query(False, description="是否使用用户本命盘数据进行个性化运势"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    try:
        if date:
            current_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            current_date = datetime.now().date()
        
        sun_sign = None
        moon_sign = None
        ascendant_sign = None
        
        if use_personal and current_user:
            user_astro = get_user_astrology_info(current_user, db)
            if user_astro:
                sun_sign = user_astro.get('sun_sign')
                moon_sign = user_astro.get('moon_sign')
                ascendant_sign = user_astro.get('ascendant_sign')
                
                if sun_sign:
                    sign = sun_sign
        
        horoscope = generate_horoscope(
            sign, 
            current_date,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            ascendant_sign=ascendant_sign
        )
        
        return ApiResponse(
            code=200,
            message="获取运势成功",
            data=horoscope.model_dump()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运势失败: {str(e)}")


@router.get("/personal", response_model=ApiResponse)
def get_personal_horoscope(
    date: Optional[str] = Query(None, description="日期，格式 YYYY-MM-DD，默认今天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if date:
            current_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            current_date = datetime.now().date()
        
        user_astro = get_user_astrology_info(current_user, db)
        
        if not user_astro or not user_astro.get('sun_sign'):
            raise HTTPException(
                status_code=400, 
                detail="您还没有保存本命盘数据，请先在星盘查询页面计算并保存您的星盘"
            )
        
        sun_sign = user_astro.get('sun_sign')
        moon_sign = user_astro.get('moon_sign')
        ascendant_sign = user_astro.get('ascendant_sign')
        
        horoscope = generate_horoscope(
            sun_sign, 
            current_date,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            ascendant_sign=ascendant_sign
        )
        
        return ApiResponse(
            code=200,
            message="获取个性化运势成功",
            data=horoscope.model_dump()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取运势失败: {str(e)}")


@router.get("/signs", response_model=ApiResponse)
def get_all_zodiac_signs():
    signs = []
    for i in range(12):
        signs.append({
            "index": i,
            "name": ZODIAC_SIGNS[i],
            "symbol": ZODIAC_SYMBOLS[i],
            "color": ZODIAC_COLORS[i],
            "element": ELEMENTS[i % 4],
            "quality": QUALITIES[i % 3],
            "date_range": get_date_range(i)
        })
    
    return ApiResponse(
        code=200,
        message="success",
        data={"zodiac_signs": signs}
    )


def get_date_range(index: int) -> str:
    date_ranges = [
        "3月21日 - 4月19日",
        "4月20日 - 5月20日",
        "5月21日 - 6月21日",
        "6月22日 - 7月22日",
        "7月23日 - 8月22日",
        "8月23日 - 9月22日",
        "9月23日 - 10月23日",
        "10月24日 - 11月22日",
        "11月23日 - 12月21日",
        "12月22日 - 1月19日",
        "1月20日 - 2月18日",
        "2月19日 - 3月20日"
    ]
    return date_ranges[index]
