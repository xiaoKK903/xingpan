from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, conversations, messages, chat, astro, geo, charts, reports, synastry, ai_interpretation, daily_horoscope, synastry_analysis, transit

app = FastAPI(
    title="AI智能客服系统",
    description="基于FastAPI的AI智能客服系统后端API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["会话管理"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息管理"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天接口"])
app.include_router(astro.router, prefix="/api/astro", tags=["星盘计算"])
app.include_router(geo.router, prefix="/api/geo", tags=["地理编码"])
app.include_router(charts.router, prefix="/api/charts", tags=["星盘存档"])
app.include_router(reports.router, prefix="/api/reports", tags=["报告生成"])
app.include_router(synastry.router, prefix="/api/synastry", tags=["双人合盘"])
app.include_router(ai_interpretation.router, prefix="/api/ai", tags=["AI解读"])
app.include_router(daily_horoscope.router, prefix="/api/horoscope", tags=["每日运势"])
app.include_router(synastry_analysis.router, prefix="/api/synastry-analysis", tags=["合盘深度分析"])
app.include_router(transit.router, prefix="/api/transit", tags=["行运气象站"])


@app.get("/")
def root():
    return {"message": "AI智能客服系统运行中", "version": "1.0.0"}
