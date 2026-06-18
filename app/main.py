from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.documents import router

app = FastAPI(
    title="ChunkLab API",
    description="Advanced RAG chunking experiments — learn by building",
    version="1.0.0",
)

# Allow Flutter (running on device/emulator) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["documents"])


@app.get("/")
def root():
    return {
        "message": "ChunkLab API is running",
        "docs": "Visit /docs for the interactive API explorer",
        "strategies_available": ["fixed"],
        "strategies_coming": ["parent_child", "semantic", "late"],
    }