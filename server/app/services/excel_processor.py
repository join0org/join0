"""
Excel file processor service

This service handles:
- Reading Excel/CSV files
- Extracting headers (row 1)
- Separating text and numerical data
- Data validation and preprocessing
"""
import pandas as pd
import numpy as np
import hashlib
import io
from typing import Dict, List, Any, Optional, Union
import re

from app.models.schemas import ProcessedExcelData, ExcelDataPoint
from app.core.config import settings


class ExcelProcessor:
    """Excel file processing service"""
    
    def __init__(self):
        self.supported_extensions = settings.ALLOWED_FILE_EXTENSIONS
        
    async def process_file(
        self, 
        file_content: bytes, 
        filename: str
    ) -> ProcessedExcelData:
        """
        Process uploaded Excel/CSV file
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            ProcessedExcelData with separated text and numerical data
        """
        # Validate file extension
        if not self._is_supported_file(filename):
            raise ValueError(f"Unsupported file type. Supported: {self.supported_extensions}")
        
        # Create file hash for deduplication
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Read file into DataFrame
        df = await self._read_file_to_dataframe(file_content, filename)
        
        # Extract headers (first row)
        headers = self._extract_headers(df)
        
        # Process data by type
        text_data, numerical_data = await self._separate_data_types(df, headers)
        
        return ProcessedExcelData(
            filename=filename,
            headers=headers,
            text_data=text_data,
            numerical_data=numerical_data,
            row_count=len(df),
            file_hash=file_hash
        )
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if file extension is supported"""
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
    
    async def _read_file_to_dataframe(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Read file content into pandas DataFrame"""
        try:
            file_io = io.BytesIO(file_content)
            
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(file_io)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_io)
            else:
                raise ValueError(f"Unsupported file format: {filename}")
            
            # Basic validation
            if df.empty:
                raise ValueError("File is empty or could not be parsed")
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading file {filename}: {str(e)}")
    
    def _extract_headers(self, df: pd.DataFrame) -> List[str]:
        """Extract column headers"""
        headers = []
        for col in df.columns:
            # Clean header names
            header = str(col).strip()
            if header.lower() not in ['unnamed', 'index']:
                headers.append(header)
        return headers
    
    async def _separate_data_types(
        self, 
        df: pd.DataFrame, 
        headers: List[str]
    ) -> tuple[List[ExcelDataPoint], List[ExcelDataPoint]]:
        """
        Separate text and numerical data
        
        Text data -> will be embedded
        Numerical data -> stored as metadata
        """
        text_data = []
        numerical_data = []
        
        for row_idx, row in df.iterrows():
            for col_name in headers:
                if col_name not in df.columns:
                    continue
                    
                value = row[col_name]
                
                # Skip NaN values
                if pd.isna(value):
                    continue
                
                # Determine data type and create data point
                data_point = self._create_data_point(
                    row_idx=int(row_idx),
                    column_name=col_name,
                    value=value
                )
                
                if data_point.data_type == 'text':
                    text_data.append(data_point)
                elif data_point.data_type in ['number', 'percentage', 'currency']:
                    numerical_data.append(data_point)
        
        return text_data, numerical_data
    
    def _create_data_point(
        self, 
        row_idx: int, 
        column_name: str, 
        value: Any
    ) -> ExcelDataPoint:
        """Create a data point with proper type classification"""
        
        # Convert value to string for analysis
        str_value = str(value).strip()
        
        # Check if it's a number
        if self._is_numerical(value):
            return ExcelDataPoint(
                row_index=row_idx,
                column_name=column_name,
                numerical_value=float(value),
                data_type=self._classify_numerical_type(value, str_value),
                text_value=None
            )
        
        # Check if it's a formula (Excel formulas start with =)
        elif str_value.startswith('='):
            return ExcelDataPoint(
                row_index=row_idx,
                column_name=column_name,
                text_value=str_value,
                data_type='formula',
                formula=str_value,
                numerical_value=None
            )
        
        # Everything else is text
        else:
            return ExcelDataPoint(
                row_index=row_idx,
                column_name=column_name,
                text_value=str_value,
                data_type='text',
                numerical_value=None
            )
    
    def _is_numerical(self, value: Any) -> bool:
        """Check if value is numerical"""
        try:
            if pd.isna(value):
                return False
            
            # Try to convert to float
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _classify_numerical_type(self, value: Any, str_value: str) -> str:
        """Classify the type of numerical data"""
        
        # Check for percentage
        if '%' in str_value or (isinstance(value, float) and 0 <= value <= 1):
            return 'percentage'
        
        # Check for currency symbols
        currency_symbols = ['$', '€', '£', '¥', '₹']
        if any(symbol in str_value for symbol in currency_symbols):
            return 'currency'
        
        # Check if it's a ratio/decimal
        if isinstance(value, float) and '.' in str_value:
            return 'decimal'
        
        # Default to number
        return 'number'
    
    def get_sample_data(self, df: pd.DataFrame, n_rows: int = 5) -> Dict[str, Any]:
        """Get sample data for preview"""
        return {
            "headers": list(df.columns),
            "sample_rows": df.head(n_rows).to_dict('records'),
            "shape": df.shape,
            "dtypes": df.dtypes.to_dict()
        }
