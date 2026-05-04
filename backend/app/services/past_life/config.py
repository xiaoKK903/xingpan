"""
前世故事 - 配置常量
"""

PAST_LIFE_THEME_CONFIG = {
    "warrior": {
        "name": "江湖侠士",
        "icon": "⚔️",
        "keywords": ["勇气", "冒险", "守护", "战斗", "自由"],
        "core_planets": ["火星", "太阳", "木星"],
        "description": "前世是一位行走江湖的侠士，锄强扶弱，快意恩仇"
    },
    "scholar": {
        "name": "文人墨客",
        "icon": "📜",
        "keywords": ["智慧", "学习", "思考", "表达", "知识"],
        "core_planets": ["水星", "月亮", "天王星"],
        "description": "前世是一位博学鸿儒，著书立说，传道授业"
    },
    "artist": {
        "name": "艺术大家",
        "icon": "🎨",
        "keywords": ["美感", "创造", "和谐", "爱", "表达"],
        "core_planets": ["金星", "海王星", "月亮"],
        "description": "前世是一位艺术天才，琴棋书画，才情横溢"
    },
    "royal": {
        "name": "王室贵族",
        "icon": "👑",
        "keywords": ["责任", "权力", "结构", "地位", "荣耀"],
        "core_planets": ["土星", "太阳", "冥王星"],
        "description": "前世是一位王室成员，肩负重任，执掌一方"
    },
    "monk": {
        "name": "修行隐士",
        "icon": "🧘",
        "keywords": ["灵性", "内省", "超脱", "修行", "智慧"],
        "core_planets": ["海王星", "冥王星", "土星"],
        "description": "前世是一位修行者，深山问道，寻求真谛"
    },
    "merchant": {
        "name": "富商巨贾",
        "icon": "💰",
        "keywords": ["资源", "价值", "积累", "交易", "务实"],
        "core_planets": ["金星", "土星", "水星"],
        "description": "前世是一位成功商人，财源广进，乐善好施"
    },
    "healer": {
        "name": "神医济世",
        "icon": "💚",
        "keywords": ["疗愈", "关怀", "服务", "健康", "净化"],
        "core_planets": ["冥王星", "海王星", "月亮"],
        "description": "前世是一位医者，救死扶伤，仁心仁术"
    },
    "adventurer": {
        "name": "探险家",
        "icon": "🧭",
        "keywords": ["探索", "自由", "远方", "知识", "冒险"],
        "core_planets": ["木星", "天王星", "火星"],
        "description": "前世是一位探险家，跋山涉水，寻觅未知"
    }
}

PAST_LIFE_RELATIONSHIP_CONFIG = {
    "lovers": {
        "name": "宿命恋人",
        "icon": "💕",
        "keywords": ["深爱", "羁绊", "前世姻缘", "遗憾", "重逢"],
        "key_aspects": [("金星", "火星"), ("金星", "冥王星"), ("太阳", "月亮")],
        "description": "前世是刻骨铭心的恋人，这份缘分延续至今"
    },
    "mentor": {
        "name": "师徒传承",
        "icon": "👨‍🏫",
        "keywords": ["教导", "传承", "指引", "恩情", "成长"],
        "key_aspects": [("土星", "太阳"), ("土星", "水星"), ("木星", "太阳")],
        "description": "前世是师徒关系，一方给予智慧，一方虚心学习"
    },
    "rival": {
        "name": "宿敌羁绊",
        "icon": "⚔️",
        "keywords": ["竞争", "较量", "成长", "宿命", "对手"],
        "key_aspects": [("火星", "土星"), ("火星", "冥王星"), ("太阳", "土星")],
        "description": "前世是势均力敌的对手，在竞争中共同成长"
    },
    "soulmate": {
        "name": "灵魂知己",
        "icon": "✨",
        "keywords": ["理解", "共鸣", "默契", "知己", "精神"],
        "key_aspects": [("月亮", "月亮"), ("水星", "水星"), ("天王星", "金星")],
        "description": "前世是灵魂契合的知己，无需言语便能心意相通"
    },
    "family": {
        "name": "前世家人",
        "icon": "👨‍👩‍👧‍👦",
        "keywords": ["亲情", "血脉", "守护", "温暖", "陪伴"],
        "key_aspects": [("月亮", "金星"), ("月亮", "太阳"), ("土星", "月亮")],
        "description": "前世是血脉相连的家人，这份亲情跨越时空"
    },
    "comrade": {
        "name": "生死之交",
        "icon": "🤝",
        "keywords": ["并肩", "信任", "勇气", "战友", "义气"],
        "key_aspects": [("火星", "木星"), ("太阳", "木星"), ("火星", "天王星")],
        "description": "前世是并肩作战的战友，生死与共，同甘共苦"
    },
    "stranger": {
        "name": "命中邂逅",
        "icon": "🌟",
        "keywords": ["偶遇", "缘分", "新开始", "惊喜", "未知"],
        "key_aspects": [],
        "description": "前世虽无交集，但今生的相遇是命运的安排"
    }
}

PAST_LIFE_PRICE = 9.9
PAST_LIFE_SYNASTRY_PRICE = 9.9

ELEMENT_SIGN_MAPPING = {
    "火象": ["白羊座", "狮子座", "射手座"],
    "土象": ["金牛座", "处女座", "摩羯座"],
    "风象": ["双子座", "天秤座", "水瓶座"],
    "水象": ["巨蟹座", "天蝎座", "双鱼座"]
}

QUALITY_SIGN_MAPPING = {
    "基本": ["白羊座", "巨蟹座", "天秤座", "摩羯座"],
    "固定": ["金牛座", "狮子座", "天蝎座", "水瓶座"],
    "变动": ["双子座", "处女座", "射手座", "双鱼座"]
}


STORY_CARD_TEMPLATE_CONFIG = {
    "soulmate_knight": {
        "name": "前世并肩骑士",
        "icon": "⚔️",
        "rarity": "legendary",
        "rarity_name": "传说",
        "keywords": ["并肩作战", "生死之交", "骑士精神", "荣耀"],
        "match_conditions": {
            "required_aspects": [("火星", "木星"), ("太阳", "木星")],
            "compatibility_threshold": 85,
            "dominant_element": "fire"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：前世并肩的荣耀骑士",
        "subheadline_template": "在古老的战场上，你们曾是并肩作战的生死之交",
        "story_templates": [
            {
                "opening": "千年之前，在那片被战火染红的大地上，{{person_a}} 与 {{person_b}} 是同生共死的骑士兄弟。",
                "middle": "每一场战役，你们都背靠背作战，用剑与盾守护着彼此的后背。在最艰难的时刻，{{person_a}} 曾为 {{person_b}} 挡下致命一击，而 {{person_b}} 也曾在绝境中救出 {{person_a}}。",
                "closing": "这份超越生死的羁绊，跨越了时空的界限，在今生再次相遇。你们无需言语，便能感受到那份深刻的信任与默契。"
            },
            {
                "opening": "遥远的中世纪，{{person_a}} 是王国的守护骑士，而 {{person_b}} 是其最忠诚的侍从。",
                "middle": "在无数次的冒险与征战中，你们建立了超越身份的友谊。{{person_a}} 教会 {{person_b}} 骑士之道，而 {{person_b}} 的忠诚与智慧也成为 {{person_a}} 最坚实的后盾。",
                "closing": "这份师徒之情与战友情谊，在时间的长河中沉淀，化作今生再次相遇的奇妙缘分。"
            }
        ]
    },
    "confidant": {
        "name": "知己挚友",
        "icon": "💫",
        "rarity": "epic",
        "rarity_name": "史诗",
        "keywords": ["心灵相通", "知己", "精神共鸣", "理解"],
        "match_conditions": {
            "required_aspects": [("月亮", "月亮"), ("水星", "水星"), ("金星", "天王星")],
            "compatibility_threshold": 80,
            "match_type": "soulmate"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：跨越时空的灵魂知己",
        "subheadline_template": "无需言语，你们的灵魂早已相识",
        "story_templates": [
            {
                "opening": "在古老的东方王朝，{{person_a}} 是一位隐居山林的智者，而 {{person_b}} 是唯一能真正理解其思想的知己。",
                "middle": "每个月圆之夜，你们都会在竹林中对坐，品茶论道。无需过多言语，一个眼神便能传递千言万语。{{person_a}} 的深邃思想，只有 {{person_b}} 能真正领悟；而 {{person_b}} 内心的细腻，也只有 {{person_a}} 能深深理解。",
                "closing": "这份超越时空的心灵契合，在今生化作无需解释的默契。你们是彼此灵魂的镜子，映照出最真实的自己。"
            },
            {
                "opening": "文艺复兴时期的佛罗伦萨，{{person_a}} 与 {{person_b}} 是两位惺惺相惜的艺术家。",
                "middle": "在艺术的道路上，你们是彼此最严格的批评者，也是最坚定的支持者。{{person_a}} 的创意能激发 {{person_b}} 的灵感，而 {{person_b}} 的细腻能完善 {{person_a}} 的构思。",
                "closing": "这份对美的共同追求与深刻理解，跨越了几个世纪，在今生再度绽放。"
            }
        ]
    },
    "rival_turns_friend": {
        "name": "宿敌化挚友",
        "icon": "⚡",
        "rarity": "epic",
        "rarity_name": "史诗",
        "keywords": ["竞争", "成长", "化敌为友", "张力"],
        "match_conditions": {
            "required_aspects": [("火星", "土星"), ("火星", "冥王星"), ("太阳", "土星")],
            "compatibility_threshold": 65,
            "match_type": "challenging"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：从宿敌到挚友的传奇",
        "subheadline_template": "在竞争中，你们成就了彼此",
        "story_templates": [
            {
                "opening": "在古老的武道圣地，{{person_a}} 与 {{person_b}} 是门派中最耀眼的两颗新星，也是彼此最强劲的对手。",
                "middle": "每一次比试，都让你们更加了解对方的招式与心意。在无数次的较量中，{{person_a}} 学会了 {{person_b}} 的坚韧，而 {{person_b}} 也领悟了 {{person_a}} 的灵动。当外敌入侵时，你们放下成见，联手御敌，在生死之间建立了真正的友谊。",
                "closing": "这份从竞争中诞生的深厚情谊，在今生化作独特的化学反应。你们依然会彼此挑战，但这份挑战只会让双方更加耀眼。"
            }
        ]
    },
    "star_crossed_lovers": {
        "name": "宿命恋人",
        "icon": "💕",
        "rarity": "legendary",
        "rarity_name": "传说",
        "keywords": ["宿命", "深爱", "遗憾", "重逢", "前世姻缘"],
        "match_conditions": {
            "required_aspects": [("金星", "火星"), ("金星", "冥王星"), ("太阳", "月亮")],
            "compatibility_threshold": 88,
            "dominant_element": "water"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：跨越时空的宿命恋人",
        "subheadline_template": "前世未了的情缘，今生再续",
        "story_templates": [
            {
                "opening": "在樱花飘落的平安时代，{{person_a}} 是贵族家的公子，而 {{person_b}} 是其倾心不已却无法相守的恋人。",
                "middle": "身份的隔阂、家族的压力，让这份爱情充满了艰辛。但每一次秘密的相遇，每一封深情的书信，都让你们的羁绊更加深厚。在生命的最后时刻，你们许下誓言：若有来生，定要跨越一切阻碍，相守相依。",
                "closing": "这份跨越千年的誓言，在今生化作宿命般的相遇。当你们的目光再次交汇时，那份熟悉而深刻的悸动，便是前世爱情的回响。"
            },
            {
                "opening": "战火纷飞的年代，{{person_a}} 与 {{person_b}} 在最不可能的时刻相遇相爱。",
                "middle": "命运的捉弄让你们经历了无数次的分离与重逢。每一次相聚都格外珍贵，每一次离别都痛彻心扉。但即使在最黑暗的时刻，你们心中那份爱意从未熄灭。",
                "closing": "前世未能圆满的爱情，在今生获得了重新开始的机会。这份穿越时空的深情，让你们的相遇注定不凡。"
            }
        ]
    },
    "mentor_student": {
        "name": "师徒传承",
        "icon": "📖",
        "rarity": "rare",
        "rarity_name": "稀有",
        "keywords": ["教导", "传承", "指引", "恩情", "成长"],
        "match_conditions": {
            "required_aspects": [("土星", "太阳"), ("土星", "水星"), ("木星", "太阳")],
            "compatibility_threshold": 70,
            "match_type": "complementary"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：前世师徒的智慧传承",
        "subheadline_template": "一方给予智慧，一方虚心学习",
        "story_templates": [
            {
                "opening": "在古老的书院中，{{person_a}} 是德高望重的夫子，而 {{person_b}} 是其最得意的门生。",
                "middle": "{{person_a}} 将毕生所学倾囊相授，不仅教授学问，更传授为人处世的道理。而 {{person_b}} 的聪慧与好学，也让 {{person_a}} 看到了自己思想的延续与升华。在多年的相处中，你们建立了超越师生的深厚情谊。",
                "closing": "这份智慧的传承与情谊，在今生化作独特的缘分。你们会发现，在某些领域，一方总能给予另一方恰到好处的指引与启发。"
            }
        ]
    },
    "comrades_in_arms": {
        "name": "生死之交",
        "icon": "🤝",
        "rarity": "rare",
        "rarity_name": "稀有",
        "keywords": ["并肩", "信任", "勇气", "战友", "义气"],
        "match_conditions": {
            "required_aspects": [("火星", "木星"), ("太阳", "木星"), ("火星", "天王星")],
            "compatibility_threshold": 75,
            "dominant_element": "fire"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：同生共死的战友",
        "subheadline_template": "在最艰难的时刻，你们是彼此最坚实的后盾",
        "story_templates": [
            {
                "opening": "在那段激情燃烧的岁月，{{person_a}} 与 {{person_b}} 是同一战壕的战友。",
                "middle": "在枪林弹雨中，你们用生命守护着彼此。{{person_a}} 曾在危急关头救下 {{person_b}}，而 {{person_b}} 也曾在寒冬中将最后的口粮分给 {{person_a}}。那些共同经历的生死考验，让你们的情谊坚如钢铁。",
                "closing": "这份用生命铸就的情谊，在今生化作无需言表的信任。当一方需要帮助时，另一方总会毫不犹豫地伸出援手。"
            }
        ]
    },
    "familiar_strangers": {
        "name": "似曾相识",
        "icon": "🌟",
        "rarity": "common",
        "rarity_name": "普通",
        "keywords": ["偶遇", "缘分", "新开始", "惊喜", "熟悉感"],
        "match_conditions": {
            "required_aspects": [],
            "compatibility_threshold": 50
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：命中注定的邂逅",
        "subheadline_template": "初见便觉熟悉，仿佛早已相识",
        "story_templates": [
            {
                "opening": "前世，你们曾在人生的某个路口擦肩而过，或是在同一片星空下仰望过同一颗星。",
                "middle": "虽然没有深刻的交集，但命运的丝线已经将你们悄然相连。也许在某个市集上，你们曾交换过一个微笑；也许在某个旅途中，你们曾短暂同行。",
                "closing": "这些微妙的缘分，在今生化作初见时的熟悉感。你们的相遇，是命运安排的新开始，充满了无限可能。"
            }
        ]
    },
    "mystic_bond": {
        "name": "神秘羁绊",
        "icon": "🔮",
        "rarity": "epic",
        "rarity_name": "史诗",
        "keywords": ["神秘", "直觉", "灵性连接", "第六感", "超越"],
        "match_conditions": {
            "required_aspects": [("海王星", "月亮"), ("冥王星", "月亮"), ("天王星", "海王星")],
            "compatibility_threshold": 80,
            "dominant_element": "water"
        },
        "headline_template": "{{person_a}} 与 {{person_b}}：超越言语的神秘羁绊",
        "subheadline_template": "有一种连接，超越了言语与理性",
        "story_templates": [
            {
                "opening": "在古老的神秘学派中，{{person_a}} 与 {{person_b}} 是一同探索灵界奥秘的同道中人。",
                "middle": "在冥想与修行中，你们发现彼此的意识能够产生奇妙的共鸣。有时无需开口，便能感知对方的思绪与情绪。这种超越言语的连接，让你们在灵性的道路上携手并进。",
                "closing": "这份神秘的灵性连接，在今生化作难以言喻的直觉与默契。你们常常能在对方开口之前，便已明了其心意。"
            }
        ]
    }
}


STORY_CARD_RARITY_CONFIG = {
    "common": {
        "name": "普通",
        "color": "#94a3b8",
        "glow_color": "rgba(148, 163, 184, 0.3)",
        "probability": 0.45,
        "share_bonus": 1
    },
    "rare": {
        "name": "稀有",
        "color": "#3b82f6",
        "glow_color": "rgba(59, 130, 246, 0.4)",
        "probability": 0.30,
        "share_bonus": 2
    },
    "epic": {
        "name": "史诗",
        "color": "#a855f7",
        "glow_color": "rgba(168, 85, 247, 0.5)",
        "probability": 0.18,
        "share_bonus": 3
    },
    "legendary": {
        "name": "传说",
        "color": "#f59e0b",
        "glow_color": "rgba(245, 158, 11, 0.6)",
        "probability": 0.07,
        "share_bonus": 5
    }
}


ASPECT_NATURE_MAPPING = {
    "三分相": "harmonious",
    "六分相": "harmonious",
    "合相": "neutral",
    "四分相": "challenging",
    "对分相": "challenging"
}


DOMINANT_ELEMENT_SIGN_MAPPING = {
    "fire": ["白羊座", "狮子座", "射手座"],
    "earth": ["金牛座", "处女座", "摩羯座"],
    "air": ["双子座", "天秤座", "水瓶座"],
    "water": ["巨蟹座", "天蝎座", "双鱼座"]
}
