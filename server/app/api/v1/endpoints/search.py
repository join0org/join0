"""
Search endpoints for semantic and SQL queries
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.services.search_service import SearchService
from app.models.schemas import SearchRequest, SearchResponse

router = APIRouter()


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str
    limit: Optional[int] = 5
    threshold: Optional[float] = 0.5


class SQLQueryRequest(BaseModel):
    """Request model for SQL query generation"""
    natural_query: str
    table_context: Optional[Dict[str, Any]] = None


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    """
    Perform semantic search on Excel data
    
    Example queries:
    - "who did the best sales from the sales team?"
    - "which region has the highest performance?"
    - "show me underperforming representatives"
    """
    try:
        search_service = SearchService(db)
        
        result = await search_service.semantic_search(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing semantic search: {str(e)}"
        )


@router.post("/sql-query")
async def generate_sql_query(
    request: SQLQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate and execute SQL query from natural language
    
    This endpoint:
    1. Converts natural language to SQL
    2. Executes the query safely
    3. Returns results with context
    """
    try:
        search_service = SearchService(db)
        
        result = await search_service.natural_language_to_sql(
            query=request.natural_query,
            table_context=request.table_context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SQL query: {str(e)}"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="Partial query for suggestions"),
    limit: int = Query(5, description="Number of suggestions to return")
) -> List[str]:
    """Get search suggestions based on available data"""
    try:
        search_service = SearchService()
        suggestions = await search_service.get_suggestions(query, limit)
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting suggestions: {str(e)}"
        )
