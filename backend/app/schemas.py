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
