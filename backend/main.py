from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import workspaces, projects, work_logs, conversations, knowledge, reports, briefings, chat, auth
import uvicorn
from .config import settings

app = FastAPI(title="Personal AI Assistant API")

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(projects.router)
app.include_router(work_logs.router)
app.include_router(conversations.router)
app.include_router(knowledge.router)
app.include_router(reports.router)
app.include_router(briefings.router)
app.include_router(chat.router)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Personal AI Assistant API is running"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", settings.app_port))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
