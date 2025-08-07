"""
Health check endpoint
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Join0 Semantic Search API is running",
        "timestamp": datetime.now().isoformat()
    }
