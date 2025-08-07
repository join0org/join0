"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ExcelFile(Base):
    """Model for uploaded Excel files metadata"""
    __tablename__ = "excel_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    original_filename = Column(String)
    headers = Column(JSON)  # Store column headers as JSON
    row_count = Column(Integer)
    upload_timestamp = Column(DateTime, default=func.now())
    file_hash = Column(String, unique=True)  # For deduplication


class SpreadsheetData(Base):
    """Model for storing numerical data from spreadsheets"""
    __tablename__ = "spreadsheet_data"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, index=True)  # Reference to ExcelFile
    row_index = Column(Integer)
    column_name = Column(String, index=True)
    text_value = Column(Text)  # For text data that gets embedded
    numerical_value = Column(Float)  # For numerical data
    data_type = Column(String)  # 'text', 'number', 'formula', etc.
    embedding_id = Column(String)  # Reference to ChromaDB document ID
    created_at = Column(DateTime, default=func.now())


class SearchHistory(Base):
    """Model for storing search queries and results"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text)
    query_type = Column(String)  # 'semantic', 'sql', 'hybrid'
    results_count = Column(Integer)
    execution_time = Column(Float)  # in seconds
    timestamp = Column(DateTime, default=func.now())
    user_feedback = Column(String)  # 'helpful', 'not_helpful', etc.
