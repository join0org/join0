"""
Embedding service using Google Gemini AI

This service handles:
- Creating embeddings for text data using Google Gemini
- Storing embeddings in ChromaDB
- Managing vector database operations
"""
import asyncio
from typing import List, Dict, Any, Optional
import google as genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_vector_db
from app.models.database import ExcelFile, SpreadsheetData
from app.models.schemas import ProcessedExcelData, ExcelDataPoint


class EmbeddingService:
    """Service for creating and managing embeddings"""
    
    def __init__(self):
        # Configure Google Gemini API
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.vector_db = get_vector_db()
    
    async def process_and_store_data(
        self, 
        processed_data: ProcessedExcelData, 
        db: AsyncSession,
        original_filename: str
    ) -> Dict[str, int]:
        """
        Process extracted data and store embeddings + metadata
        
        Args:
            processed_data: Processed Excel data
            db: Database session
            original_filename: Original file name
            
        Returns:
            Dictionary with counts of created records
        """
        # Store file metadata in SQL database
        excel_file = await self._store_file_metadata(db, processed_data, original_filename)
        
        # Process text data for embeddings
        embeddings_count = 0
        if processed_data.text_data:
            embeddings_count = await self._create_and_store_embeddings(
                processed_data.text_data,
                processed_data.headers,
                excel_file.id,
                db
            )
        
        # Store numerical data as metadata
        metadata_count = await self._store_numerical_metadata(
            processed_data.numerical_data,
            excel_file.id,
            db
        )
        
        return {
            "embeddings_count": embeddings_count,
            "metadata_count": metadata_count
        }
    
    async def _store_file_metadata(
        self, 
        db: AsyncSession, 
        processed_data: ProcessedExcelData,
        original_filename: str
    ) -> ExcelFile:
        """Store file metadata in SQL database"""
        
        excel_file = ExcelFile(
            filename=processed_data.filename,
            original_filename=original_filename,
            headers=processed_data.headers,
            row_count=processed_data.row_count,
            file_hash=processed_data.file_hash
        )
        
        db.add(excel_file)
        await db.commit()
        await db.refresh(excel_file)
        
        return excel_file
    
    async def _create_and_store_embeddings(
        self,
        text_data: List[ExcelDataPoint],
        headers: List[str],
        file_id: int,
        db: AsyncSession
    ) -> int:
        """
        Create embeddings for text data and store in ChromaDB
        
        Strategy:
        1. Create embeddings for headers (row 1)
        2. Create embeddings for each text value with context
        3. Store in ChromaDB with rich metadata
        """
        embeddings_count = 0
        
        # Create header embeddings (these are crucial for understanding context)
        header_text = " | ".join(headers)
        header_embedding = await self._create_embedding(f"Headers: {header_text}")
        
        # Store header embedding
        await self._store_embedding_in_chromadb(
            embedding=header_embedding,
            text=header_text,
            metadata={
                "type": "header",
                "file_id": file_id,
                "headers": headers,
                "row_index": 0,
                "column_name": "headers"
            },
            doc_id=f"file_{file_id}_headers"
        )
        embeddings_count += 1
        
        # Process text data in batches
        batch_size = 10
        for i in range(0, len(text_data), batch_size):
            batch = text_data[i:i + batch_size]
            
            # Create embeddings for batch
            batch_embeddings = await self._create_batch_embeddings(batch, headers)
            
            # Store embeddings and metadata
            for data_point, embedding in zip(batch, batch_embeddings):
                doc_id = f"file_{file_id}_row_{data_point.row_index}_col_{data_point.column_name}"
                
                # Create rich context for embedding
                context_text = self._create_context_text(data_point, headers)
                
                # Store in ChromaDB
                await self._store_embedding_in_chromadb(
                    embedding=embedding,
                    text=context_text,
                    metadata={
                        "type": "data",
                        "file_id": file_id,
                        "row_index": data_point.row_index,
                        "column_name": data_point.column_name,
                        "data_type": data_point.data_type,
                        "original_text": data_point.text_value,
                        "headers": headers
                    },
                    doc_id=doc_id
                )
                
                # Store reference in SQL database
                await self._store_data_reference(db, data_point, file_id, doc_id)
                embeddings_count += 1
        
        await db.commit()
        return embeddings_count
    
    async def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text"""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error creating embedding for text '{text[:50]}...': {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 768  # Default embedding dimension
    
    async def _create_batch_embeddings(
        self, 
        batch: List[ExcelDataPoint], 
        headers: List[str]
    ) -> List[List[float]]:
        """Create embeddings for a batch of text data points"""
        
        embeddings = []
        for data_point in batch:
            context_text = self._create_context_text(data_point, headers)
            embedding = await self._create_embedding(context_text)
            embeddings.append(embedding)
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return embeddings
    
    def _create_context_text(self, data_point: ExcelDataPoint, headers: List[str]) -> str:
        """
        Create rich context text for embedding
        
        This combines the column header with the actual value to provide
        better semantic understanding
        """
        header_context = f"Column: {data_point.column_name}"
        value_context = f"Value: {data_point.text_value}"
        
        # Add formula context if available
        if data_point.formula:
            formula_context = f"Formula: {data_point.formula}"
            return f"{header_context} | {value_context} | {formula_context}"
        
        return f"{header_context} | {value_context}"
    
    async def _store_embedding_in_chromadb(
        self,
        embedding: List[float],
        text: str,
        metadata: Dict[str, Any],
        doc_id: str
    ):
        """Store embedding in ChromaDB"""
        try:
            self.vector_db.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"Error storing embedding in ChromaDB: {str(e)}")
            raise
    
    async def _store_data_reference(
        self,
        db: AsyncSession,
        data_point: ExcelDataPoint,
        file_id: int,
        embedding_id: str
    ):
        """Store reference to embedding in SQL database"""
        
        data_record = SpreadsheetData(
            file_id=file_id,
            row_index=data_point.row_index,
            column_name=data_point.column_name,
            text_value=data_point.text_value,
            numerical_value=data_point.numerical_value,
            data_type=data_point.data_type,
            embedding_id=embedding_id
        )
        
        db.add(data_record)
    
    async def _store_numerical_metadata(
        self,
        numerical_data: List[ExcelDataPoint],
        file_id: int,
        db: AsyncSession
    ) -> int:
        """Store numerical data as metadata in SQL database"""
        
        count = 0
        for data_point in numerical_data:
            data_record = SpreadsheetData(
                file_id=file_id,
                row_index=data_point.row_index,
                column_name=data_point.column_name,
                text_value=None,
                numerical_value=data_point.numerical_value,
                data_type=data_point.data_type,
                embedding_id=None  # No embedding for pure numerical data
            )
            
            db.add(data_record)
            count += 1
        
        await db.commit()
        return count
    
    async def create_query_embedding(self, query: str) -> List[float]:
        """Create embedding for search query"""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error creating query embedding: {str(e)}")
            return [0.0] * 768
