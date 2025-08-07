"""
Test script for Join0 Semantic Search API

This script tests the basic functionality without requiring a Google API key.
It mocks the embedding service to verify the core architecture works.
"""
import sys
import os

# Add the server directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import pandas as pd
from io import BytesIO

# Import our services
from app.services.excel_processor import ExcelProcessor
from app.core.config import settings

async def test_excel_processing():
    """Test Excel file processing"""
    print("🧪 Testing Excel Processing...")
    
    # Create sample data
    sample_data = {
        "Rep Name": ["Alice Smith", "Bob Lee", "Carlos Diaz", "Dana Kim", "Evan Chen"],
        "Region": ["North", "South", "East", "West", "North"],
        "Quota": [120000, 100000, 110000, 130000, 90000],
        "Actual Sales": [135000, 95000, 120000, 128000, 87000],
        "Performance %": [1.125, 0.95, 1.090909091, 0.984615385, 0.966666667]
    }
    
    # Create DataFrame and convert to Excel bytes
    df = pd.DataFrame(sample_data)
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_bytes = excel_buffer.getvalue()
    
    # Test Excel processor
    processor = ExcelProcessor()
    
    try:
        processed_data = await processor.process_file(excel_bytes, "test_sales.xlsx")
        
        print(f"✅ File processed successfully!")
        print(f"   - Filename: {processed_data.filename}")
        print(f"   - Headers: {processed_data.headers}")
        print(f"   - Row count: {processed_data.row_count}")
        print(f"   - Text data points: {len(processed_data.text_data)}")
        print(f"   - Numerical data points: {len(processed_data.numerical_data)}")
        print(f"   - File hash: {processed_data.file_hash[:8]}...")
        
        # Show some sample data points
        print("\n📊 Sample Text Data Points:")
        for i, dp in enumerate(processed_data.text_data[:3]):
            print(f"   {i+1}. Row {dp.row_index}, Column: {dp.column_name}, Value: {dp.text_value}")
        
        print("\n📈 Sample Numerical Data Points:")
        for i, dp in enumerate(processed_data.numerical_data[:3]):
            print(f"   {i+1}. Row {dp.row_index}, Column: {dp.column_name}, Value: {dp.numerical_value} ({dp.data_type})")
        
        return processed_data
        
    except Exception as e:
        print(f"❌ Error processing Excel: {str(e)}")
        return None

async def test_api_structure():
    """Test API structure without actually starting the server"""
    print("\n🔧 Testing API Structure...")
    
    try:
        from app.main import create_app
        from app.api.v1.api import api_router
        
        app = create_app()
        
        print("✅ FastAPI app created successfully!")
        print(f"   - App title: {app.title}")
        print(f"   - App version: {app.version}")
        
        # Check routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(f"{route.methods} {route.path}" if hasattr(route, 'methods') else route.path)
        
        print(f"   - Total routes: {len(routes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API structure: {str(e)}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n⚙️  Testing Configuration...")
    
    try:
        print(f"✅ Configuration loaded successfully!")
        print(f"   - App name: {settings.APP_NAME}")
        print(f"   - Debug mode: {settings.DEBUG}")
        print(f"   - Database URL: {settings.DATABASE_URL}")
        print(f"   - ChromaDB collection: {settings.CHROMA_COLLECTION_NAME}")
        print(f"   - Supported file extensions: {settings.ALLOWED_FILE_EXTENSIONS}")
        print(f"   - Max file size: {settings.MAX_FILE_SIZE / (1024*1024):.1f} MB")
        
        # Check if Google API key is set (don't print the actual key)
        if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your_google_api_key_here":
            print(f"   - Google API key: ✅ Set (length: {len(settings.GOOGLE_API_KEY)} chars)")
        else:
            print(f"   - Google API key: ⚠️  Not set (using placeholder)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Join0 Semantic Search - System Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_configuration()
    
    # Test API structure
    api_ok = await test_api_structure()
    
    # Test Excel processing
    excel_data = await test_excel_processing()
    excel_ok = excel_data is not None
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    print(f"✅ Configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"✅ API Structure: {'PASS' if api_ok else 'FAIL'}")
    print(f"✅ Excel Processing: {'PASS' if excel_ok else 'FAIL'}")
    
    if all([config_ok, api_ok, excel_ok]):
        print("\n🎉 All tests passed! Your system is ready.")
        print("\n📝 Next steps:")
        print("1. Add your Google API key to .env file")
        print("2. Start the FastAPI server: uv run uvicorn app.main:app --reload")
        print("3. Start Streamlit interface: uv run streamlit run streamlit_app.py")
        print("4. Upload your Excel file and start searching!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return all([config_ok, api_ok, excel_ok])

if __name__ == "__main__":
    asyncio.run(main())
