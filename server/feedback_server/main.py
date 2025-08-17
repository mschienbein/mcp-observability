import uvicorn
from .app import app

if __name__ == "__main__":
    uvicorn.run("server.feedback_server.main:app", host="0.0.0.0", port=3003, reload=True)
