"""
Quick Start Guide for Join0 Semantic Search

This script helps you get started with the semantic search system.
"""

print("""
🚀 JOIN0 SEMANTIC SEARCH - QUICK START GUIDE
==============================================

✅ Your system is ready to use! Here's how to get started:

📋 PREREQUISITES COMPLETED:
- ✅ FastAPI backend structure created
- ✅ Streamlit testing interface ready  
- ✅ Excel processing service working
- ✅ Database models and APIs configured
- ✅ Dependencies installed with uv

🔑 IMPORTANT: Set up your Google API Key
1. Get a Google API key from: https://makersuite.google.com/app/apikey
2. Edit the .env file in this directory
3. Replace 'your_google_api_key_here' with your actual API key

🚀 START THE SYSTEM:

Option 1 - Using startup script (Recommended):
   ./start_server.sh     # On Linux/Mac
   bash start_server.sh  # On Windows with Git Bash

Option 2 - Manual startup:
   Terminal 1: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   Terminal 2: uv run streamlit run streamlit_app.py

🌐 ACCESS POINTS:
- FastAPI Server: http://localhost:8000
- API Docs: http://localhost:8000/docs  
- Streamlit Interface: http://localhost:8501

📊 TEST WITH SAMPLE DATA:
Your sample Excel data structure should look like:

   Rep Name    | Region | Quota  | Actual Sales | Performance %
   ------------|--------|--------|--------------|---------------
   Alice Smith | North  | 120000 | 135000       | 1.125
   Bob Lee     | South  | 100000 | 95000        | 0.95
   ...         | ...    | ...    | ...          | ...

🔍 EXAMPLE QUERIES TO TRY:
- "Who did the best sales from the sales team?"
- "Which region has the highest performance?"
- "Show me representatives who exceeded their quota"
- "What's the average performance in the North region?"

💡 HOW IT WORKS:
1. Upload your Excel file via Streamlit or API
2. Headers (row 1) get embedded for context
3. Text data gets embedded using Google Gemini AI
4. Numerical data stored as metadata for calculations
5. Ask questions in natural language
6. Get intelligent answers with source references

🛠️ TROUBLESHOOTING:
- If ChromaDB errors: The system uses embedded ChromaDB (no separate install needed)
- If import errors: Run 'uv sync' to ensure all dependencies are installed
- If Google API errors: Check your API key and ensure billing is enabled
- If port conflicts: Change ports in the startup commands

📚 ARCHITECTURE OVERVIEW:
- FastAPI: RESTful API backend
- ChromaDB: Vector database for embeddings
- SQLAlchemy: Metadata storage and SQL queries  
- Google Gemini: Text embeddings and NLP
- Streamlit: User-friendly testing interface

🎯 KEY FEATURES IMPLEMENTED:
✅ Excel/CSV file upload and processing
✅ Text vs numerical data separation
✅ Semantic search with vector similarity
✅ Natural language to SQL conversion
✅ Query result visualization
✅ Source attribution and scoring
✅ Search suggestions and optimization

Ready to start? Run the system and upload your first Excel file! 🚀
""")
