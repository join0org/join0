"""
Streamlit interface for testing the semantic search API

This provides a user-friendly interface to:
- Upload Excel files
- Test semantic search queries
- View and analyze results
- Test SQL query generation
"""
import streamlit as st
import requests
import pandas as pd
import json
from typing import Dict, Any, List
import time
import plotly.express as px
import plotly.graph_objects as go

# Configure Streamlit page
st.set_page_config(
    page_title="Join0 Semantic Search - Excel Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


class StreamlitInterface:
    """Streamlit interface for testing semantic search"""
    
    def __init__(self):
        self.api_base = API_BASE_URL
    
    def run(self):
        """Main Streamlit app"""
        st.title("📊 Join0 Semantic Search")
        st.markdown("### Excel Data Semantic Search with Google Gemini AI")
        
        # Sidebar navigation
        with st.sidebar:
            st.image("https://via.placeholder.com/200x100/4CAF50/FFFFFF?text=Join0", width=200)
            
            page = st.selectbox(
                "Choose a function:",
                ["🏠 Home", "📤 Upload Data", "🔍 Semantic Search", "💾 SQL Queries", "📈 Analytics"]
            )
        
        # Route to different pages
        if page == "🏠 Home":
            self.home_page()
        elif page == "📤 Upload Data":
            self.upload_page()
        elif page == "🔍 Semantic Search":
            self.search_page()
        elif page == "💾 SQL Queries":
            self.sql_page()
        elif page == "📈 Analytics":
            self.analytics_page()
    
    def home_page(self):
        """Home page with information and example"""
        st.markdown("""
        ## Welcome to Join0 Semantic Search! 🚀
        
        This application allows you to perform intelligent semantic search on your Excel spreadsheets using Google Gemini AI.
        
        ### How it works:
        1. **Upload** your Excel file with data
        2. **Text data** gets embedded using Google Gemini
        3. **Numerical data** is stored as metadata for calculations
        4. **Ask questions** in natural language
        5. **Get intelligent answers** with source references
        
        ### Example Use Cases:
        - "Who did the best sales from the sales team?"
        - "Which region has the highest performance?"
        - "Show me representatives who exceeded their quota"
        - "What's the average performance in the North region?"
        """)
        
        # Sample data preview
        st.markdown("### 📋 Sample Data Structure")
        sample_data = {
            "Rep Name": ["Alice Smith", "Bob Lee", "Carlos Diaz", "Dana Kim"],
            "Region": ["North", "South", "East", "West"],
            "Quota": [120000, 100000, 110000, 130000],
            "Actual Sales": [135000, 95000, 120000, 128000],
            "Performance %": [1.125, 0.95, 1.091, 0.985]
        }
        
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)
        
        # System status
        st.markdown("### 🔧 System Status")
        self.check_system_status()
    
    def upload_page(self):
        """File upload page"""
        st.header("📤 Upload Excel Data")
        
        uploaded_file = st.file_uploader(
            "Choose your Excel or CSV file",
            type=['xlsx', 'xls', 'csv'],
            help="Upload your spreadsheet with data you want to search"
        )
        
        if uploaded_file is not None:
            # Show file info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "File type": uploaded_file.type
            }
            
            st.markdown("### 📄 File Information")
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
            
            # Preview data
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.markdown("### 👀 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Data statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Text Columns", len(df.select_dtypes(include=['object']).columns))
                with col4:
                    st.metric("Numeric Columns", len(df.select_dtypes(include=['number']).columns))
                
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return
            
            # Upload button
            if st.button("🚀 Process File", type="primary"):
                self.upload_file(uploaded_file)
    
    def search_page(self):
        """Semantic search interface"""
        st.header("🔍 Semantic Search")
        
        # Search input
        query = st.text_input(
            "Ask a question about your data:",
            placeholder="e.g., Who did the best sales from the sales team?",
            help="Use natural language to ask questions about your uploaded data"
        )
        
        # Search parameters
        col1, col2 = st.columns(2)
        with col1:
            limit = st.slider("Number of results", 1, 20, 5)
        with col2:
            threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.5)
        
        # Quick suggestion buttons
        st.markdown("### 💡 Quick Suggestions")
        suggestions = [
            "Who did the best sales from the sales team?",
            "Which region has the highest performance?",
            "Show me underperforming representatives",
            "What's the average quota by region?"
        ]
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}"):
                    query = suggestion
        
        # Perform search
        if query and st.button("🔍 Search", type="primary"):
            self.perform_semantic_search(query, limit, threshold)
    
    def sql_page(self):
        """SQL query generation interface"""
        st.header("💾 Natural Language to SQL")
        
        query = st.text_area(
            "Describe what you want to find:",
            placeholder="e.g., Find all representatives with performance above 110%",
            help="Describe your query in natural language and we'll generate SQL"
        )
        
        if query and st.button("🔄 Generate & Execute SQL", type="primary"):
            self.generate_and_execute_sql(query)
    
    def analytics_page(self):
        """Analytics and visualizations page"""
        st.header("📈 Analytics Dashboard")
        
        # This would show analytics of the uploaded data and search patterns
        st.info("Analytics dashboard will be implemented once data is uploaded and searches are performed.")
        
        # Placeholder for future analytics
        if st.button("📊 Generate Sample Analytics"):
            self.show_sample_analytics()
    
    def upload_file(self, uploaded_file):
        """Upload file to API"""
        try:
            with st.spinner("Processing file..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                response = requests.post(
                    f"{self.api_base}/upload/excel",
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ File processed successfully!")
                    
                    # Show processing results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows Processed", result["rows_processed"])
                    with col2:
                        st.metric("Embeddings Created", result["embeddings_created"])
                    with col3:
                        st.metric("Metadata Records", result["metadata_records"])
                    
                    st.markdown("### 📝 Extracted Headers")
                    st.write(result["headers"])
                    
                else:
                    st.error(f"Upload failed: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def perform_semantic_search(self, query: str, limit: int, threshold: float):
        """Perform semantic search via API"""
        try:
            with st.spinner("Searching..."):
                payload = {
                    "query": query,
                    "limit": limit,
                    "threshold": threshold
                }
                
                response = requests.post(
                    f"{self.api_base}/search/semantic",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    self.display_search_results(results)
                else:
                    st.error(f"Search failed: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def generate_and_execute_sql(self, query: str):
        """Generate and execute SQL query"""
        try:
            with st.spinner("Generating SQL..."):
                payload = {"natural_query": query}
                
                response = requests.post(
                    f"{self.api_base}/search/sql-query",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    results = response.json()
                    self.display_sql_results(results)
                else:
                    st.error(f"SQL generation failed: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def display_search_results(self, results: Dict[str, Any]):
        """Display semantic search results"""
        st.markdown(f"### 🎯 Search Results for: '{results['query']}'")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Results Found", results['total_results'])
        with col2:
            st.metric("Execution Time", f"{results['execution_time']:.3f}s")
        with col3:
            st.metric("Search Type", results['search_type'].title())
        
        # Results
        if results['results']:
            for i, result in enumerate(results['results']):
                with st.expander(f"Result {i+1} - Score: {result['score']:.3f} - {result['source']}"):
                    st.write(f"**Content:** {result['content']}")
                    st.write(f"**Source:** {result['source']}")
                    st.write(f"**Similarity Score:** {result['score']:.3f}")
                    
                    if result['metadata']:
                        st.write("**Metadata:**")
                        st.json(result['metadata'])
        else:
            st.info("No results found. Try adjusting your query or similarity threshold.")
        
        # Suggestions
        if results.get('suggestions'):
            st.markdown("### 💡 Related Suggestions")
            for suggestion in results['suggestions']:
                st.write(f"• {suggestion}")
    
    def display_sql_results(self, results: Dict[str, Any]):
        """Display SQL query results"""
        st.markdown(f"### 💾 SQL Results for: '{results['query']}'")
        
        # Show generated SQL
        st.markdown("#### Generated SQL Query")
        st.code(results['generated_sql'], language='sql')
        
        # Show explanation
        st.markdown("#### Explanation")
        st.write(results['explanation'])
        
        # Show metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rows Returned", results['row_count'])
        with col2:
            st.metric("Execution Time", f"{results['execution_time']:.3f}s")
        
        # Show results
        if results['results']:
            st.markdown("#### Query Results")
            df = pd.DataFrame(results['results'])
            st.dataframe(df, use_container_width=True)
            
            # Try to create visualizations for numerical data
            if len(df) > 0:
                numeric_columns = df.select_dtypes(include=['number']).columns
                if len(numeric_columns) > 0:
                    st.markdown("#### 📊 Visualization")
                    
                    chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter"])
                    
                    if chart_type == "Bar" and len(df) <= 20:
                        fig = px.bar(df, x=df.columns[0], y=numeric_columns[0] if len(numeric_columns) > 0 else df.columns[0])
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Query executed successfully but returned no results.")
    
    def show_sample_analytics(self):
        """Show sample analytics visualization"""
        # Create sample data for demonstration
        sample_data = {
            "Region": ["North", "South", "East", "West"],
            "Avg Performance": [1.08, 0.95, 1.12, 0.99],
            "Total Sales": [450000, 380000, 520000, 410000],
            "Rep Count": [3, 4, 2, 3]
        }
        
        df = pd.DataFrame(sample_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Performance by Region")
            fig1 = px.bar(df, x="Region", y="Avg Performance", color="Avg Performance")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.markdown("#### Sales Distribution")
            fig2 = px.pie(df, values="Total Sales", names="Region")
            st.plotly_chart(fig2, use_container_width=True)
    
    def check_system_status(self):
        """Check if the API is running"""
        try:
            response = requests.get(f"{self.api_base}/health/", timeout=5)
            if response.status_code == 200:
                st.success("✅ API is running")
                result = response.json()
                st.write(f"**Status:** {result['status']}")
                st.write(f"**Message:** {result['message']}")
            else:
                st.error("❌ API is not responding correctly")
        except requests.exceptions.RequestException:
            st.error("❌ API is not running. Please start the FastAPI server.")
            st.code("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")


def main():
    """Main function to run the Streamlit app"""
    app = StreamlitInterface()
    app.run()


if __name__ == "__main__":
    main()
