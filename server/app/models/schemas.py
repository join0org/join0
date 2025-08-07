"""
Pydantic schemas for request/response models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class SearchRequest(BaseModel):
    """Base search request schema"""
    query: str
    limit: Optional[int] = 5


class SearchResult(BaseModel):
    """Individual search result"""
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str
    row_index: int
    column_name: str


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time: float
    search_type: str
    suggestions: Optional[List[str]] = None


class FileUploadResponse(BaseModel):
    """Response after successful file upload"""
    message: str
    filename: str
    headers: List[str]
    rows_processed: int
    embeddings_created: int
    metadata_records: int


class SQLQueryResult(BaseModel):
    """Result from SQL query execution"""
    query: str
    generated_sql: str
    results: List[Dict[str, Any]]
    execution_time: float
    row_count: int
    explanation: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: str


class ExcelDataPoint(BaseModel):
    """Individual data point from Excel"""
    row_index: int
    column_name: str
    text_value: Optional[str] = None
    numerical_value: Optional[float] = None
    data_type: str
    formula: Optional[str] = None


class ProcessedExcelData(BaseModel):
    """Processed Excel file data"""
    filename: str
    headers: List[str]
    text_data: List[ExcelDataPoint]
    numerical_data: List[ExcelDataPoint]
    row_count: int
    file_hash: str
