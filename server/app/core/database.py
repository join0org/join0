"""
Database setup and configuration
"""
import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

# SQLAlchemy setup
engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.DEBUG
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


# ChromaDB setup
def get_chroma_client():
    """Get ChromaDB client"""
    client = chromadb.Client(ChromaSettings(
        anonymized_telemetry=False
    ))
    return client


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully")


def get_vector_db():
    """Get ChromaDB collection for vector storage"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"description": "Excel semantic search embeddings"}
    )
    return collection
