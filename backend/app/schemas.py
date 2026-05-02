from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class HouseSystemEnum(str, Enum):
    placidus = "placidus"
    whole_sign = "whole_sign"


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConversationBase(BaseModel):
    title: str = Field("新会话", max_length=200, description="会话标题")


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class MessageCreate(MessageBase):
    conversation_id: int = Field(..., description="会话ID")


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = Field(None, description="会话ID，不传则新建会话")
    message: str = Field(..., description="用户消息")


class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse


class ChartCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="星盘名称/备注")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    birth_place: Optional[str] = Field(None, max_length=100, description="出生地点")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")


class ChartUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    house_system: Optional[str] = None


class ChartResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str]
    birth_date: str
    birth_time: str
    birth_place: Optional[str]
    latitude: float
    longitude: float
    house_system: str
    chart_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SynastryPersonInput(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="人物名称")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    birth_place: Optional[str] = Field(None, max_length=100, description="出生地点")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")


class SynastryCalculateRequest(BaseModel):
    person_a: SynastryPersonInput = Field(..., description="人物A的星盘信息")
    person_b: SynastryPersonInput = Field(..., description="人物B的星盘信息")


class GroupMemberInput(BaseModel):
    name: str = Field(..., max_length=100, description="成员名称")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    birth_place: Optional[str] = Field(None, max_length=100, description="出生地点")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")
    is_core: bool = Field(False, description="是否为核心成员")
    weight: float = Field(1.0, description="权重，核心成员权重更高")


class GroupMatrixCalculateRequest(BaseModel):
    group_name: str = Field("未命名群组", max_length=200, description="群组名称")
    group_type: str = Field("other", description="群组类型: team/friends/roommates/lovers/other")
    description: Optional[str] = Field(None, description="群组描述")
    members: List[GroupMemberInput] = Field(..., min_items=2, description="成员列表，至少2人")


class VIPPlanType(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class VIPPrivilegeType(str, Enum):
    NO_ADS = "no_ads"
    BLIND_BOX_EXTRA = "blind_box_extra"
    BLIND_BOX_DISCOUNT = "blind_box_discount"
    UNLIMITED_SYNASTRY = "unlimited_synastry"
    ADVANCED_HOROSCOPE = "advanced_horoscope"
    EXCLUSIVE_SKIN = "exclusive_skin"
    SOCIAL_WEIGHT = "social_weight"
    FREE_REPORTS = "free_reports"


class VIPPlanResponse(BaseModel):
    id: int
    plan_type: str
    name: str
    description: Optional[str] = None
    price: int
    original_price: Optional[int] = None
    duration_days: int
    is_active: bool
    sort_order: int
    
    class Config:
        from_attributes = True


class VIPPrivilegeResponse(BaseModel):
    id: int
    privilege_key: str
    name: str
    description: Optional[str] = None
    privilege_type: str
    value_data: Optional[dict] = None
    icon: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class UserVIPResponse(BaseModel):
    id: int
    user_id: int
    is_vip: bool
    plan_type: Optional[str] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    total_subscriptions: int
    total_paid: int
    auto_renew_enabled: bool
    last_renewed_at: Optional[datetime] = None
    monthly_free_reports_used: int
    monthly_free_reports_reset_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VIPSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    subscription_no: str
    plan_type: str
    price: int
    discount_amount: int
    duration_days: int
    started_at: datetime
    expires_at: datetime
    status: str
    is_auto_renew: bool
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class GiftType(str, Enum):
    STARDUST_BOUQUET = "stardust_bouquet"
    ENERGY_CRYSTAL = "energy_crystal"
    LIMITED_CARD_FRAME = "limited_card_frame"


class GiftResponse(BaseModel):
    id: int
    gift_key: str
    name: str
    description: Optional[str] = None
    gift_type: str
    price: int
    currency_type: str
    rarity: str
    animation_effect: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool
    is_limited: bool
    stock_remaining: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    sort_order: int
    
    class Config:
        from_attributes = True


class GiftSendRequest(BaseModel):
    gift_id: int = Field(..., description="礼物ID")
    receiver_id: Optional[int] = Field(None, description="接收者用户ID（优先使用）")
    receiver_identifier: Optional[str] = Field(None, description="接收者用户ID或用户名（当 receiver_id 为空时使用）")
    quantity: int = Field(1, ge=1, description="赠送数量")
    message: Optional[str] = Field(None, max_length=500, description="附言")
    is_anonymous: bool = Field(False, description="是否匿名赠送")


class GiftTransactionResponse(BaseModel):
    id: int
    transaction_no: str
    sender_id: int
    receiver_id: int
    gift_id: int
    gift_name: str
    gift_key: str
    quantity: int
    price_per_unit: int
    total_price: int
    currency_type: str
    message: Optional[str] = None
    is_anonymous: bool
    is_displayed: bool
    displayed_at: Optional[datetime] = None
    created_at: datetime
    
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserGiftDisplayResponse(BaseModel):
    id: int
    user_id: int
    gift_transaction_id: int
    gift_key: str
    gift_name: str
    sender_name: Optional[str] = None
    is_featured: bool
    display_order: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportProductType(str, Enum):
    DEEP_SINGLE = "deep_single"
    SYNASTRY_INTERPRETATION = "synastry_interpretation"
    YEARLY_PREDICTION = "yearly_prediction"
    GROUP_ENERGY = "group_energy"


class ReportProductResponse(BaseModel):
    id: int
    product_key: str
    name: str
    description: Optional[str] = None
    product_type: str
    price: int
    original_price: Optional[int] = None
    currency_type: str
    report_template: Optional[str] = None
    sections_included: Optional[List[str]] = None
    is_active: bool
    sort_order: int
    icon_url: Optional[str] = None
    preview_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportPurchaseRequest(BaseModel):
    product_id: int = Field(..., description="报告产品ID")
    chart_id: Optional[int] = Field(None, description="星盘ID（单人报告用）")
    synastry_record_id: Optional[int] = Field(None, description="合盘记录ID（合盘报告用）")
    group_matrix_id: Optional[int] = Field(None, description="群组矩阵ID（群组报告用）")
    use_free_vip: bool = Field(False, description="是否使用VIP免费报告权益")


class UserReportPurchaseResponse(BaseModel):
    id: int
    purchase_no: str
    user_id: int
    product_id: int
    product_key: str
    product_name: str
    price_paid: int
    currency_type: str
    is_free_vip: bool
    chart_id: Optional[int] = None
    synastry_record_id: Optional[int] = None
    group_matrix_id: Optional[int] = None
    report_data: Optional[dict] = None
    report_pdf_url: Optional[str] = None
    view_count: int
    last_viewed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    VIP_SUBSCRIPTION = "vip_subscription"
    GIFT_PURCHASE = "gift_purchase"
    REPORT_PURCHASE = "report_purchase"
    STARDUST_RECHARGE = "stardust_recharge"


class PaymentOrderCreate(BaseModel):
    payment_type: str = Field(..., description="支付类型")
    related_type: Optional[str] = Field(None, description="关联类型")
    related_id: Optional[int] = Field(None, description="关联ID")
    amount: int = Field(..., gt=0, description="金额（分）")
    payment_method: Optional[str] = Field(None, description="支付方式")


class PaymentOrderResponse(BaseModel):
    id: int
    order_no: str
    user_id: int
    payment_type: str
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    amount: int
    currency: str
    discount_amount: int
    final_amount: int
    payment_method: Optional[str] = None
    payment_platform: Optional[str] = None
    platform_order_no: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    is_sandbox: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentSimulateRequest(BaseModel):
    order_no: str = Field(..., description="订单号")
    success: bool = Field(True, description="是否模拟支付成功")


class UserVIPWithPrivilegesResponse(BaseModel):
    vip_status: UserVIPResponse
    privileges: List[VIPPrivilegeResponse]
    current_plan: Optional[VIPPlanResponse] = None
    days_remaining: Optional[int] = None


class GiftShopResponse(BaseModel):
    gifts: List[GiftResponse]
    user_balance: dict


class ReportShopResponse(BaseModel):
    products: List[ReportProductResponse]
    user_vip: Optional[UserVIPResponse] = None
    free_reports_remaining: int = 0


class CheckInRewardType(str, Enum):
    STARDUST_FRAGMENT = "stardust_fragment"
    PROPHECY_TICKET = "prophecy_ticket"
    COUPON = "coupon"
    BENEFIT = "benefit"
    BLIND_BOX = "blind_box"
    VIP_TRIAL = "vip_trial"


class CheckInRewardResponse(BaseModel):
    id: int
    day_number: int
    reward_type: str
    reward_amount: int
    reward_value: Optional[dict] = None
    reward_name: str
    reward_description: Optional[str] = None
    icon: Optional[str] = None
    rarity: str
    is_active: bool
    
    class Config:
        from_attributes = True


class CheckInRecordResponse(BaseModel):
    id: int
    user_id: int
    checkin_date: str
    checkin_at: Optional[datetime] = None
    streak_day_number: int
    reward_claimed: bool
    reward_type: Optional[str] = None
    reward_amount: Optional[int] = None
    reward_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CheckInProgressResponse(BaseModel):
    id: int
    user_id: int
    current_streak: int
    best_streak: int
    last_checkin_at: Optional[datetime] = None
    last_checkin_date: Optional[str] = None
    total_checkins: int
    total_rewards_claimed: int
    
    class Config:
        from_attributes = True


class CheckInStatusResponse(BaseModel):
    has_checked_in_today: bool
    current_streak: int
    best_streak: int
    total_checkins: int
    last_checkin_at: Optional[datetime] = None
    next_reward: Optional[CheckInRewardResponse] = None
    today_reward: Optional[CheckInRewardResponse] = None
    all_rewards: List[CheckInRewardResponse]
    recent_history: List[CheckInRecordResponse]


class CheckInPerformResponse(BaseModel):
    checkin_record: CheckInRecordResponse
    current_streak: int
    best_streak: int
    reward: CheckInRewardResponse
    reward_result: Optional[dict] = None


class CheckInHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    records: List[CheckInRecordResponse]
