"""
Search service for semantic and SQL-based queries

This service handles:
- Semantic search using ChromaDB and embeddings
- Natural language to SQL query conversion
- Hybrid search combining vector and SQL results
- Query suggestions and optimization
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import google as genai

from app.core.config import settings
from app.core.database import get_vector_db
from app.models.database import SpreadsheetData, ExcelFile, SearchHistory
from app.models.schemas import SearchResponse, SearchResult, SQLQueryResult
from app.services.embedding_service import EmbeddingService


class SearchService:
    """Service for handling search operations"""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.vector_db = get_vector_db()
        self.embedding_service = EmbeddingService()
        
        # Configure Gemini for text generation
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.text_model = genai.GenerativeModel('gemini-pro')
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> SearchResponse:
        """
        Perform semantic search on embedded data
        
        Process:
        1. Create query embedding
        2. Search ChromaDB for similar vectors
        3. Fetch associated metadata from SQL
        4. Format and return results
        """
        start_time = asyncio.get_event_loop().time()
        
        # Create query embedding
        query_embedding = await self.embedding_service.create_query_embedding(query)
        
        # Search ChromaDB
        chroma_results = self.vector_db.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,  # Get more results to filter
            include=["documents", "metadatas", "distances"]
        )
        
        # Process and filter results
        search_results = []
        if chroma_results and chroma_results['documents']:
            for i, (doc, metadata, distance) in enumerate(zip(
                chroma_results['documents'][0],
                chroma_results['metadatas'][0], 
                chroma_results['distances'][0]
            )):
                # Calculate similarity score (1 - distance for cosine similarity)
                score = 1 - distance
                
                # Filter by threshold
                if score < threshold:
                    continue
                
                # Get additional context from SQL database
                enhanced_metadata = await self._enhance_metadata_with_sql_context(metadata)
                
                result = SearchResult(
                    content=doc,
                    score=score,
                    metadata=enhanced_metadata,
                    source=f"Row {metadata.get('row_index', 'N/A')}, Column {metadata.get('column_name', 'N/A')}",
                    row_index=metadata.get('row_index', 0),
                    column_name=metadata.get('column_name', '')
                )
                search_results.append(result)
                
                if len(search_results) >= limit:
                    break
        
        # Generate suggestions for refinement
        suggestions = await self._generate_search_suggestions(query, search_results)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Log search history
        await self._log_search_history(query, "semantic", len(search_results), execution_time)
        
        return SearchResponse(
            query=query,
            results=search_results,
            total_results=len(search_results),
            execution_time=execution_time,
            search_type="semantic",
            suggestions=suggestions
        )
    
    async def natural_language_to_sql(
        self,
        query: str,
        table_context: Optional[Dict[str, Any]] = None
    ) -> SQLQueryResult:
        """
        Convert natural language query to SQL and execute it
        
        Examples:
        - "who did the best sales?" -> SELECT * FROM spreadsheet_data WHERE column_name='Actual Sales' ORDER BY numerical_value DESC LIMIT 1
        - "average performance in North region" -> Complex JOIN query
        """
        start_time = asyncio.get_event_loop().time()
        
        # Get database schema context
        schema_context = await self._get_database_schema_context()
        
        # Generate SQL using Gemini
        sql_query, explanation = await self._generate_sql_with_gemini(
            query, schema_context, table_context
        )
        
        # Execute SQL query safely
        results = await self._execute_sql_safely(sql_query)
        
        # Post-process results for better presentation
        processed_results = await self._post_process_sql_results(results, query)
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        # Log search history
        await self._log_search_history(query, "sql", len(processed_results), execution_time)
        
        return SQLQueryResult(
            query=query,
            generated_sql=sql_query,
            results=processed_results,
            execution_time=execution_time,
            row_count=len(processed_results),
            explanation=explanation
        )
    
    async def _enhance_metadata_with_sql_context(
        self, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance ChromaDB metadata with additional SQL context"""
        if not self.db:
            return metadata
        
        try:
            # Get related numerical data from the same row
            query = text("""
                SELECT column_name, numerical_value, data_type 
                FROM spreadsheet_data 
                WHERE file_id = :file_id AND row_index = :row_index 
                AND numerical_value IS NOT NULL
            """)
            
            result = await self.db.execute(query, {
                "file_id": metadata.get("file_id"),
                "row_index": metadata.get("row_index")
            })
            
            numerical_context = {}
            for row in result:
                numerical_context[row.column_name] = {
                    "value": row.numerical_value,
                    "type": row.data_type
                }
            
            metadata["numerical_context"] = numerical_context
            return metadata
            
        except Exception as e:
            print(f"Error enhancing metadata: {str(e)}")
            return metadata
    
    async def _get_database_schema_context(self) -> str:
        """Get database schema context for SQL generation"""
        schema_info = """
        Database Schema:
        
        Table: spreadsheet_data
        Columns:
        - id (INTEGER): Primary key
        - file_id (INTEGER): Reference to excel_files table
        - row_index (INTEGER): Row number in spreadsheet (0-based)
        - column_name (VARCHAR): Name of the column/header
        - text_value (TEXT): Text content (for embedded data)
        - numerical_value (FLOAT): Numerical content (for calculations)
        - data_type (VARCHAR): Type of data (text, number, percentage, currency)
        
        Table: excel_files
        Columns:
        - id (INTEGER): Primary key
        - filename (VARCHAR): Name of the uploaded file
        - headers (JSON): Column headers as JSON array
        - row_count (INTEGER): Total number of rows
        
        Common column names in sales data:
        - Rep Name, Region, Quota, Actual Sales, Performance %
        
        Example queries:
        - Best performer: SELECT * FROM spreadsheet_data WHERE column_name='Performance %' ORDER BY numerical_value DESC LIMIT 1
        - Regional analysis: SELECT column_name, AVG(numerical_value) FROM spreadsheet_data WHERE column_name IN ('Quota', 'Actual Sales') GROUP BY column_name
        """
        return schema_info
    
    async def _generate_sql_with_gemini(
        self,
        natural_query: str,
        schema_context: str,
        table_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """Generate SQL query using Gemini AI"""
        
        prompt = f"""
        You are an expert SQL query generator. Convert the natural language query to a safe SQL query.
        
        Database Schema:
        {schema_context}
        
        Natural Language Query: {natural_query}
        
        Additional Context: {table_context or 'None'}
        
        Requirements:
        1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)
        2. Use proper JOINs when needed
        3. Include column_name filtering when looking for specific data types
        4. For performance queries, look for 'Performance %' or similar columns
        5. For sales queries, look for 'Actual Sales' or similar columns
        6. For names, look for 'Rep Name' or similar columns
        7. Always include LIMIT to prevent huge result sets
        8. Use proper aggregation functions (AVG, SUM, MAX, MIN) when appropriate
        
        Return format:
        SQL_QUERY: [your SQL query here]
        EXPLANATION: [brief explanation of what the query does]
        """
        
        try:
            response = await self.text_model.generate_content_async(prompt)
            response_text = response.text
            
            # Parse SQL query and explanation
            sql_match = re.search(r'SQL_QUERY:\s*(.*?)(?=EXPLANATION:|$)', response_text, re.DOTALL | re.IGNORECASE)
            explanation_match = re.search(r'EXPLANATION:\s*(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
            
            sql_query = sql_match.group(1).strip() if sql_match else ""
            explanation = explanation_match.group(1).strip() if explanation_match else "No explanation provided"
            
            # Clean up SQL query
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            return sql_query, explanation
            
        except Exception as e:
            print(f"Error generating SQL with Gemini: {str(e)}")
            # Return a safe default query
            return "SELECT * FROM spreadsheet_data LIMIT 10", f"Error generating query: {str(e)}"
    
    async def _execute_sql_safely(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute SQL query with safety checks"""
        if not self.db:
            return []
        
        # Safety checks
        unsafe_keywords = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = sql_query.upper()
        
        for keyword in unsafe_keywords:
            if keyword in query_upper:
                raise ValueError(f"Unsafe SQL operation detected: {keyword}")
        
        try:
            result = await self.db.execute(text(sql_query))
            rows = result.fetchall()
            
            # Convert to list of dictionaries
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            print(f"Error executing SQL: {str(e)}")
            return []
    
    async def _post_process_sql_results(
        self, 
        results: List[Dict[str, Any]], 
        original_query: str
    ) -> List[Dict[str, Any]]:
        """Post-process SQL results for better presentation"""
        if not results:
            return results
        
        # Add human-readable formatting for common queries
        for result in results:
            # Format percentages
            if 'numerical_value' in result and 'column_name' in result:
                if 'performance' in result.get('column_name', '').lower() or '%' in result.get('column_name', ''):
                    if isinstance(result['numerical_value'], (int, float)):
                        result['formatted_value'] = f"{result['numerical_value']:.2%}"
                
                # Format currency
                elif 'sales' in result.get('column_name', '').lower() or 'quota' in result.get('column_name', '').lower():
                    if isinstance(result['numerical_value'], (int, float)):
                        result['formatted_value'] = f"${result['numerical_value']:,.2f}"
        
        return results
    
    async def _generate_search_suggestions(
        self, 
        query: str, 
        results: List[SearchResult]
    ) -> List[str]:
        """Generate search suggestions based on query and results"""
        suggestions = []
        
        # Basic suggestions based on common patterns
        base_suggestions = [
            "Show me the top performers",
            "Which region has the best sales?",
            "Who is underperforming?",
            "Average performance by region",
            "Total sales by representative"
        ]
        
        # Filter out suggestions similar to current query
        for suggestion in base_suggestions:
            if not any(word in suggestion.lower() for word in query.lower().split()):
                suggestions.append(suggestion)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def _log_search_history(
        self,
        query: str,
        query_type: str,
        results_count: int,
        execution_time: float
    ):
        """Log search query for analytics"""
        if not self.db:
            return
        
        try:
            search_record = SearchHistory(
                query=query,
                query_type=query_type,
                results_count=results_count,
                execution_time=execution_time
            )
            
            self.db.add(search_record)
            await self.db.commit()
            
        except Exception as e:
            print(f"Error logging search history: {str(e)}")
    
    async def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query"""
        # This could be enhanced with ML-based suggestions
        # For now, return basic suggestions
        
        suggestions = [
            "who did the best sales from the sales team?",
            "which representative has the highest performance?",
            "show me all representatives in the North region",
            "what is the average quota by region?",
            "which region has the lowest performance?",
            "who exceeded their quota?",
            "total sales for each region",
            "performance ranking of all representatives"
        ]
        
        # Filter suggestions based on partial query
        if partial_query:
            filtered = [s for s in suggestions if partial_query.lower() in s.lower()]
            return filtered[:limit]
        
        return suggestions[:limit]
