import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from app.main import app
from app.database import Base, engine
from app.models import User, Conversation, Message, Chart, SynastryRecord

Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
