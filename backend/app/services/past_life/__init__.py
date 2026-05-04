"""
前世故事模块 - 统一导出入口

模块结构:
- config.py: 配置常量（主题、关系类型、价格）
- analysis_service.py: 分析服务（主题判断、关系判断）
- story_service.py: AI故事生成服务
- data_service.py: 数据服务（记录管理、分页、分享）
- payment_service.py: 支付服务（订单、升级）

重构说明:
1. 拆分了原900+行的上帝文件为5个模块
2. 修复了假分页问题：data_service.py现在返回真实的total计数
3. 修复了并发计数问题：使用数据库原子操作更新share_count
4. 修复了订单幂等问题：防止重复创建订单和重复处理支付回调
"""

from .config import (
    PAST_LIFE_THEME_CONFIG,
    PAST_LIFE_RELATIONSHIP_CONFIG,
    PAST_LIFE_PRICE,
    PAST_LIFE_SYNASTRY_PRICE,
    ELEMENT_SIGN_MAPPING,
    QUALITY_SIGN_MAPPING,
)

from .analysis_service import (
    safe_get,
    extract_core_planets,
    _get_element_by_sign,
    _get_quality_by_sign,
    determine_past_life_theme,
    determine_past_life_relationship,
)

from .story_service import (
    build_past_life_prompt,
    build_synastry_past_life_prompt,
    generate_past_life_story,
    generate_synastry_past_life_story,
)

from .data_service import (
    generate_share_code,
    get_or_create_past_life_record,
    get_or_create_synastry_past_life_record,
    get_user_past_life_records,
    get_user_synastry_past_life_records,
    get_past_life_by_share_code,
    get_single_record_by_id,
    get_synastry_record_by_id,
    record_to_dict,
    synastry_record_to_dict,
)

from .payment_service import (
    create_past_life_order,
    upgrade_to_deep_version,
    process_payment_callback,
    get_order_status,
)

__all__ = [
    "PAST_LIFE_THEME_CONFIG",
    "PAST_LIFE_RELATIONSHIP_CONFIG",
    "PAST_LIFE_PRICE",
    "PAST_LIFE_SYNASTRY_PRICE",
    "ELEMENT_SIGN_MAPPING",
    "QUALITY_SIGN_MAPPING",
    "safe_get",
    "extract_core_planets",
    "_get_element_by_sign",
    "_get_quality_by_sign",
    "determine_past_life_theme",
    "determine_past_life_relationship",
    "build_past_life_prompt",
    "build_synastry_past_life_prompt",
    "generate_past_life_story",
    "generate_synastry_past_life_story",
    "generate_share_code",
    "get_or_create_past_life_record",
    "get_or_create_synastry_past_life_record",
    "get_user_past_life_records",
    "get_user_synastry_past_life_records",
    "get_past_life_by_share_code",
    "get_single_record_by_id",
    "get_synastry_record_by_id",
    "record_to_dict",
    "synastry_record_to_dict",
    "create_past_life_order",
    "upgrade_to_deep_version",
    "process_payment_callback",
    "get_order_status",
]
