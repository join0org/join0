"""
File upload endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.database import get_db
from app.services.excel_processor import ExcelProcessor
from app.services.embedding_service import EmbeddingService

router = APIRouter()


@router.post("/excel")
async def upload_excel_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload and process Excel file for semantic search
    
    This endpoint:
    1. Validates the uploaded file
    2. Extracts headers and data
    3. Separates text and numerical data
    4. Creates embeddings for text data
    5. Stores metadata for numerical data
    """
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only Excel (.xlsx, .xls) and CSV files are supported."
        )
    
    try:
        # Initialize processors
        excel_processor = ExcelProcessor()
        embedding_service = EmbeddingService()
        
        # Process the uploaded file
        file_content = await file.read()
        
        # Extract data from Excel
        extracted_data = await excel_processor.process_file(
            file_content, 
            filename=file.filename
        )
        
        # Create embeddings and store data
        result = await embedding_service.process_and_store_data(
            extracted_data, 
            db, 
            file.filename
        )
        
        return {
            "message": "File processed successfully",
            "filename": file.filename,
            "headers": extracted_data["headers"],
            "rows_processed": extracted_data["row_count"],
            "embeddings_created": result["embeddings_count"],
            "metadata_records": result["metadata_count"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
