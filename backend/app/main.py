from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, conversations, messages, chat, astro, geo

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


@app.get("/")
def root():
    return {"message": "AI智能客服系统运行中", "version": "1.0.0"}
