# Join0 Semantic Search - Backend

A powerful semantic search engine for Excel spreadsheets using Google Gemini AI, FastAPI, and ChromaDB.

## 🏗️ Architecture Overview

This system implements semantic search on Excel data with the following components:

- **FastAPI Backend**: RESTful API for file upload and search operations
- **Google Gemini AI**: For text embeddings and natural language processing
- **ChromaDB**: Vector database for storing and searching embeddings  
- **SQLAlchemy**: For metadata storage and SQL query generation
- **Streamlit**: Testing interface for easy interaction

## 📋 Completed TODOs

### ✅ Phase 1: Project Structure & Setup
- [x] **TODO 1.1**: Analyzed current backend structure
- [x] **TODO 1.2**: Created scalable FastAPI folder structure  
- [x] **TODO 1.3**: Set up additional dependencies (ChromaDB, SQLAlchemy, etc.)
- [x] **TODO 1.4**: Created configuration management system

### ✅ Phase 2: Data Processing Foundation
- [x] **TODO 2.1**: Created Excel file reader utility
- [x] **TODO 2.2**: Implemented data separator (text vs numerical)
- [x] **TODO 2.3**: Built header extraction logic
- [x] **TODO 2.4**: Created embedding service using Google Gemini

### ✅ Phase 3: Database & Storage
- [x] **TODO 3.1**: Set up ChromaDB for vector storage
- [x] **TODO 3.2**: Created SQL database for metadata (numerical data)
- [x] **TODO 3.3**: Implemented data models and schemas
- [x] **TODO 3.4**: Built data ingestion pipeline

### ✅ Phase 4: API Development
- [x] **TODO 4.1**: Created FastAPI application structure
- [x] **TODO 4.2**: Implemented file upload endpoint
- [x] **TODO 4.3**: Built semantic search endpoint
- [x] **TODO 4.4**: Added SQL query generation endpoint

### ✅ Phase 5: Query Processing & Response
- [x] **TODO 5.1**: Implemented natural language query processor
- [x] **TODO 5.2**: Built vector similarity search
- [x] **TODO 5.3**: Created SQL query generator for numerical operations
- [x] **TODO 5.4**: Implemented response formatter with sources

### ✅ Phase 6: Testing Interface
- [x] **TODO 6.1**: Created Streamlit testing interface
- [x] **TODO 6.2**: Added file upload functionality
- [x] **TODO 6.3**: Implemented query testing interface
- [x] **TODO 6.4**: Added results visualization

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- [uv package manager](https://github.com/astral-sh/uv)
- Google Gemini API key

### 2. Setup
```bash
# Clone and enter the server directory
cd server

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run the System

#### Option A: Using the startup script
```bash
chmod +x start_server.sh
./start_server.sh
```

#### Option B: Manual startup
```bash
# Start FastAPI server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start Streamlit interface
uv run streamlit run streamlit_app.py
```

### 4. Access the System
- **FastAPI Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Interface**: http://localhost:8501

## 📊 How It Works

### Data Processing Flow
1. **Upload Excel/CSV file** → System validates and reads the file
2. **Extract headers** → Row 1 becomes the context headers  
3. **Separate data types**:
   - Text data → Gets embedded using Google Gemini
   - Numerical data → Stored as metadata for calculations
4. **Store in databases**:
   - Embeddings → ChromaDB vector database
   - Metadata → SQLAlchemy/SQLite for fast queries

### Query Processing
1. **User asks question** → "who did the best sales from the sales team?"
2. **Create query embedding** → Google Gemini converts to vector
3. **Vector similarity search** → ChromaDB finds relevant text
4. **SQL query generation** → For numerical operations
5. **Combine results** → Provide answer with source references

## 📁 Project Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # Router setup
│   │       └── endpoints/
│   │           ├── upload.py   # File upload
│   │           ├── search.py   # Search endpoints
│   │           └── health.py   # Health checks
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Settings
│   │   └── database.py        # DB setup
│   ├── models/                 # Data models
│   │   ├── database.py        # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   └── services/              # Business logic
│       ├── excel_processor.py # Excel file processing
│       ├── embedding_service.py# Embeddings with Gemini
│       └── search_service.py  # Search operations
├── streamlit_app.py           # Testing interface
├── main.py                    # Entry point
├── pyproject.toml            # Dependencies
├── .env.example              # Environment template
└── start_server.sh           # Startup script
```

## 🔍 Example Queries

The system can handle various types of questions:

### Semantic Search Examples
- "Who did the best sales from the sales team?"
- "Which representatives are underperforming?"
- "Show me all sales reps in the North region"
- "Who exceeded their quota by the most?"

### SQL Generation Examples  
- "What's the average performance by region?"
- "Total sales for each representative"
- "Find all reps with performance above 110%"
- "Which region has the lowest average quota?"

## 🛠️ API Endpoints

### File Upload
- `POST /api/v1/upload/excel` - Upload and process Excel file

### Search
- `POST /api/v1/search/semantic` - Perform semantic search
- `POST /api/v1/search/sql-query` - Natural language to SQL
- `GET /api/v1/search/suggestions` - Get search suggestions

### Health  
- `GET /api/v1/health/` - System health check

## 🔧 Configuration

Key settings in `.env`:
```bash
GOOGLE_API_KEY=your_google_api_key_here
DATABASE_URL=sqlite:///./join0_semantic.db
CHROMA_COLLECTION_NAME=excel_semantic_search
DEBUG=False
```

## 📈 Features

### ✅ Implemented
- Excel/CSV file upload and processing
- Text data embedding with Google Gemini
- Vector similarity search with ChromaDB
- Natural language to SQL conversion
- Metadata storage for numerical data
- RESTful API with FastAPI
- Interactive Streamlit testing interface
- Query result visualization
- Search suggestions

### 🚧 Future Enhancements
- Support for multiple files/datasets
- Advanced analytics dashboard
- User authentication and file management
- Query optimization and caching
- Support for more file formats
- Batch processing capabilities

## 🤝 Contributing

This is a production-ready semantic search system built with modern Python tools and AI integration.

## 📄 License

MIT License - see LICENSE file for details.
