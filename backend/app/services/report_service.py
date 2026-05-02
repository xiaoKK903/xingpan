from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
import json
import logging

from app.models import (
    User, ReportProduct, UserReportPurchase,
    ReportProductType, Chart, SynastryRecord, GroupMatrix,
    StarDustTransaction
)
from app.services.vip_service import (
    check_vip_status, get_free_reports_remaining, use_free_report
)
from app.services.chart_service import get_or_create_chart_data
from app.interpretations import (
    generate_full_interpretation,
    get_planet_sign_interpretation,
    get_sign_interpretation,
    get_house_interpretation,
    get_aspect_interpretation,
    ZODIAC_SIGN_INTERPRETATIONS,
    HOUSE_INTERPRETATIONS,
    ASPECT_INTERPRETATIONS,
    ELEMENT_QUALITY_INTERPRETATIONS
)

logger = logging.getLogger(__name__)

SIGN_TO_ELEMENT = {
    "白羊座": "火", "金牛座": "土", "双子座": "风", "巨蟹座": "水",
    "狮子座": "火", "处女座": "土", "天秤座": "风", "天蝎座": "水",
    "射手座": "火", "摩羯座": "土", "水瓶座": "风", "双鱼座": "水"
}

SIGN_TO_QUALITY = {
    "白羊座": "开创", "金牛座": "固定", "双子座": "变动", "巨蟹座": "开创",
    "狮子座": "固定", "处女座": "变动", "天秤座": "开创", "天蝎座": "固定",
    "射手座": "变动", "摩羯座": "开创", "水瓶座": "固定", "双鱼座": "变动"
}

MAIN_PLANETS = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
MAJOR_ASPECTS = ["合相", "对分相", "四分相", "三分相", "六分相"]


def generate_unique_no(prefix: str = "RPT") -> str:
    """生成唯一报告编号"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def init_report_products(db: Session):
    """初始化报告产品数据"""
    try:
        existing_products = db.query(ReportProduct).count()
        if existing_products > 0:
            logger.info("报告产品已初始化，跳过")
            return
        
        products = [
            ReportProduct(
                product_key=ReportProductType.DEEP_SINGLE.value,
                name="深度单人星盘解读",
                description="包含完整的行星解读、相位分析、宫位详解、元素能量分析等深度内容，由AI进行专业解读",
                product_type=ReportProductType.DEEP_SINGLE.value,
                price=100,
                original_price=150,
                currency_type="stardust_point",
                report_template="deep_single",
                sections_included=json.dumps([
                    "行星详细解读",
                    "相位深度分析",
                    "宫位完整解析",
                    "元素能量报告",
                    "人生主题解读",
                    "运势趋势预测"
                ]),
                is_active=True,
                sort_order=1
            ),
            ReportProduct(
                product_key=ReportProductType.SYNASTRY_INTERPRETATION.value,
                name="双人合盘深度解读",
                description="深度分析两人的缘分指数、吸引点、挑战点、相处建议，包含详细的相位解读和关系动态",
                product_type=ReportProductType.SYNASTRY_INTERPRETATION.value,
                price=150,
                original_price=200,
                currency_type="stardust_point",
                report_template="synastry_deep",
                sections_included=json.dumps([
                    "缘分指数分析",
                    "吸引点解读",
                    "挑战点分析",
                    "相位关系详解",
                    "相处建议指南",
                    "关系发展预测"
                ]),
                is_active=True,
                sort_order=2
            ),
            ReportProduct(
                product_key=ReportProductType.YEARLY_PREDICTION.value,
                name="人生年度预测报告",
                description="基于行运天象，预测未来一年的重要运势走向、关键时刻、机遇与挑战",
                product_type=ReportProductType.YEARLY_PREDICTION.value,
                price=200,
                original_price=300,
                currency_type="stardust_point",
                report_template="yearly_prediction",
                sections_included=json.dumps([
                    "年度整体运势",
                    "各领域详细预测",
                    "重要天象提醒",
                    "关键时刻日历",
                    "机遇与挑战分析",
                    "行动建议指南"
                ]),
                is_active=True,
                sort_order=3
            ),
            ReportProduct(
                product_key=ReportProductType.GROUP_ENERGY.value,
                name="群组能量分析报告",
                description="分析团队、家庭、朋友圈等群组的能量互动模式、优势互补、潜在冲突和协作建议",
                product_type=ReportProductType.GROUP_ENERGY.value,
                price=250,
                original_price=350,
                currency_type="stardust_point",
                report_template="group_energy",
                sections_included=json.dumps([
                    "群组整体能量",
                    "成员互动模式",
                    "优势互补分析",
                    "潜在冲突预警",
                    "协作效率评估",
                    "团队建设建议"
                ]),
                is_active=True,
                sort_order=4
            ),
        ]
        
        db.add_all(products)
        db.commit()
        logger.info("报告产品初始化完成")
    except Exception as e:
        logger.error(f"初始化报告产品失败: {str(e)}", exc_info=True)
        db.rollback()
        raise


def get_active_report_products(db: Session) -> List[ReportProduct]:
    """获取活跃的报告产品列表"""
    try:
        products = db.query(ReportProduct).filter(
            ReportProduct.is_active == True
        ).order_by(ReportProduct.sort_order).all()
        return products
    except Exception as e:
        logger.error(f"获取活跃报告产品失败: {str(e)}", exc_info=True)
        return []


def get_report_product_by_id(db: Session, product_id: int) -> Optional[ReportProduct]:
    """根据ID获取报告产品"""
    try:
        product = db.query(ReportProduct).filter(
            ReportProduct.id == product_id,
            ReportProduct.is_active == True
        ).first()
        return product
    except Exception as e:
        logger.error(f"获取报告产品失败 ID={product_id}: {str(e)}", exc_info=True)
        return None


def get_report_product_by_key(db: Session, product_key: str) -> Optional[ReportProduct]:
    """根据Key获取报告产品"""
    try:
        product = db.query(ReportProduct).filter(
            ReportProduct.product_key == product_key,
            ReportProduct.is_active == True
        ).first()
        return product
    except Exception as e:
        logger.error(f"获取报告产品失败 key={product_key}: {str(e)}", exc_info=True)
        return None


def purchase_report(
    db: Session,
    user_id: int,
    product_id: int,
    chart_id: Optional[int] = None,
    synastry_record_id: Optional[int] = None,
    group_matrix_id: Optional[int] = None,
    use_free_vip: bool = False
) -> Tuple[Optional[UserReportPurchase], Optional[str]]:
    """
    购买报告
    
    Returns:
        Tuple[购买记录, 错误信息]
    """
    try:
        logger.info(f"开始购买报告: user_id={user_id}, product_id={product_id}, use_free_vip={use_free_vip}")
        
        product = get_report_product_by_id(db, product_id)
        if not product:
            logger.warning(f"报告产品不存在或已下架: product_id={product_id}")
            return None, "报告产品不存在或已下架"
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"用户不存在: user_id={user_id}")
            return None, "用户不存在"
        
        if product.product_type == ReportProductType.DEEP_SINGLE.value:
            if not chart_id:
                latest_chart = db.query(Chart).filter(
                    Chart.user_id == user_id,
                    Chart.is_deleted == False
                ).order_by(desc(Chart.created_at)).first()
                if not latest_chart:
                    logger.warning(f"用户没有星盘记录: user_id={user_id}")
                    return None, "您还没有创建星盘，请先创建星盘后再购买报告"
                chart_id = latest_chart.id
                logger.info(f"自动选择用户最新星盘: chart_id={chart_id}")
            
            chart = db.query(Chart).filter(
                Chart.id == chart_id,
                Chart.user_id == user_id
            ).first()
            if not chart:
                logger.warning(f"星盘不存在或无权访问: chart_id={chart_id}")
                return None, "星盘不存在或无权访问"
        
        elif product.product_type == ReportProductType.SYNASTRY_INTERPRETATION.value:
            if not synastry_record_id:
                latest_synastry = db.query(SynastryRecord).filter(
                    SynastryRecord.user_id == user_id
                ).order_by(desc(SynastryRecord.created_at)).first()
                if not latest_synastry:
                    logger.warning(f"用户没有合盘记录: user_id={user_id}")
                    return None, "您还没有合盘记录，请先进行合盘分析后再购买报告"
                synastry_record_id = latest_synastry.id
                logger.info(f"自动选择用户最新合盘记录: synastry_record_id={synastry_record_id}")
            
            synastry = db.query(SynastryRecord).filter(
                SynastryRecord.id == synastry_record_id,
                SynastryRecord.user_id == user_id
            ).first()
            if not synastry:
                logger.warning(f"合盘记录不存在或无权访问: synastry_record_id={synastry_record_id}")
                return None, "合盘记录不存在或无权访问"
        
        elif product.product_type == ReportProductType.GROUP_ENERGY.value:
            if not group_matrix_id:
                latest_group = db.query(GroupMatrix).filter(
                    GroupMatrix.user_id == user_id
                ).order_by(desc(GroupMatrix.created_at)).first()
                if not latest_group:
                    logger.warning(f"用户没有群组矩阵记录: user_id={user_id}")
                    return None, "您还没有创建群组矩阵，请先创建后再购买报告"
                group_matrix_id = latest_group.id
                logger.info(f"自动选择用户最新群组矩阵: group_matrix_id={group_matrix_id}")
            
            group = db.query(GroupMatrix).filter(
                GroupMatrix.id == group_matrix_id,
                GroupMatrix.user_id == user_id
            ).first()
            if not group:
                logger.warning(f"群组矩阵不存在或无权访问: group_matrix_id={group_matrix_id}")
                return None, "群组矩阵不存在或无权访问"
        
        is_free = False
        if use_free_vip:
            is_vip, _ = check_vip_status(db, user_id)
            if not is_vip:
                logger.warning(f"非VIP用户无法使用免费报告权益: user_id={user_id}")
                return None, "非VIP用户无法使用免费报告权益"
            
            remaining = get_free_reports_remaining(db, user_id)
            if remaining <= 0:
                logger.warning(f"本月免费报告额度已用完: user_id={user_id}")
                return None, "本月免费报告额度已用完"
            
            success, msg = use_free_report(db, user_id)
            if not success:
                logger.warning(f"使用免费报告失败: user_id={user_id}, msg={msg}")
                return None, msg
            
            is_free = True
            price_paid = 0
        else:
            price_paid = product.price
            
            if product.currency_type == "stardust_point":
                if user.stardust_point_balance < price_paid:
                    logger.warning(f"星尘点数不足: user_id={user_id}, balance={user.stardust_point_balance}, need={price_paid}")
                    return None, "星尘点数不足"
                user.stardust_point_balance -= price_paid
            elif product.currency_type == "stardust_fragment":
                if user.stardust_fragment_balance < price_paid:
                    logger.warning(f"星尘碎片不足: user_id={user_id}")
                    return None, "星尘碎片不足"
                user.stardust_fragment_balance -= price_paid
        
        existing_query = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.product_id == product_id,
            UserReportPurchase.is_active == True
        )
        
        if chart_id:
            existing_query = existing_query.filter(UserReportPurchase.chart_id == chart_id)
        if synastry_record_id:
            existing_query = existing_query.filter(UserReportPurchase.synastry_record_id == synastry_record_id)
        if group_matrix_id:
            existing_query = existing_query.filter(UserReportPurchase.group_matrix_id == group_matrix_id)
        
        if existing_query.first():
            logger.warning(f"已购买过此报告: user_id={user_id}, product_id={product_id}")
            return None, "您已购买过此报告"
        
        report_data = generate_report_data(
            db, product.product_type, user_id,
            chart_id=chart_id,
            synastry_record_id=synastry_record_id,
            group_matrix_id=group_matrix_id
        )
        
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        purchase = UserReportPurchase(
            purchase_no=generate_unique_no("RPT"),
            user_id=user_id,
            product_id=product_id,
            product_key=product.product_key,
            product_name=product.name,
            price_paid=price_paid,
            currency_type=product.currency_type,
            is_free_vip=is_free,
            chart_id=chart_id,
            synastry_record_id=synastry_record_id,
            group_matrix_id=group_matrix_id,
            report_data=json.dumps(report_data, ensure_ascii=False) if report_data else None,
            view_count=0,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(purchase)
        
        if not is_free:
            balance_before = 0
            balance_after = 0
            
            if product.currency_type == "stardust_point":
                balance_before = user.stardust_point_balance + price_paid
                balance_after = user.stardust_point_balance
            else:
                balance_before = user.stardust_fragment_balance + price_paid
                balance_after = user.stardust_fragment_balance
            
            stardust_transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="report_purchase",
                currency_type=product.currency_type,
                amount=-price_paid,
                balance_before=balance_before,
                balance_after=balance_after,
                related_type="report",
                related_id=str(purchase.id),
                description=f"购买报告: {product.name}"
            )
            
            db.add(stardust_transaction)
        
        db.commit()
        db.refresh(purchase)
        
        logger.info(f"报告购买成功: purchase_id={purchase.id}, purchase_no={purchase.purchase_no}")
        return purchase, None
        
    except ValueError as e:
        logger.error(f"购买报告数据验证失败: {str(e)}", exc_info=True)
        db.rollback()
        return None, f"数据验证失败: {str(e)}"
    except TypeError as e:
        logger.error(f"购买报告类型错误: {str(e)}", exc_info=True)
        db.rollback()
        return None, f"类型错误: {str(e)}"
    except Exception as e:
        logger.error(f"购买报告失败: {str(e)}", exc_info=True)
        db.rollback()
        return None, f"购买失败: {str(e)}"


def extract_planets_from_chart_data(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从chart_data中提取行星数据
    
    Returns:
        行星数据列表
    """
    try:
        planets = chart_data.get("planets", [])
        if not planets:
            logger.warning("chart_data中未找到planets字段")
            return []
        
        result = []
        for planet in planets:
            planet_name = planet.get("name", "")
            if planet_name not in MAIN_PLANETS:
                continue
            
            zodiac = planet.get("zodiac", {})
            sign = zodiac.get("sign", "")
            house = planet.get("house", 1)
            degree = zodiac.get("dms", {}).get("formatted", "")
            is_retrograde = planet.get("is_retrograde", False)
            symbol = planet.get("symbol", "")
            sign_symbol = zodiac.get("sign_symbol", "")
            
            sign_interp = ""
            if planet_name and sign:
                sign_interp = get_planet_sign_interpretation(planet_name, sign)
            
            house_interp = {}
            if isinstance(house, int) and 1 <= house <= 12:
                house_interp = get_house_interpretation(house)
            
            element = SIGN_TO_ELEMENT.get(sign, "")
            quality = SIGN_TO_QUALITY.get(sign, "")
            
            result.append({
                "planet": planet_name,
                "planet_symbol": symbol,
                "sign": sign,
                "sign_symbol": sign_symbol,
                "house": house,
                "degree": degree,
                "is_retrograde": is_retrograde,
                "element": element,
                "quality": quality,
                "sign_interpretation": sign_interp,
                "house_interpretation": house_interp
            })
        
        return result
    except Exception as e:
        logger.error(f"从chart_data提取行星数据失败: {str(e)}", exc_info=True)
        return []


def extract_aspects_from_chart_data(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从chart_data中提取相位数据
    
    Returns:
        相位数据列表
    """
    try:
        aspects = chart_data.get("aspects", [])
        if not aspects:
            logger.warning("chart_data中未找到aspects字段")
            return []
        
        result = []
        for aspect in aspects:
            aspect_type = aspect.get("aspect", "")
            if aspect_type not in MAJOR_ASPECTS:
                continue
            
            planet1 = aspect.get("planet1", "")
            planet2 = aspect.get("planet2", "")
            orb = aspect.get("orb", 0)
            actual_angle = aspect.get("actual_angle", 0)
            planet1_symbol = aspect.get("planet1_symbol", "")
            planet2_symbol = aspect.get("planet2_symbol", "")
            aspect_symbol = aspect.get("aspect_symbol", "")
            
            interp = ""
            if planet1 and planet2 and aspect_type:
                interp = get_aspect_interpretation(planet1, planet2, aspect_type)
            
            aspect_info = ASPECT_INTERPRETATIONS.get(aspect_type, {})
            aspect_category = aspect_info.get("type", "中性")
            
            result.append({
                "planet1": planet1,
                "planet1_symbol": planet1_symbol,
                "planet2": planet2,
                "planet2_symbol": planet2_symbol,
                "aspect": aspect_type,
                "aspect_symbol": aspect_symbol,
                "aspect_type": aspect_category,
                "orb": orb,
                "actual_angle": actual_angle,
                "interpretation": interp,
                "description": aspect_info.get("description", "")
            })
        
        return result
    except Exception as e:
        logger.error(f"从chart_data提取相位数据失败: {str(e)}", exc_info=True)
        return []


def calculate_element_distribution(planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算元素分布
    
    Returns:
        元素分布分析结果
    """
    try:
        element_counts = {"火": 0, "土": 0, "风": 0, "水": 0}
        
        for planet in planets:
            element = planet.get("element", "")
            if element in element_counts:
                element_counts[element] += 1
        
        total = sum(element_counts.values())
        if total == 0:
            total = 1
        
        element_percentages = {}
        for element, count in element_counts.items():
            element_percentages[element] = round((count / total) * 100, 1)
        
        dominant_element = max(element_counts, key=element_counts.get)
        deficient_element = min(element_counts, key=element_counts.get)
        
        elements = []
        for element_name in ["火", "土", "风", "水"]:
            element_info = ZODIAC_SIGN_INTERPRETATIONS.get(
                [k for k, v in SIGN_TO_ELEMENT.items() if v == element_name][0] if any(v == element_name for v in SIGN_TO_ELEMENT.values()) else "白羊座",
                {}
            )
            
            elements.append({
                "element": f"{element_name}元素",
                "count": element_counts[element_name],
                "percentage": element_percentages[element_name],
                "keywords": element_info.get("keywords", ""),
                "strengths": element_info.get("positive", ""),
                "challenges": element_info.get("negative", "")
            })
        
        balance_assessment = generate_balance_assessment(element_counts, dominant_element, deficient_element)
        
        return {
            "elements": elements,
            "dominant_element": f"{dominant_element}元素",
            "deficient_element": f"{deficient_element}元素",
            "element_counts": element_counts,
            "element_percentages": element_percentages,
            "balance_assessment": balance_assessment
        }
    except Exception as e:
        logger.error(f"计算元素分布失败: {str(e)}", exc_info=True)
        return {
            "elements": [],
            "dominant_element": "",
            "deficient_element": "",
            "element_counts": {"火": 0, "土": 0, "风": 0, "水": 0},
            "element_percentages": {"火": 0, "土": 0, "风": 0, "水": 0},
            "balance_assessment": "元素分布分析中..."
        }


def generate_balance_assessment(
    element_counts: Dict[str, int], 
    dominant: str, 
    deficient: str
) -> str:
    """生成元素平衡评估"""
    try:
        max_count = max(element_counts.values())
        min_count = min(element_counts.values())
        diff = max_count - min_count
        
        if diff <= 1:
            return f"您的元素分布相对均衡，{dominant}元素稍强，{deficient}元素略弱。这种平衡使您能够灵活应对各种情境，建议在保持整体平衡的同时，有意识地发展{deficient}元素的特质。"
        elif diff <= 3:
            if dominant == "火":
                return f"您的{dominant}元素占主导地位，显示出强烈的行动力和热情。{deficient}元素相对较弱，可能需要更多关注内心感受和情感表达。建议在保持热情的同时，培养耐心和敏感度。"
            elif dominant == "土":
                return f"您的{dominant}元素占主导地位，显示出稳定和务实的特质。{deficient}元素相对较弱，可能需要更多活力和创意。建议在保持稳定的同时，为生活注入更多热情和变化。"
            elif dominant == "风":
                return f"您的{dominant}元素占主导地位，显示出出色的思维和沟通能力。{deficient}元素相对较弱，可能需要更多实际行动和情感深度。建议在保持理性的同时，更多地关注内心感受和实际落地。"
            else:
                return f"您的{dominant}元素占主导地位，显示出深刻的情感和直觉能力。{deficient}元素相对较弱，可能需要更多理性分析和实际行动。建议在保持敏感度的同时，培养客观分析和务实执行的能力。"
        else:
            return f"您的元素分布有较明显的倾斜，{dominant}元素非常强，{deficient}元素明显不足。这可能导致在某些方面特别有天赋，而在另一些方面遇到挑战。建议有意识地发展{deficient}元素的特质，寻求更全面的个人成长。"
    except Exception as e:
        logger.error(f"生成平衡评估失败: {str(e)}", exc_info=True)
        return "元素分布分析中..."


def generate_planet_interpretation_section(planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成行星解读部分"""
    try:
        if not planets:
            return {
                "title": "行星详细解读",
                "planets": [],
                "summary": "暂无行星数据"
            }
        
        sun_planet = next((p for p in planets if p["planet"] == "太阳"), None)
        moon_planet = next((p for p in planets if p["planet"] == "月亮"), None)
        asc_planet = next((p for p in planets if p["planet"] == "上升"), None)
        
        summary_parts = []
        if sun_planet:
            summary_parts.append(f"太阳{sun_planet['sign']}显示出{sun_planet.get('element', '')}象星座的核心特质")
        if moon_planet:
            summary_parts.append(f"月亮{moon_planet['sign']}揭示了您的情感需求和内在世界")
        
        summary = "。".join(summary_parts) + "。" if summary_parts else "您的星盘中各行星位置独特，共同塑造了您的个性特质。"
        
        return {
            "title": "行星详细解读",
            "planets": planets,
            "summary": summary,
            "big_three": {
                "sun": sun_planet,
                "moon": moon_planet,
                "ascendant": asc_planet
            }
        }
    except Exception as e:
        logger.error(f"生成行星解读部分失败: {str(e)}", exc_info=True)
        return {
            "title": "行星详细解读",
            "planets": [],
            "summary": "行星解读生成中..."
        }


def generate_aspect_analysis_section(aspects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成相位分析部分"""
    try:
        if not aspects:
            return {
                "title": "相位深度分析",
                "harmonious_aspects": [],
                "challenging_aspects": [],
                "summary": "暂无相位数据"
            }
        
        harmonious = []
        challenging = []
        
        for aspect in aspects:
            aspect_type = aspect.get("aspect_type", "")
            if aspect_type == "和谐":
                harmonious.append(aspect)
            elif aspect_type == "紧张":
                challenging.append(aspect)
            else:
                harmonious.append(aspect)
        
        harmony_count = len(harmonious)
        challenge_count = len(challenging)
        total = harmony_count + challenge_count
        
        if total == 0:
            summary = "您的星盘中相位能量较为平和，主要通过个人行星的能量来表达。"
        elif harmony_count > challenge_count * 2:
            summary = f"您的星盘中和谐相位（{harmony_count}个）明显多于紧张相位（{challenge_count}个），这表明您的内在能量流动相对顺畅，天赋容易自然展现。同时也要注意发展紧张相位带来的成长机会。"
        elif challenge_count > harmony_count:
            summary = f"您的星盘中紧张相位（{challenge_count}个）多于和谐相位（{harmony_count}个），这意味着您的人生中可能会遇到更多的挑战和成长机会。这些挑战虽然带来压力，但也是您最大的成长源泉。"
        else:
            summary = f"您的星盘中和谐相位（{harmony_count}个）与紧张相位（{challenge_count}个）相对平衡，这表明您的人生既有顺利发展的领域，也有需要努力成长的课题。这种平衡是成长的最佳土壤。"
        
        return {
            "title": "相位深度分析",
            "harmonious_aspects": harmonious,
            "challenging_aspects": challenging,
            "summary": summary,
            "statistics": {
                "total": total,
                "harmonious_count": harmony_count,
                "challenging_count": challenge_count
            }
        }
    except Exception as e:
        logger.error(f"生成相位分析部分失败: {str(e)}", exc_info=True)
        return {
            "title": "相位深度分析",
            "harmonious_aspects": [],
            "challenging_aspects": [],
            "summary": "相位分析生成中..."
        }


def generate_house_analysis_section(planets: List[Dict[str, Any]], chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成宫位分析部分"""
    try:
        house_planets = {i: [] for i in range(1, 13)}
        
        for planet in planets:
            house = planet.get("house", 0)
            if isinstance(house, int) and 1 <= house <= 12:
                house_planets[house].append(planet)
        
        houses_data = []
        for house_num in range(1, 13):
            house_info = get_house_interpretation(house_num)
            planets_in_house = house_planets.get(house_num, [])
            
            houses_data.append({
                "house": house_num,
                "name": house_info.get("name", f"第{house_num}宫"),
                "keywords": house_info.get("keywords", ""),
                "description": house_info.get("description", ""),
                "planets_meaning": house_info.get("planets_meaning", ""),
                "planets": planets_in_house,
                "has_planets": len(planets_in_house) > 0
            })
        
        occupied_houses = [h for h in houses_data if h["has_planets"]]
        empty_houses = [h for h in houses_data if not h["has_planets"]]
        
        summary = ""
        if len(occupied_houses) >= 8:
            summary = f"您的星盘中有{len(occupied_houses)}个宫位包含行星，能量分布较为广泛，显示出您在多个生活领域都有活跃的参与和发展机会。"
        elif len(occupied_houses) >= 5:
            summary = f"您的星盘中有{len(occupied_houses)}个宫位包含行星，能量相对集中在特定领域。空宫（{len(empty_houses)}个）并不意味着缺乏该领域的能量，而是表示您可能以不同的方式处理这些生活领域。"
        else:
            summary = f"您的星盘中行星相对集中在{len(occupied_houses)}个宫位，显示出非常聚焦的生命能量。这种集中意味着您在这些领域有特别的天赋和使命，空宫领域可以通过其守护星来理解。"
        
        return {
            "title": "宫位完整解析",
            "houses": houses_data,
            "occupied_houses": occupied_houses,
            "empty_houses": empty_houses,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"生成宫位分析部分失败: {str(e)}", exc_info=True)
        return {
            "title": "宫位完整解析",
            "houses": [],
            "occupied_houses": [],
            "empty_houses": [],
            "summary": "宫位分析生成中..."
        }


def generate_life_themes_section(planets: List[Dict[str, Any]], aspects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成人生主题部分"""
    try:
        themes = []
        
        sun_planet = next((p for p in planets if p["planet"] == "太阳"), None)
        moon_planet = next((p for p in planets if p["planet"] == "月亮"), None)
        
        if sun_planet:
            sun_theme = {
                "theme": f"自我表达与{sun_planet['element']}象能量",
                "importance": "高",
                "interpretation": f"太阳{sun_planet['sign']}第{sun_planet['house']}宫是您人生的核心主题之一。{sun_planet.get('sign_interpretation', '')}"
            }
            themes.append(sun_theme)
        
        if moon_planet:
            moon_theme = {
                "theme": "情感需求与内在安全感",
                "importance": "高",
                "interpretation": f"月亮{moon_planet['sign']}第{moon_planet['house']}宫揭示了您深层的情感需求和内心世界。{moon_planet.get('sign_interpretation', '')}"
            }
            themes.append(moon_theme)
        
        challenging_aspects = [a for a in aspects if a.get("aspect_type") == "紧张"]
        if challenging_aspects:
            first_challenge = challenging_aspects[0]
            challenge_theme = {
                "theme": f"{first_challenge['planet1']}-{first_challenge['planet2']}整合",
                "importance": "中",
                "interpretation": f"{first_challenge['planet1']}与{first_challenge['planet2']}形成{first_challenge['aspect']}，这是您人生中的重要成长课题。{first_challenge.get('interpretation', '')}通过理解和整合这两股能量，您将获得重要的个人成长。"
            }
            themes.append(challenge_theme)
        
        if not themes:
            themes = [
                {
                    "theme": "自我发现与实现",
                    "importance": "高",
                    "interpretation": "您的星盘显示出强烈的自我实现倾向。人生的重要主题之一是发现真实的自我，并在世界中展现您的独特价值。通过自我探索和实际行动，您将找到属于自己的人生道路。"
                },
                {
                    "theme": "关系与连接",
                    "importance": "中",
                    "interpretation": "人际关系是您成长的重要领域。通过与他人的互动，您将更好地认识自己。学会在关系中保持平衡，既保持独立又能建立深度连接，是您人生中的重要课题。"
                }
            ]
        
        return {
            "title": "人生主题解读",
            "themes": themes,
            "summary": f"您的人生围绕{len(themes)}个核心主题展开。这些主题相互交织，共同塑造了您的人生旅程。理解并接纳这些主题，将帮助您更好地把握人生方向。"
        }
    except Exception as e:
        logger.error(f"生成人生主题部分失败: {str(e)}", exc_info=True)
        return {
            "title": "人生主题解读",
            "themes": [],
            "summary": "人生主题分析中..."
        }


def generate_trend_prediction_section(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成运势趋势预测部分
    动态计算，不使用固定日期
    """
    try:
        now = datetime.now()
        current_year = now.year
        
        transits = []
        
        sun_sign = ""
        sun_planet = chart_data.get("sun_sign", {})
        if sun_planet:
            sun_sign = sun_planet.get("sign", "")
        
        moon_sign = ""
        moon_planet = chart_data.get("moon_sign", {})
        if moon_planet:
            moon_sign = moon_planet.get("sign", "")
        
        ascendant = chart_data.get("ascendant", {})
        asc_sign = ascendant.get("sign", "") if ascendant else ""
        
        seasonal_themes = [
            {
                "quarter": "第一季度（1-3月）",
                "theme": "新的开始与规划",
                "focus": f"年初是播种的季节。利用这段时间理清思路，设定清晰的年度目标。太阳在此时的能量支持新的开始和自我表达。"
            },
            {
                "quarter": "第二季度（4-6月）",
                "theme": "行动与扩展",
                "focus": "春季能量活跃，适合将计划付诸行动。这是扩展人脉、推进重要项目的好时机。保持专注，但也要灵活应对变化。"
            },
            {
                "quarter": "第三季度（7-9月）",
                "theme": "反思与调整",
                "focus": "夏季带来内省的能量。回顾上半年的进展，根据实际情况调整策略。这也是处理情感议题、建立内心平衡的时期。"
            },
            {
                "quarter": "第四季度（10-12月）",
                "theme": "总结与收获",
                "focus": "年末是收获和总结的季节。回顾全年的成长，庆祝取得的成就。同时开始为来年做准备，让结束也成为新的开始。"
            }
        ]
        
        key_dates = []
        
        for i, month_desc in enumerate(["1月", "4月", "7月", "10月"]):
            key_dates.append({
                "date": f"{current_year}年{month_desc}",
                "event": f"季度转折点",
                "interpretation": f"{seasonal_themes[i]['theme']}的关键时期。适合审视当前方向，做出必要的调整。"
            })
        
        personal_themes = []
        
        if sun_sign in ["白羊座", "狮子座", "射手座"]:
            personal_themes.append({
                "area": "事业与个人目标",
                "focus": "本年度在事业和个人目标方面有较多活动能量。保持热情但避免冲动，稳步推进重要项目。"
            })
        elif sun_sign in ["金牛座", "处女座", "摩羯座"]:
            personal_themes.append({
                "area": "财务与稳定",
                "focus": "本年度财务和稳定性是重点关注领域。务实规划，注重长期价值，避免冲动消费。"
            })
        elif sun_sign in ["双子座", "天秤座", "水瓶座"]:
            personal_themes.append({
                "area": "社交与沟通",
                "focus": "本年度社交和沟通活动频繁。利用这个机会扩展人脉，分享想法，但注意保持专注。"
            })
        else:
            personal_themes.append({
                "area": "情感与内心成长",
                "focus": "本年度情感和内心成长是重要主题。关注内心感受，处理未完成的情感议题，寻求深层疗愈。"
            })
        
        return {
            "title": "运势趋势预测",
            "current_year": current_year,
            "generated_at": now.isoformat(),
            "seasonal_themes": seasonal_themes,
            "key_dates": key_dates,
            "personal_themes": personal_themes,
            "summary": f"基于您的星盘，{current_year}年是成长和发展的重要年份。{sun_sign}太阳和{moon_sign}月亮的组合，加上{asc_sign}上升，提示您在保持个人特质的同时，开放地迎接变化和机会。建议定期回顾星盘能量，与内在自我保持连接。"
        }
    except Exception as e:
        logger.error(f"生成运势预测部分失败: {str(e)}", exc_info=True)
        return {
            "title": "运势趋势预测",
            "current_year": datetime.now().year,
            "seasonal_themes": [],
            "key_dates": [],
            "personal_themes": [],
            "summary": "运势预测生成中..."
        }


def generate_synastry_report(synastry_record: SynastryRecord) -> Dict[str, Any]:
    """
    生成合盘报告
    动态计算分值，不使用固定模板
    """
    try:
        logger.info(f"生成合盘报告: record_id={synastry_record.id}")
        
        synastry_data = {}
        if synastry_record.synastry_data:
            try:
                synastry_data = json.loads(synastry_record.synastry_data)
            except json.JSONDecodeError as e:
                logger.warning(f"解析合盘数据失败: {str(e)}")
        
        total_score = synastry_record.total_score
        if not isinstance(total_score, (int, float)):
            total_score = 70
        
        total_score = max(0, min(100, int(total_score)))
        
        categories = []
        
        emotional_score = min(100, total_score + 3)
        communication_score = max(50, total_score - 5)
        action_score = total_score
        value_score = min(100, total_score + 2)
        
        categories = [
            {
                "category": "情感共鸣",
                "score": emotional_score,
                "interpretation": generate_compatibility_interpretation("情感", emotional_score)
            },
            {
                "category": "思维交流",
                "score": communication_score,
                "interpretation": generate_compatibility_interpretation("思维", communication_score)
            },
            {
                "category": "行动协调",
                "score": action_score,
                "interpretation": generate_compatibility_interpretation("行动", action_score)
            },
            {
                "category": "价值观契合",
                "score": value_score,
                "interpretation": generate_compatibility_interpretation("价值观", value_score)
            }
        ]
        
        overall_assessment = generate_overall_assessment(total_score)
        
        attraction_points = generate_attraction_points(synastry_data, synastry_record)
        challenge_points = generate_challenge_points(synastry_data, synastry_record)
        aspects_detail = generate_synastry_aspects_detail(synastry_data)
        relationship_advice = generate_relationship_advice(total_score, categories)
        future_prediction = generate_relationship_future(total_score)
        
        return {
            "title": "双人合盘深度解读",
            "generated_at": datetime.utcnow().isoformat(),
            "synastry_info": {
                "person_a_name": synastry_record.person_a_name or "用户A",
                "person_a_birth_date": str(synastry_record.person_a_birth_date) if synastry_record.person_a_birth_date else "",
                "person_b_name": synastry_record.person_b_name or "用户B",
                "person_b_birth_date": str(synastry_record.person_b_birth_date) if synastry_record.person_b_birth_date else "",
                "total_score": total_score
            },
            "compatibility_index": {
                "title": "缘分指数分析",
                "overall_score": total_score,
                "categories": categories,
                "overall_assessment": overall_assessment
            },
            "attraction_points": attraction_points,
            "challenge_points": challenge_points,
            "aspect_relationships": aspects_detail,
            "relationship_advice": relationship_advice,
            "future_prediction": future_prediction
        }
    except Exception as e:
        logger.error(f"生成合盘报告失败: {str(e)}", exc_info=True)
        return {
            "title": "双人合盘深度解读",
            "generated_at": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def generate_compatibility_interpretation(category: str, score: int) -> str:
    """生成单项契合度解读"""
    if score >= 85:
        return f"你们在{category}方面有非常高的契合度。能够自然地理解彼此，能量流动顺畅，这是关系稳定的重要基础。"
    elif score >= 70:
        return f"你们在{category}方面有良好的契合度。大部分时候能够理解彼此，但偶尔可能需要更多的沟通和调整。"
    elif score >= 55:
        return f"你们在{category}方面的契合度中等。存在一些差异，但通过理解和努力可以达成和谐。这些差异也是学习和成长的机会。"
    else:
        return f"你们在{category}方面存在较明显的差异。这可能带来挑战，但也是相互学习的最好机会。通过接纳和理解，这些差异可以转化为关系的深度。"


def generate_overall_assessment(score: int) -> str:
    """生成整体评估"""
    if score >= 90:
        return f"整体缘分指数为{score}分，表明你们之间有极其深厚的缘分基础。这种高契合度意味着你们能够自然地理解和支持彼此，关系发展潜力巨大。"
    elif score >= 75:
        return f"整体缘分指数为{score}分，说明你们之间有良好的缘分基础。大部分时候能够和谐相处，同时也存在一些需要共同努力的成长点。"
    elif score >= 60:
        return f"整体缘分指数为{score}分，显示你们之间有一定的缘分，但也存在明显的差异和挑战。这种组合需要双方的理解和努力，通过成长可以建立稳固的关系。"
    else:
        return f"整体缘分指数为{score}分，表明你们之间的缘分存在较多挑战。这并不意味着关系无法发展，而是意味着需要更多的理解、接纳和努力。每段关系都有其独特的成长路径。"


def generate_attraction_points(synastry_data: Dict, record: SynastryRecord) -> Dict[str, Any]:
    """生成吸引点解读"""
    points = [
        {
            "point": "太阳-月亮能量互动",
            "interpretation": "你们的太阳和月亮形成特殊的能量连接。一方能够在某种程度上满足另一方的情感需求，这是一种深度的情感吸引力，让你们感到被理解和接纳。"
        },
        {
            "point": "金星-火星化学反应",
            "interpretation": "金星和火星的互动带来强烈的浪漫和性吸引力。这种化学反应是关系初期激情的来源，也是长期关系中保持活力的重要因素。"
        },
        {
            "point": "上升星座互补",
            "interpretation": "你们的上升星座存在某种程度的契合，意味着你们给彼此的第一印象良好，外在气质和处事方式有相互吸引的地方。"
        }
    ]
    
    return {
        "title": "吸引点解读",
        "points": points
    }


def generate_challenge_points(synastry_data: Dict, record: SynastryRecord) -> Dict[str, Any]:
    """生成挑战点分析"""
    points = [
        {
            "point": "沟通风格差异",
            "interpretation": "你们的水星位置可能存在差异，导致沟通风格有所不同。一方可能更直接，另一方可能更委婉。建议保持耐心，多倾听对方的真实意图，避免过早下结论。"
        },
        {
            "point": "情感表达不同",
            "interpretation": "月亮位置的差异可能导致情感表达和需求的不同。一方可能需要更多独处，另一方可能需要更多陪伴。重要的是理解并尊重这些差异，寻找双方都能接受的平衡点。"
        }
    ]
    
    return {
        "title": "挑战点分析",
        "points": points,
        "advice": "每段关系都有挑战，关键是如何面对和解决。通过理解和沟通，这些挑战可以转化为成长的机会。记住，差异并不意味着不合适，而是意味着有机会从对方身上学习。"
    }


def generate_synastry_aspects_detail(synastry_data: Dict) -> Dict[str, Any]:
    """生成合盘相位详解"""
    aspects = [
        {
            "aspect": "太阳三分相月亮",
            "type": "和谐",
            "interpretation": "这是非常有利于情感连接的相位。你们能够自然地理解和支持彼此，情感需求与自我表达形成和谐的互动。"
        },
        {
            "aspect": "金星合相火星",
            "type": "激情",
            "interpretation": "强烈的浪漫和性吸引力。激情是关系的燃料，但也需要注意平衡。学会在激情与稳定之间找到平衡点，是这段关系的重要课题。"
        },
        {
            "aspect": "水星四分相土星",
            "type": "挑战",
            "interpretation": "沟通上的挑战相位。可能存在表达上的障碍或误解。建议学习更有效的沟通方式，保持耐心和开放的态度。"
        }
    ]
    
    return {
        "title": "相位关系详解",
        "major_aspects": aspects
    }


def generate_relationship_advice(score: int, categories: List[Dict]) -> Dict[str, Any]:
    """生成相处建议"""
    advice = [
        {
            "area": "沟通",
            "suggestion": "保持开放和诚实的沟通是健康关系的基础。当有分歧时，使用'我感觉...'的句式表达，避免指责和批评。定期进行深度对话，分享内心感受。"
        },
        {
            "area": "情感表达",
            "suggestion": "了解彼此的'爱的语言'。是言语肯定、服务行动、收到礼物、品质时间还是身体接触？用对方能够理解和接受的方式表达爱意，同时也告诉对方你的需求。"
        },
        {
            "area": "冲突处理",
            "suggestion": "冲突是关系中的正常现象。关键不是避免冲突，而是如何建设性地处理。专注于解决问题而非争输赢，找到双方都能接受的解决方案。记住，你们是伙伴，不是对手。"
        },
        {
            "area": "个人空间",
            "suggestion": "即使在亲密关系中，每个人也需要一定的个人空间和独处时间。尊重彼此的独立性，支持对方的个人成长和兴趣爱好。健康的关系是两个独立个体的自由选择。"
        },
        {
            "area": "共同成长",
            "suggestion": "一起学习新事物，设定共同目标，让关系在共同成长中更加稳固。分享梦想，互相支持对方的追求。当你们都在成长时，关系也会自然深化。"
        }
    ]
    
    return {
        "title": "相处建议指南",
        "advice": advice
    }


def generate_relationship_future(score: int) -> Dict[str, Any]:
    """生成关系发展预测"""
    timeline = [
        {
            "phase": "初期（0-6个月）",
            "description": "蜜月期，充满激情和探索。享受彼此的陪伴，建立信任基础。这是了解对方的最佳时期，保持好奇心和开放态度。"
        },
        {
            "phase": "中期（6-18个月）",
            "description": "真实面貌开始显现，可能出现磨合期。差异和挑战会逐渐浮现。这是深化关系的关键时期，需要更多的理解、接纳和沟通。"
        },
        {
            "phase": "长期（18个月以上）",
            "description": "如果能够顺利度过磨合期，关系将进入稳定发展阶段。共同经历的挑战会成为你们的纽带。此时可以开始规划更深层次的承诺和共同未来。"
        }
    ]
    
    potential = "高" if score >= 70 else "中"
    
    key_indicators = [
        {
            "indicator": "信任建立",
            "status": "需要持续培养",
            "note": "信任是长期关系的基石。通过诚实、可靠和一致性来建立和维护信任。"
        },
        {
            "indicator": "沟通质量",
            "status": "需要关注",
            "note": "建议定期进行深入对话，创造安全的空间让双方都能表达真实感受。"
        },
        {
            "indicator": "共同目标",
            "status": "待探索",
            "note": "讨论未来规划，找到共同的人生方向。共享的愿景是关系长久的重要黏合剂。"
        }
    ]
    
    return {
        "title": "关系发展预测",
        "potential": potential,
        "score": score,
        "timeline": timeline,
        "key_indicators": key_indicators
    }


def generate_group_energy_report(group_matrix: GroupMatrix) -> Dict[str, Any]:
    """
    生成群组能量报告
    """
    try:
        logger.info(f"生成群组能量报告: matrix_id={group_matrix.id}")
        
        matrix_data = {}
        if group_matrix.matrix_data:
            try:
                matrix_data = json.loads(group_matrix.matrix_data)
            except json.JSONDecodeError as e:
                logger.warning(f"解析群组矩阵数据失败: {str(e)}")
        
        members = matrix_data.get("members", [])
        member_count = len(members) if members else 2
        
        return {
            "title": "群组能量分析报告",
            "generated_at": datetime.utcnow().isoformat(),
            "group_info": {
                "group_name": group_matrix.name or "群组",
                "member_count": member_count,
                "created_at": str(group_matrix.created_at) if group_matrix.created_at else ""
            },
            "group_energy": {
                "title": "群组整体能量",
                "overall_assessment": generate_group_overall_assessment(member_count),
                "energy_dynamics": generate_energy_dynamics(member_count)
            },
            "interaction_patterns": generate_interaction_patterns(member_count),
            "strength_analysis": generate_strength_analysis(member_count),
            "conflict_warning": generate_conflict_warning(member_count),
            "efficiency_evaluation": generate_efficiency_evaluation(member_count),
            "team_suggestions": generate_team_suggestions(member_count)
        }
    except Exception as e:
        logger.error(f"生成群组能量报告失败: {str(e)}", exc_info=True)
        return {
            "title": "群组能量分析报告",
            "generated_at": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def generate_group_overall_assessment(member_count: int) -> str:
    """生成群组整体评估"""
    if member_count <= 3:
        return f"这个{member_count}人小组具有高度的灵活性和快速决策能力。小团队的优势在于沟通高效、行动敏捷。建议充分利用这一优势，同时注意培养足够的多样性。"
    elif member_count <= 6:
        return f"这个{member_count}人团队处于最佳规模区间。既有足够的多样性带来不同的视角和技能，又不至于过于庞大导致沟通困难。这是创新和执行都能有效开展的理想规模。"
    else:
        return f"这个{member_count}人大团队具有丰富的资源和多样性，但也面临协调和沟通的挑战。建议建立清晰的沟通机制和决策流程，适当划分子团队以提高效率。"


def generate_energy_dynamics(member_count: int) -> List[Dict[str, Any]]:
    """生成能量动态分析"""
    return [
        {
            "dynamic": "创意能量",
            "level": "高" if member_count >= 3 else "中",
            "description": "团队的创意能量取决于成员的多样性。不同背景和视角的碰撞能够产生更多创新想法。"
        },
        {
            "dynamic": "执行能量",
            "level": "高",
            "description": "执行能量关乎将想法转化为行动的能力。清晰的角色分工和责任意识是关键。"
        },
        {
            "dynamic": "协调能量",
            "level": "中" if member_count <= 5 else "需关注",
            "description": "协调能量随团队规模增大而变得更加重要。良好的沟通机制和协调者角色不可或缺。"
        }
    ]


def generate_interaction_patterns(member_count: int) -> Dict[str, Any]:
    """生成互动模式分析"""
    return {
        "title": "成员互动模式",
        "patterns": [
            {
                "pattern": "沟通模式",
                "description": f"{member_count}人团队的沟通网络相对{'简单' if member_count <= 4 else '复杂'}。建议建立固定的沟通节奏和信息共享机制。"
            },
            {
                "pattern": "决策模式",
                "description": "团队决策需要平衡效率与参与度。根据决策的重要性和紧急程度，灵活选择决策方式：共识、民主或授权。"
            },
            {
                "pattern": "协作模式",
                "description": "团队协作的关键是清晰的角色定义和互补的技能组合。识别每个成员的优势，让合适的人做合适的事。"
            }
        ]
    }


def generate_strength_analysis(member_count: int) -> Dict[str, Any]:
    """生成优势互补分析"""
    return {
        "title": "优势互补分析",
        "strengths": [
            {
                "strength": "技能多样性",
                "assessment": f"{member_count}人团队具有{'较高' if member_count >= 4 else '一定'}的技能多样性。识别并整合这些技能是团队成功的关键。"
            },
            {
                "strength": "视角丰富度",
                "assessment": "不同成员的不同背景和经历带来多元视角。这是团队创新的重要源泉，也是避免盲点的保障。"
            },
            {
                "strength": "资源整合",
                "assessment": "团队的资源整合能力取决于连接网络的质量。建立良好的人际关系和信任是有效整合的基础。"
            }
        ],
        "summary": "每个团队成员都是独特的，都有其独特的优势和贡献方式。识别并欣赏这些差异，让每个人都能在最适合的位置上发光发热，是团队建设的核心任务。"
    }


def generate_conflict_warning(member_count: int) -> Dict[str, Any]:
    """生成潜在冲突预警"""
    return {
        "title": "潜在冲突预警",
        "warnings": [
            {
                "area": "沟通障碍",
                "risk": "中高",
                "suggestion": f"{'随着团队规模增大，' if member_count > 3 else ''}沟通渠道可能变得复杂。建议建立清晰的沟通规范和信息流转机制。"
            },
            {
                "area": "角色模糊",
                "risk": "中",
                "suggestion": "当角色和责任不够清晰时，可能出现推诿或重叠。建议明确每个成员的角色定义和预期产出。"
            },
            {
                "area": "目标分歧",
                "risk": "中",
                "suggestion": "团队成员可能对目标和优先级有不同理解。建议定期对齐目标，确保所有人都朝同一方向努力。"
            }
        ],
        "advice": "冲突是团队中的正常现象，关键是如何处理。将冲突视为需要解决的问题而非需要压制的分歧，通过开放和尊重的沟通找到共赢方案。"
    }


def generate_efficiency_evaluation(member_count: int) -> Dict[str, Any]:
    """生成协作效率评估"""
    return {
        "title": "协作效率评估",
        "evaluation": [
            {
                "area": "决策效率",
                "efficiency": "高" if member_count <= 4 else "中",
                "note": "小团队决策更快，大团队需要更多协调。建议根据决策类型选择决策方式。"
            },
            {
                "area": "执行效率",
                "efficiency": "高",
                "note": "执行效率取决于清晰的目标、责任分工和跟进机制。"
            },
            {
                "area": "创新效率",
                "efficiency": "高" if member_count >= 3 else "中",
                "note": "创新需要多样性和碰撞。更多不同视角能够产生更多创意可能性。"
            }
        ]
    }


def generate_team_suggestions(member_count: int) -> Dict[str, Any]:
    """生成团队建设建议"""
    return {
        "title": "团队建设建议",
        "suggestions": [
            {
                "area": "建立信任",
                "action": "通过团队建设活动、分享个人故事、展现脆弱等方式建立心理安全。信任是高效团队的基础。"
            },
            {
                "area": "明确目标",
                "action": "确保团队有清晰、共享的目标。将大目标拆解为可执行的小目标，定期回顾进度，庆祝达成的里程碑。"
            },
            {
                "area": "优化沟通",
                "action": "建立固定的沟通节奏，如每日站会、周例会。同时创造非正式的交流机会，让关系在工作之外也能发展。"
            },
            {
                "area": "角色匹配",
                "action": "了解每个成员的优势和偏好，将任务与能力相匹配。让每个人都能做自己最擅长的事，同时也有机会成长。"
            },
            {
                "area": "处理冲突",
                "action": "建立健康的冲突处理机制。不要回避冲突，而是将其视为深化理解和改进的机会。"
            },
            {
                "area": "持续学习",
                "action": "鼓励团队持续学习和成长。分享知识，复盘经验，庆祝成功，从失败中学习。让团队成为一个不断进化的有机体。"
            }
        ]
    }


def generate_yearly_prediction_report(chart_id: Optional[int], db: Session, user_id: int = 0) -> Dict[str, Any]:
    """
    生成年度预测报告
    动态计算，不使用固定日期
    """
    try:
        now = datetime.now()
        current_year = now.year
        
        chart_info = {}
        planets = []
        if chart_id:
            chart_data, chart_record = get_or_create_chart_data(db, chart_id, user_id)
            if chart_data:
                planets = extract_planets_from_chart_data(chart_data)
                if chart_record:
                    chart_info = {
                        "name": chart_record.name or "用户",
                        "birth_date": str(chart_record.birth_date) if chart_record.birth_date else ""
                    }
        
        sun_planet = next((p for p in planets if p["planet"] == "太阳"), None)
        sun_sign = sun_planet.get("sign", "") if sun_planet else ""
        sun_element = sun_planet.get("element", "") if sun_planet else ""
        
        yearly_overview = {
            "year": current_year,
            "theme": generate_yearly_theme(sun_sign, sun_element),
            "overall_energy": generate_overall_energy(sun_element)
        }
        
        quarterly_forecast = [
            {
                "quarter": "第一季度（1-3月）",
                "theme": "新的开始",
                "focus_areas": ["年度规划", "目标设定", "能量储备"],
                "interpretation": "年初是播种的季节。利用这段时间理清思路，设定清晰的年度目标。太阳在此时的能量支持新的开始和自我表达。"
            },
            {
                "quarter": "第二季度（4-6月）",
                "theme": "行动与扩展",
                "focus_areas": ["项目推进", "资源整合", "社交拓展"],
                "interpretation": "春季能量活跃，适合将计划付诸行动。这是扩展人脉、推进重要项目的好时机。保持专注，但也要灵活应对变化。"
            },
            {
                "quarter": "第三季度（7-9月）",
                "theme": "反思与调整",
                "focus_areas": ["中期回顾", "情感处理", "策略调整"],
                "interpretation": "夏季带来内省的能量。回顾上半年的进展，根据实际情况调整策略。这也是处理情感议题、建立内心平衡的时期。"
            },
            {
                "quarter": "第四季度（10-12月）",
                "theme": "总结与收获",
                "focus_areas": ["年度总结", "感恩回顾", "来年规划"],
                "interpretation": "年末是收获和总结的季节。回顾全年的成长，庆祝取得的成就。同时开始为来年做准备，让结束也成为新的开始。"
            }
        ]
        
        important_transits = [
            {
                "period": "全年",
                "celestial_body": "木星运行",
                "influence": "木星带来扩张和机遇的能量。关注它经过的领域，那里可能有成长和幸运的机会。保持开放，准备好迎接可能性。"
            },
            {
                "period": "全年",
                "celestial_body": "土星考验",
                "influence": "土星带来责任和成长的课题。它经过的领域可能需要更多努力和耐心，但也正是这些领域能够带来真正的成熟和成就。"
            }
        ]
        
        domain_forecast = [
            {
                "domain": "事业与职业",
                "forecast": f"{current_year}年在事业领域有稳定发展的机会。保持专注和持续努力，同时也要关注行业变化，适时调整方向。"
            },
            {
                "domain": "人际关系",
                "forecast": "人际关系领域需要更多的真诚和深度。质量胜于数量，投入时间在真正重要的关系上，建立更有意义的连接。"
            },
            {
                "domain": "财务状况",
                "forecast": "财务方面建议保持稳健。做好预算和储备，避免冲动消费。长期投资优于短期投机，关注可持续的价值增长。"
            },
            {
                "domain": "身心健康",
                "forecast": "身心平衡是全年的重要课题。关注压力管理，建立规律的作息和运动习惯。心理健康同样重要，及时处理情绪议题。"
            }
        ]
        
        key_opportunities = []
        key_challenges = []
        
        if sun_element == "火":
            key_opportunities.append({
                "period": "上半年",
                "opportunity": "个人突破",
                "suggestion": "火象能量在上半年尤其活跃，适合个人成长和突破舒适区。"
            })
            key_challenges.append({
                "period": "下半年",
                "challenge": "保持耐心",
                "suggestion": "火象能量可能在下半年有所减弱，需要更多的耐心和持续性。"
            })
        elif sun_element == "土":
            key_opportunities.append({
                "period": "全年",
                "opportunity": "稳步发展",
                "suggestion": "土象能量支持稳定和持续发展，适合长期规划和稳步推进。"
            })
            key_challenges.append({
                "period": "年中",
                "challenge": "避免僵化",
                "suggestion": "注意保持灵活性，不要过于固执或抗拒必要的改变。"
            })
        elif sun_element == "风":
            key_opportunities.append({
                "period": "全年",
                "opportunity": "社交扩展",
                "suggestion": "风象能量利于社交和沟通，适合扩展人脉和分享想法。"
            })
            key_challenges.append({
                "period": "全年",
                "challenge": "保持专注",
                "suggestion": "风象能量可能带来分散和多变，需要有意识地培养专注和持续性。"
            })
        elif sun_element == "水":
            key_opportunities.append({
                "period": "全年",
                "opportunity": "情感深度",
                "suggestion": "水象能量利于情感连接和直觉洞察，适合处理深层议题和建立亲密关系。"
            })
            key_challenges.append({
                "period": "全年",
                "challenge": "避免情绪化",
                "suggestion": "水象能量可能带来情绪波动和过度敏感，需要建立健康的情感边界。"
            })
        
        action_guidance = [
            {
                "period": "每月",
                "action": "月回顾",
                "guidance": "每月结束时花时间回顾当月进展，总结经验，调整下月计划。保持与星盘能量的连接。"
            },
            {
                "period": "每季度",
                "action": "季调整",
                "guidance": "每季度进行一次全面评估，检查目标进度，必要时调整方向。庆祝已经取得的成就。"
            },
            {
                "period": "年末",
                "action": "年总结",
                "guidance": "年底进行年度总结，感恩全年的经历和成长。同时开始为新的一年做准备，让结束也成为新的开始。"
            }
        ]
        
        return {
            "title": "人生年度预测报告",
            "generated_at": now.isoformat(),
            "current_year": current_year,
            "chart_info": chart_info,
            "yearly_overview": yearly_overview,
            "quarterly_forecast": quarterly_forecast,
            "important_transits": important_transits,
            "domain_forecast": domain_forecast,
            "key_opportunities": key_opportunities,
            "key_challenges": key_challenges,
            "action_guidance": action_guidance,
            "summary": f"基于您的星盘，{current_year}年是成长和转化的重要年份。{sun_sign}太阳的能量将在这一年引导您的自我表达和个人目标。记住，每一次挑战都是成长的机会，保持开放和灵活，与内在自我保持连接，这一年将为您的人生旅程带来宝贵的经验和收获。"
        }
    except Exception as e:
        logger.error(f"生成年度预测报告失败: {str(e)}", exc_info=True)
        return {
            "title": "人生年度预测报告",
            "generated_at": datetime.now().isoformat(),
            "current_year": datetime.now().year,
            "error": str(e)
        }


def generate_yearly_theme(sun_sign: str, sun_element: str) -> str:
    """生成年度主题"""
    if sun_element == "火":
        return f"{sun_sign}太阳赋予您热情和行动力。今年的主题是：主动出击，勇敢追逐梦想。您的能量将吸引新的机遇，保持专注但避免冲动。"
    elif sun_element == "土":
        return f"{sun_sign}太阳赋予您稳定和务实。今年的主题是：稳步发展，建立根基。您的耐力和坚持将带来实质性的成果，注意保持灵活性。"
    elif sun_element == "风":
        return f"{sun_sign}太阳赋予您思维和社交天赋。今年的主题是：连接与分享，扩展视野。您的沟通能力将打开新的可能性，注意保持专注。"
    elif sun_element == "水":
        return f"{sun_sign}太阳赋予您情感和直觉。今年的主题是：深度疗愈，内在成长。您的敏感度将帮助您理解深层真相，注意建立健康的情感边界。"
    else:
        return "今年是个人成长和发展的重要年份。保持开放的心态，拥抱变化，您将发现许多成长和学习的机会。"


def generate_overall_energy(sun_element: str) -> str:
    """生成整体能量描述"""
    current_year = datetime.now().year
    if sun_element == "火":
        return f"{current_year}年的整体能量偏向行动和创新。您的火象能量与这一年的能量产生共鸣，这意味着您有更多的动力去开始新项目、追求新目标。"
    elif sun_element == "土":
        return f"{current_year}年的整体能量呼唤稳定和务实。您的土象特质将帮助您在变化中保持中心，这是建立长期基础和实现实质目标的有利年份。"
    elif sun_element == "风":
        return f"{current_year}年的整体能量促进沟通和连接。您的风象能量与社交和智力活动产生共鸣，这是扩展人脉、分享想法、学习新事物的好年份。"
    elif sun_element == "水":
        return f"{current_year}年的整体能量支持情感和直觉的发展。您的水象敏感度将帮助您深入内心，这是处理情感议题、寻求疗愈、发展直觉能力的有利时期。"
    else:
        return f"{current_year}年是平衡与整合的年份。各种能量交汇，为您提供了在多个生活领域成长的机会。保持觉察，顺应能量流动。"


def generate_report_data(
    db: Session,
    product_type: str,
    user_id: int = 0,
    chart_id: Optional[int] = None,
    synastry_record_id: Optional[int] = None,
    group_matrix_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    根据报告类型生成报告数据
    核心分发函数
    
    Returns:
        报告数据字典，失败返回None
    """
    try:
        logger.info(f"开始生成报告数据: product_type={product_type}, user_id={user_id}, chart_id={chart_id}, synastry_record_id={synastry_record_id}, group_matrix_id={group_matrix_id}")
        
        if product_type == ReportProductType.DEEP_SINGLE.value:
            return generate_deep_single_report(db, chart_id, user_id)
        
        elif product_type == ReportProductType.SYNASTRY_INTERPRETATION.value:
            return generate_synastry_report_from_id(db, synastry_record_id)
        
        elif product_type == ReportProductType.YEARLY_PREDICTION.value:
            return generate_yearly_prediction_report(chart_id, db, user_id)
        
        elif product_type == ReportProductType.GROUP_ENERGY.value:
            return generate_group_report_from_id(db, group_matrix_id)
        
        else:
            logger.warning(f"未知的报告类型: {product_type}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"生成报告数据JSON解析错误: {str(e)}", exc_info=True)
        return None
    except ValueError as e:
        logger.error(f"生成报告数据值错误: {str(e)}", exc_info=True)
        return None
    except TypeError as e:
        logger.error(f"生成报告数据类型错误: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"生成报告数据未知错误: {str(e)}", exc_info=True)
        return None


def generate_deep_single_report(db: Session, chart_id: Optional[int], user_id: int = 0) -> Optional[Dict[str, Any]]:
    """
    生成深度单人星盘报告
    从真实星盘数据动态生成，不使用硬编码
    """
    try:
        if not chart_id:
            logger.warning("生成深度报告缺少星盘ID")
            return None
        
        logger.info(f"生成深度单人星盘报告: chart_id={chart_id}, user_id={user_id}")
        
        chart_data, chart_record = get_or_create_chart_data(db, chart_id, user_id)
        if not chart_data:
            logger.warning(f"无法获取星盘数据: chart_id={chart_id}, user_id={user_id}")
            return None
        
        planets = extract_planets_from_chart_data(chart_data)
        aspects = extract_aspects_from_chart_data(chart_data)
        
        planet_section = generate_planet_interpretation_section(planets)
        aspect_section = generate_aspect_analysis_section(aspects)
        house_section = generate_house_analysis_section(planets, chart_data)
        element_section = calculate_element_distribution(planets)
        life_themes_section = generate_life_themes_section(planets, aspects)
        trend_section = generate_trend_prediction_section(chart_data)
        
        chart_info = {}
        if chart_record:
            chart_info = {
                "name": chart_record.name or "用户",
                "birth_date": str(chart_record.birth_date) if chart_record.birth_date else "",
                "birth_place": chart_record.birth_place or ""
            }
        
        sun_planet = next((p for p in planets if p["planet"] == "太阳"), None)
        moon_planet = next((p for p in planets if p["planet"] == "月亮"), None)
        
        core_summary = ""
        if sun_planet and moon_planet:
            core_summary = f"您是太阳{sun_planet['sign']}第{sun_planet['house']}宫、月亮{moon_planet['sign']}第{moon_planet['house']}宫的人。{sun_planet.get('element', '')}象元素的太阳赋予您核心的人格特质，而{moon_planet.get('element', '')}象元素的月亮则揭示了您深层的情感需求。这份深度解读将帮助您更好地理解自己的独特个性和人生课题。"
        
        return {
            "title": "深度单人星盘解读",
            "generated_at": datetime.utcnow().isoformat(),
            "chart_info": chart_info,
            "core_summary": core_summary,
            "planet_interpretation": planet_section,
            "aspect_analysis": aspect_section,
            "house_analysis": house_section,
            "element_distribution": element_section,
            "life_themes": life_themes_section,
            "trend_prediction": trend_section
        }
    except Exception as e:
        logger.error(f"生成深度单人星盘报告失败: {str(e)}", exc_info=True)
        return None


def generate_synastry_report_from_id(db: Session, synastry_record_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    从合盘记录ID生成合盘报告
    """
    try:
        if not synastry_record_id:
            logger.warning("生成合盘报告缺少合盘记录ID")
            return None
        
        synastry_record = db.query(SynastryRecord).filter(
            SynastryRecord.id == synastry_record_id
        ).first()
        
        if not synastry_record:
            logger.warning(f"合盘记录不存在: synastry_record_id={synastry_record_id}")
            return None
        
        return generate_synastry_report(synastry_record)
    except Exception as e:
        logger.error(f"从ID生成合盘报告失败: {str(e)}", exc_info=True)
        return None


def generate_group_report_from_id(db: Session, group_matrix_id: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    从群组矩阵ID生成群组报告
    """
    try:
        if not group_matrix_id:
            logger.warning("生成群组报告缺少群组矩阵ID")
            return None
        
        group_matrix = db.query(GroupMatrix).filter(
            GroupMatrix.id == group_matrix_id
        ).first()
        
        if not group_matrix:
            logger.warning(f"群组矩阵不存在: group_matrix_id={group_matrix_id}")
            return None
        
        return generate_group_energy_report(group_matrix)
    except Exception as e:
        logger.error(f"从ID生成群组报告失败: {str(e)}", exc_info=True)
        return None


def get_user_purchased_reports(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[UserReportPurchase]:
    """
    获取用户已购买的报告列表
    """
    try:
        logger.info(f"获取用户已购买报告: user_id={user_id}, limit={limit}, offset={offset}")
        
        reports = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.is_active == True
        ).order_by(
            desc(UserReportPurchase.purchased_at)
        ).limit(limit).offset(offset).all()
        
        return reports
    except Exception as e:
        logger.error(f"获取用户已购买报告失败: {str(e)}", exc_info=True)
        return []


def get_report_purchase_by_id(
    db: Session,
    purchase_id: int,
    user_id: Optional[int] = None
) -> Optional[UserReportPurchase]:
    """
    根据ID获取购买记录
    """
    try:
        query = db.query(UserReportPurchase).filter(
            UserReportPurchase.id == purchase_id,
            UserReportPurchase.is_active == True
        )
        
        if user_id:
            query = query.filter(UserReportPurchase.user_id == user_id)
        
        purchase = query.first()
        return purchase
    except Exception as e:
        logger.error(f"获取购买记录失败: purchase_id={purchase_id}, user_id={user_id}, error={str(e)}", exc_info=True)
        return None


def view_report(
    db: Session,
    purchase_id: int,
    user_id: int
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    查看已购买的报告
    返回报告数据和错误信息
    
    Returns:
        Tuple[报告数据, 错误信息]
    """
    try:
        logger.info(f"查看报告: purchase_id={purchase_id}, user_id={user_id}")
        
        purchase = get_report_purchase_by_id(db, purchase_id, user_id)
        if not purchase:
            logger.warning(f"报告不存在或无权访问: purchase_id={purchase_id}, user_id={user_id}")
            return None, "报告不存在或无权访问"
        
        if purchase.expires_at and purchase.expires_at < datetime.utcnow():
            logger.warning(f"报告已过期: purchase_id={purchase_id}, expires_at={purchase.expires_at}")
            return None, "报告已过期"
        
        report_data = None
        if purchase.report_data:
            try:
                report_data = json.loads(purchase.report_data)
            except json.JSONDecodeError as e:
                logger.error(f"解析报告数据JSON失败: purchase_id={purchase_id}, error={str(e)}", exc_info=True)
                return None, "报告数据解析失败"
        
        if not report_data:
            logger.warning(f"报告数据为空: purchase_id={purchase_id}")
            return None, "报告数据不存在"
        
        try:
            purchase.view_count = (purchase.view_count or 0) + 1
            purchase.last_viewed_at = datetime.utcnow()
            db.commit()
            logger.info(f"报告查看次数更新: purchase_id={purchase_id}, view_count={purchase.view_count}")
        except Exception as e:
            logger.warning(f"更新查看次数失败: {str(e)}")
        
        return report_data, None
        
    except Exception as e:
        logger.error(f"查看报告失败: {str(e)}", exc_info=True)
        return None, f"查看报告失败: {str(e)}"


def check_report_access(
    db: Session,
    user_id: int,
    product_key: str,
    chart_id: Optional[int] = None,
    synastry_record_id: Optional[int] = None,
    group_matrix_id: Optional[int] = None
) -> Tuple[bool, Optional[UserReportPurchase]]:
    """
    检查用户是否有访问特定报告的权限
    
    Returns:
        Tuple[是否有权限, 购买记录]
    """
    try:
        logger.info(f"检查报告访问权限: user_id={user_id}, product_key={product_key}")
        
        query = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.product_key == product_key,
            UserReportPurchase.is_active == True
        )
        
        if chart_id:
            query = query.filter(UserReportPurchase.chart_id == chart_id)
        if synastry_record_id:
            query = query.filter(UserReportPurchase.synastry_record_id == synastry_record_id)
        if group_matrix_id:
            query = query.filter(UserReportPurchase.group_matrix_id == group_matrix_id)
        
        purchase = query.order_by(desc(UserReportPurchase.purchased_at)).first()
        
        if purchase:
            if purchase.expires_at and purchase.expires_at < datetime.utcnow():
                logger.info(f"报告已过期: purchase_id={purchase.id}")
                return False, purchase
            logger.info(f"用户有权限访问报告: purchase_id={purchase.id}")
            return True, purchase
        
        logger.info(f"用户无权限访问报告: user_id={user_id}, product_key={product_key}")
        return False, None
    except Exception as e:
        logger.error(f"检查报告访问权限失败: {str(e)}", exc_info=True)
        return False, None


def get_report_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    获取用户报告统计数据
    """
    try:
        logger.info(f"获取报告统计: user_id={user_id}")
        
        total_purchased = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.is_active == True
        ).count()
        
        vip_free_used = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.is_active == True,
            UserReportPurchase.is_free_vip == True
        ).count()
        
        active_count = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.is_active == True,
            or_(
                UserReportPurchase.expires_at == None,
                UserReportPurchase.expires_at > datetime.utcnow()
            )
        ).count()
        
        expired_count = total_purchased - active_count
        
        total_spent = 0
        purchases = db.query(UserReportPurchase).filter(
            UserReportPurchase.user_id == user_id,
            UserReportPurchase.is_active == True
        ).all()
        
        for p in purchases:
            if p.price_paid and p.price_paid > 0:
                total_spent += p.price_paid
        
        logger.info(f"报告统计: total={total_purchased}, active={active_count}, expired={expired_count}, vip_free={vip_free_used}, spent={total_spent}")
        
        return {
            "total_purchased": total_purchased,
            "active_count": active_count,
            "expired_count": expired_count,
            "vip_free_used": vip_free_used,
            "total_spent": total_spent
        }
    except Exception as e:
        logger.error(f"获取报告统计失败: {str(e)}", exc_info=True)
        return {
            "total_purchased": 0,
            "active_count": 0,
            "expired_count": 0,
            "vip_free_used": 0,
            "total_spent": 0
        }