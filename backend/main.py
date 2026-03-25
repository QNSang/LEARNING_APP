from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from routers import upload, graph, ai, documents

app = FastAPI(title="KnowledgeMap API")

app.include_router(upload.router)
app.include_router(graph.router)
app.include_router(ai.router)
app.include_router(documents.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "KnowledgeMap API is running"}

if __name__ == "__main__":
    # Exclude 'uploads' directory from reloading to prevent restart on every file upload
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True, 
        reload_excludes=["uploads/*", "logs/*", "*.log"],
        log_level="info", 
        access_log=True
    )
