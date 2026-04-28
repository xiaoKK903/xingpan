import uvicorn
from app.main import app
from app.database import Base, engine
from app.models import User, Conversation, Message

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
