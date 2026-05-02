from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConflictAspect:
    planet_a: str
    planet_b: str
    aspect_type: str
    conflict_tags: List[str]
    atmosphere: str
    drama_theme: str
    severity: int
    description: str
    is_harmonious: bool = False
    orb_arcminutes: float = 0.0


KEY_CONFLICT_PLANET_PAIRS = {
    ("火星", "冥王星"): {
        "conflict_theme": "权力斗争",
        "base_severity": 8,
        "description": "火星代表行动、欲望和冲动，冥王星代表深层转化、控制和权力。这两颗行星的互动会产生强烈的能量碰撞。",
        "aspects": {
            "合相": {
                "conflict_tags": ["权力斗争", "深度控制", "极致激情", "隐藏的愤怒"],
                "atmosphere": "空气中弥漫着紧张的能量，仿佛随时可能爆发激烈的冲突",
                "drama_theme": "权力与控制",
                "severity": 9,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["权力斗争", "对立冲突", "控制欲较量", "隐藏的敌意"],
                "atmosphere": "双方像磁铁的两极，既相互排斥又不可避免地被对方吸引",
                "drama_theme": "对立与吸引",
                "severity": 8,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["权力斗争", "情绪爆发", "控制欲冲突", "无意识的对抗"],
                "atmosphere": "随时可能爆发的紧张感，每一句话都可能成为导火索",
                "drama_theme": "冲突与转化",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("太阳", "月亮"): {
        "conflict_theme": "自我与情感",
        "base_severity": 4,
        "description": "太阳代表自我认同、意志和外在表现，月亮代表情感需求、内心世界和安全感。这两颗行星的互动决定了内外在的平衡。",
        "aspects": {
            "合相": {
                "conflict_tags": ["自我与情感融合", "过度依赖", "情感绑定", "身份认同"],
                "atmosphere": "温暖而亲密的氛围，双方感到彼此是天生的一对",
                "drama_theme": "融合与独立",
                "severity": 3,
                "is_harmonious": True,
            },
            "三分相": {
                "conflict_tags": ["情感共鸣", "相互理解", "情感支持", "温暖连接"],
                "atmosphere": "温暖和谐的氛围，双方自然地理解和支持彼此",
                "drama_theme": "和谐与支持",
                "severity": 2,
                "is_harmonious": True,
            },
            "六分相": {
                "conflict_tags": ["情感默契", "相互关心", "轻松连接", "温和支持"],
                "atmosphere": "轻松愉快的氛围，通过简单的努力就能建立深厚的情感连接",
                "drama_theme": "默契与关怀",
                "severity": 1,
                "is_harmonious": True,
            },
            "对分相": {
                "conflict_tags": ["自我表达冲突", "情感需求分歧", "内外不一致", "身份认同挑战"],
                "atmosphere": "一方需要认可，另一方需要滋养，双方可能感到对方不能满足自己的需求",
                "drama_theme": "自我与情感的平衡",
                "severity": 6,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["自我意志冲突", "情感需求矛盾", "身份认同危机", "内在分裂"],
                "atmosphere": "自我意志与情感需求之间的持续拉锯，双方都感到被误解",
                "drama_theme": "整合与成长",
                "severity": 7,
                "is_harmonious": False,
            }
        }
    },
    ("金星", "火星"): {
        "conflict_theme": "爱与欲望",
        "base_severity": 5,
        "description": "金星代表爱、美、和谐与价值观，火星代表行动、欲望、激情与冲动。这两颗行星的互动决定了浪漫关系中的吸引力与张力。",
        "aspects": {
            "合相": {
                "conflict_tags": ["致命吸引", "强烈情欲", "爱与欲望交织", "激情碰撞"],
                "atmosphere": "空气中充满浪漫和激情，双方之间有难以抗拒的吸引力",
                "drama_theme": "爱与欲望",
                "severity": 4,
                "is_harmonious": True,
            },
            "三分相": {
                "conflict_tags": ["浪漫吸引", "和谐激情", "甜蜜爱意", "自然吸引"],
                "atmosphere": "浪漫吸引力和谐流动，关系中充满甜蜜的激情",
                "drama_theme": "和谐的激情",
                "severity": 2,
                "is_harmonious": True,
            },
            "六分相": {
                "conflict_tags": ["浪漫默契", "轻松吸引", "温和激情", "愉快互动"],
                "atmosphere": "通过积极的表达，可以轻松增进彼此的吸引力",
                "drama_theme": "轻松的浪漫",
                "severity": 1,
                "is_harmonious": True,
            },
            "对分相": {
                "conflict_tags": ["致命吸引", "爱与行动对立", "表达差异", "吸引力与排斥"],
                "atmosphere": "这种张力既吸引又挑战，双方感到被对方吸引但又难以达成一致",
                "drama_theme": "对立的吸引",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["沟通不畅", "爱与行动摩擦", "表达冲突", "欲望与满足"],
                "atmosphere": "爱与行动可能产生摩擦，双方对爱的表达方式有不同期待",
                "drama_theme": "激情与成长",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("太阳", "冥王星"): {
        "conflict_theme": "身份与权力",
        "base_severity": 7,
        "description": "太阳代表自我认同和核心意志，冥王星代表深度转化和权力控制。这两颗行星的互动会引发身份认同的深刻危机与转化。",
        "aspects": {
            "合相": {
                "conflict_tags": ["权力意志", "深度转化", "控制欲", "身份认同危机"],
                "atmosphere": "强烈而深刻的能量，关系可能带来彻底的个人转化",
                "drama_theme": "转化与重生",
                "severity": 8,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["权力对抗", "深度冲突", "控制与反抗", "身份认同对立"],
                "atmosphere": "双方都感到对方在挑战自己的核心身份，权力斗争持续存在",
                "drama_theme": "身份与权力",
                "severity": 8,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["权力斗争", "身份认同危机", "无意识控制", "深层冲突"],
                "atmosphere": "持续的紧张感，双方都感到需要维护自己的身份和权力",
                "drama_theme": "身份整合",
                "severity": 9,
                "is_harmonious": False,
            }
        }
    },
    ("月亮", "冥王星"): {
        "conflict_theme": "情感深度",
        "base_severity": 6,
        "description": "月亮代表情感需求和安全感，冥王星代表深度转化和潜意识力量。这两颗行星的互动会引发情感层面的深刻体验和转化。",
        "aspects": {
            "合相": {
                "conflict_tags": ["深度情感", "情感控制", "心理转化", "情感绑架"],
                "atmosphere": "情感深度极高，但也可能伴随着控制欲和情感操纵",
                "drama_theme": "情感深度",
                "severity": 7,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["情感对立", "潜意识冲突", "情感操纵", "深度不信任"],
                "atmosphere": "情感暗流涌动，双方可能感到被对方的情绪淹没或控制",
                "drama_theme": "情感融合",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["情感控制", "信任危机", "无意识创伤", "情感爆发"],
                "atmosphere": "情感层面的紧张和不信任，可能引发深层的心理防御",
                "drama_theme": "情感疗愈",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("水星", "土星"): {
        "conflict_theme": "沟通障碍",
        "base_severity": 5,
        "description": "水星代表思维、沟通和表达，土星代表限制、责任和严肃。这两颗行星的互动可能导致沟通不畅或思维受限。",
        "aspects": {
            "合相": {
                "conflict_tags": ["思维严谨", "表达克制", "严肃沟通", "深度思考"],
                "atmosphere": "沟通方式严肃而谨慎，可能显得缺乏灵活性",
                "drama_theme": "责任与表达",
                "severity": 4,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["沟通障碍", "思维对立", "表达受限", "互相指责"],
                "atmosphere": "双方在沟通方式上存在根本差异，可能导致误解和争执",
                "drama_theme": "理解与误解",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["沟通不畅", "思维受阻", "表达困难", "负面思维"],
                "atmosphere": "沟通容易产生误解，双方可能感到对方不理解自己",
                "drama_theme": "突破限制",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("金星", "土星"): {
        "conflict_theme": "情感压抑",
        "base_severity": 6,
        "description": "金星代表爱、美与和谐，土星代表限制、责任与严肃。这两颗行星的互动可能导致情感表达受限或关系中缺乏温暖。",
        "aspects": {
            "合相": {
                "conflict_tags": ["情感克制", "责任重于情感", "严肃关系", "忠诚但缺乏温暖"],
                "atmosphere": "关系中责任和承诺大于浪漫表达，可能显得过于严肃",
                "drama_theme": "责任与爱",
                "severity": 5,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["情感隔阂", "责任与爱的对立", "亲密障碍", "互相指责"],
                "atmosphere": "双方在情感表达和责任承担上存在对立，关系可能感到压抑",
                "drama_theme": "爱与责任的平衡",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["情感压抑", "关系障碍", "表达受阻", "不信任"],
                "atmosphere": "情感表达受到限制，可能导致关系中的冷淡或不信任",
                "drama_theme": "释放情感",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("火星", "土星"): {
        "conflict_theme": "行动受阻",
        "base_severity": 7,
        "description": "火星代表行动、欲望和冲动，土星代表限制、责任和延迟。这两颗行星的互动会产生行动与限制之间的张力。",
        "aspects": {
            "合相": {
                "conflict_tags": ["行动受限", "意志坚韧", "挫折与坚持", "缓慢但坚定"],
                "atmosphere": "行动力被责任和限制所约束，可能感到压抑但持久",
                "drama_theme": "坚持与突破",
                "severity": 6,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["行动对立", "意志冲突", "压抑与爆发", "互相阻碍"],
                "atmosphere": "双方在行动方式和节奏上存在根本对立，可能产生强烈的冲突",
                "drama_theme": "自由与责任",
                "severity": 8,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["行动受阻", "意志冲突", "挫折感", "冲动与压抑"],
                "atmosphere": "行动欲望与现实限制产生冲突，可能导致沮丧或爆发",
                "drama_theme": "突破阻碍",
                "severity": 9,
                "is_harmonious": False,
            }
        }
    },
    ("天王星", "土星"): {
        "conflict_theme": "变革与稳定",
        "base_severity": 6,
        "description": "天王星代表变革、突破和自由，土星代表稳定、责任和传统。这两颗行星的互动代表了旧与新、传统与变革之间的张力。",
        "aspects": {
            "合相": {
                "conflict_tags": ["变革与稳定共存", "谨慎创新", "传统中的突破", "渐进式改变"],
                "atmosphere": "在稳定中寻求突破，可能感到新旧力量的拉扯",
                "drama_theme": "渐进式变革",
                "severity": 5,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["变革与传统对立", "自由与责任冲突", "革命与保守", "新旧对立"],
                "atmosphere": "一方追求变革和自由，另一方坚持传统和稳定，产生强烈的对立",
                "drama_theme": "传统与变革",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["变革受阻", "打破限制", "突发变化", "秩序崩溃"],
                "atmosphere": "传统结构受到突发变革的冲击，可能产生混乱或解放",
                "drama_theme": "突破传统",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    },
    ("太阳", "土星"): {
        "conflict_theme": "自我限制",
        "base_severity": 5,
        "description": "太阳代表自我认同和核心意志，土星代表限制、责任和严肃。这两颗行星的互动可能导致自我表达受限或感到被评判。",
        "aspects": {
            "合相": {
                "conflict_tags": ["自我克制", "责任感强", "严肃自我", "成就但缺乏快乐"],
                "atmosphere": "自我表达受到责任和严肃态度的约束，可能显得过于稳重",
                "drama_theme": "责任与自我",
                "severity": 4,
                "is_harmonious": False,
            },
            "对分相": {
                "conflict_tags": ["自我表达受阻", "感到被限制", "权威冲突", "压抑自我"],
                "atmosphere": "双方在自我表达和责任承担上存在对立，可能感到被对方限制",
                "drama_theme": "自我与责任",
                "severity": 7,
                "is_harmonious": False,
            },
            "四分相": {
                "conflict_tags": ["自我价值低落", "感到被评判", "表达受阻", "自信不足"],
                "atmosphere": "自我表达受到限制，可能导致自卑或害怕被评判",
                "drama_theme": "接纳自我",
                "severity": 8,
                "is_harmonious": False,
            }
        }
    }
}


def _get_standardized_key(planet_a: str, planet_b: str) -> Optional[Tuple[str, str]]:
    """获取标准化的行星对key，支持双向匹配"""
    if (planet_a, planet_b) in KEY_CONFLICT_PLANET_PAIRS:
        return (planet_a, planet_b)
    if (planet_b, planet_a) in KEY_CONFLICT_PLANET_PAIRS:
        return (planet_b, planet_a)
    return None


def detect_conflict_aspects(
    synastry_aspects: List[Dict[str, Any]],
    orb_threshold: float = 5.0
) -> List[ConflictAspect]:
    """
    检测合盘相位中的关键冲突相位
    
    Args:
        synastry_aspects: 合盘相位列表（来自calculate_synastry_aspects）
        orb_threshold: 容许度阈值（弧分），超过此值的相位不被视为关键相位
    
    Returns:
        检测到的冲突相位列表
    """
    detected_conflicts: List[ConflictAspect] = []
    
    for aspect in synastry_aspects:
        planet_a = aspect.get("planet_a", "")
        planet_b = aspect.get("planet_b", "")
        aspect_type = aspect.get("aspect", "")
        orb_arcminutes = aspect.get("orb_arcminutes", 0.0)
        nature = aspect.get("nature", "neutral")
        
        if orb_arcminutes > orb_threshold:
            continue
        
        key = _get_standardized_key(planet_a, planet_b)
        if not key:
            continue
        
        planet_pair_info = KEY_CONFLICT_PLANET_PAIRS[key]
        aspects_info = planet_pair_info.get("aspects", {})
        
        if aspect_type in aspects_info:
            aspect_info = aspects_info[aspect_type]
            
            conflict = ConflictAspect(
                planet_a=planet_a,
                planet_b=planet_b,
                aspect_type=aspect_type,
                conflict_tags=aspect_info.get("conflict_tags", []),
                atmosphere=aspect_info.get("atmosphere", ""),
                drama_theme=aspect_info.get("drama_theme", ""),
                severity=aspect_info.get("severity", 5),
                description=planet_pair_info.get("description", ""),
                is_harmonious=aspect_info.get("is_harmonious", False),
                orb_arcminutes=orb_arcminutes
            )
            
            detected_conflicts.append(conflict)
    
    detected_conflicts.sort(key=lambda x: x.severity, reverse=True)
    
    return detected_conflicts


def analyze_conflict_intensity(conflicts: List[ConflictAspect]) -> Dict[str, Any]:
    """
    分析冲突相位的整体强度
    
    Args:
        conflicts: 检测到的冲突相位列表
    
    Returns:
        包含强度分析的字典
    """
    if not conflicts:
        return {
            "total_severity": 0,
            "average_severity": 0,
            "conflict_level": "无冲突",
            "conflict_level_code": 0,
            "harmonious_count": 0,
            "challenging_count": 0,
            "dominant_theme": None,
            "dominant_atmosphere": None
        }
    
    total_severity = sum(c.severity for c in conflicts)
    average_severity = total_severity / len(conflicts)
    
    harmonious_count = sum(1 for c in conflicts if c.is_harmonious)
    challenging_count = len(conflicts) - harmonious_count
    
    theme_counts: Dict[str, int] = {}
    for c in conflicts:
        for tag in c.conflict_tags:
            theme_counts[tag] = theme_counts.get(tag, 0) + 1
    
    dominant_tag = max(theme_counts.items(), key=lambda x: x[1])[0] if theme_counts else None
    
    atmosphere_list = [c.atmosphere for c in conflicts if c.atmosphere]
    dominant_atmosphere = atmosphere_list[0] if atmosphere_list else None
    
    if average_severity >= 8:
        conflict_level = "极度紧张"
        conflict_level_code = 4
    elif average_severity >= 6:
        conflict_level = "高度紧张"
        conflict_level_code = 3
    elif average_severity >= 4:
        conflict_level = "中度紧张"
        conflict_level_code = 2
    elif average_severity >= 2:
        conflict_level = "轻度紧张"
        conflict_level_code = 1
    else:
        conflict_level = "和谐"
        conflict_level_code = 0
    
    return {
        "total_severity": total_severity,
        "average_severity": round(average_severity, 2),
        "conflict_level": conflict_level,
        "conflict_level_code": conflict_level_code,
        "harmonious_count": harmonious_count,
        "challenging_count": challenging_count,
        "dominant_tag": dominant_tag,
        "dominant_atmosphere": dominant_atmosphere,
        "all_tags": list(theme_counts.keys())
    }


def extract_conflict_context_for_ai(
    conflicts: List[ConflictAspect],
    intensity_analysis: Dict[str, Any],
    person_a_name: str = "角色A",
    person_b_name: str = "角色B"
) -> Dict[str, Any]:
    """
    提取用于AI剧情生成的冲突上下文
    
    Args:
        conflicts: 冲突相位列表
        intensity_analysis: 强度分析结果
        person_a_name: 角色A名称
        person_b_name: 角色B名称
    
    Returns:
        格式化的冲突上下文，可直接用于AI提示词
    """
    if not conflicts:
        return {
            "has_conflict": False,
            "summary": f"{person_a_name}和{person_b_name}在广场相遇，没有发现明显的冲突相位。关系基础和谐，但也可能因此缺乏戏剧性张力。",
            "themes": [],
            "atmosphere": "平静的广场氛围，两人相遇时没有明显的紧张感",
            "conflict_details": [],
            "intensity": {"level": "和谐", "code": 0}
        }
    
    conflict_details = []
    for i, c in enumerate(conflicts, 1):
        detail = {
            "phase": i,
            "planet_pair": f"{c.planet_a}与{c.planet_b}",
            "aspect_type": c.aspect_type,
            "drama_theme": c.drama_theme,
            "atmosphere": c.atmosphere,
            "conflict_tags": c.conflict_tags,
            "severity": c.severity,
            "description": c.description,
            "is_harmonious": c.is_harmonious
        }
        conflict_details.append(detail)
    
    all_tags = intensity_analysis.get("all_tags", [])
    dominant_tag = intensity_analysis.get("dominant_tag")
    
    themes_list = []
    for c in conflicts:
        if c.drama_theme not in themes_list:
            themes_list.append(c.drama_theme)
    
    atmosphere_parts = []
    for c in conflicts[:3]:
        if c.atmosphere:
            atmosphere_parts.append(c.atmosphere)
    
    combined_atmosphere = "。".join(atmosphere_parts) if atmosphere_parts else "紧张而充满戏剧性的氛围"
    
    summary_parts = []
    summary_parts.append(f"{person_a_name}和{person_b_name}在广场相遇。")
    
    if dominant_tag:
        summary_parts.append(f"两人之间最显著的特征是「{dominant_tag}」。")
    
    if intensity_analysis["challenging_count"] > 0:
        summary_parts.append(f"检测到{intensity_analysis['challenging_count']}个紧张相位，整体关系强度为「{intensity_analysis['conflict_level']}」。")
    
    if intensity_analysis["harmonious_count"] > 0:
        summary_parts.append(f"同时存在{intensity_analysis['harmonious_count']}个和谐相位，为关系提供积极基础。")
    
    summary = "".join(summary_parts)
    
    return {
        "has_conflict": True,
        "summary": summary,
        "themes": themes_list,
        "atmosphere": combined_atmosphere,
        "conflict_details": conflict_details,
        "all_tags": all_tags,
        "dominant_tag": dominant_tag,
        "intensity": {
            "level": intensity_analysis["conflict_level"],
            "code": intensity_analysis["conflict_level_code"],
            "average_severity": intensity_analysis["average_severity"],
            "total_severity": intensity_analysis["total_severity"],
            "harmonious_count": intensity_analysis["harmonious_count"],
            "challenging_count": intensity_analysis["challenging_count"]
        }
    }