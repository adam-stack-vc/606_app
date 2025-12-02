# 606 Query Analysis Tool - Streamlit App

A comprehensive Streamlit application for analyzing and evaluating the 606 query generation system. This tool allows you to test natural language questions, inspect the generated SQL queries, view results, and provide feedback for continuous improvement.

## Features

### 1. Dual Input Modes
- **Manual Entry**: Type any natural language question
- **Test Questions**: Select from pre-configured test questions in `eval/nl_sql_pairs_additional.jsonl`

### 2. Query Analysis
- **SQL Query Display**: View the generated SQL query with syntax highlighting
- **Logic Details**: Inspect the decision-making process with detailed tabs showing:
  - Triggered keywords and patterns
  - Query classification tags
  - Selected tables and heuristics
  - Query intent and dimensions
  - Operation types (aggregate, topN, etc.)

### 3. Results Display
- View SQL query results in a formatted table
- Download results as CSV
- See result counts and metadata

### 4. GenAI Response
- View natural language narrative responses
- Understand how the AI synthesizes query results

### 5. Feedback System
- Add notes for SQL queries (mistakes, improvements, etc.)
- Add notes for GenAI responses (accuracy, clarity, etc.)
- Rate overall performance (1-5 scale)
- All feedback saved to CSV for analysis

### 6. Analytics Dashboard
- Track total feedback entries
- View average ratings
- Download complete feedback history

## Installation

### Prerequisites
- Python 3.8 or higher
- FastAPI backend running (default: http://localhost:8000)
- PostgreSQL database with 606 data

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

The required packages include:
- `streamlit>=1.30.0` - Web application framework
- `requests>=2.31.0` - HTTP client for API calls
- `pandas>=2.2.0` - Data manipulation
- `python-dotenv>=1.0.0` - Environment configuration

### Step 2: Configure Environment

Create or update your `.env` file:

```bash
# Optional: Custom API URL (defaults to http://localhost:8000/ask)
API_URL=http://localhost:8000/ask

# Database and OpenAI credentials (for the backend)
OPENAI_API_KEY=your-api-key-here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password-here

# Query handler configuration
ASK_HANDLER=hybrid
USE_SEMANTIC_HINTS=false
```

### Step 3: Start the FastAPI Backend

In a separate terminal, start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

Verify the backend is running:
```bash
curl http://localhost:8000/health
```

### Step 4: Launch Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open automatically in your browser at http://localhost:8501

## Usage Guide

### Testing Queries

#### Manual Entry Mode
1. Select "Manual Entry" in the question input mode
2. Type your natural language question
3. Click "Generate Query"
4. Review the results in each section

Example questions:
- "What venue received the most volume in January 2024?"
- "PFOF for Robinhood in April 2024"
- "Top 5 brokers by PFOF in January 2024"

#### Test Questions Mode
1. Select "Select from Test Questions"
2. Choose a question from the dropdown (showing ID and question text)
3. Review the table hint and notes for context
4. Click "Generate Query"

### Understanding the Output

#### SQL Query Tab
- Shows the exact SQL query sent to the database
- Formatted with syntax highlighting for readability
- Copy-paste friendly for testing in database clients

#### Logic Details Tab
- **Classification Tags**: Shows which keywords were detected
- **Triggered Keywords**: Lists what triggered database/metric selection
- **Query Intent**: Displays the parsed semantic intent
- **Tables Queried**: Shows which tables were accessed
- **Heuristics & Calculations**: Explains the logic used (aggregations, filters, etc.)

#### SQL Results Section
- Displays query results in a paginated table
- Download button for CSV export
- Shows row count

#### GenAI Response Section
- Natural language explanation of the results
- Synthesized narrative combining multiple queries (for complex questions)

### Providing Feedback

1. **Query Notes**: Document any issues with the SQL query
   - Incorrect table selection
   - Missing filters
   - Wrong aggregations
   - Performance issues

2. **GenAI Notes**: Document any issues with the AI response
   - Inaccurate summaries
   - Unclear explanations
   - Missing context

3. **Overall Rating**: Rate the complete query generation process
   - 1 = Poor (major errors)
   - 2 = Below Average (significant issues)
   - 3 = Average (acceptable with minor issues)
   - 4 = Good (minor improvements needed)
   - 5 = Excellent (accurate and complete)

4. Click "Save Feedback" to persist all notes and ratings

### Analyzing Feedback

All feedback is saved to `query_feedback.csv` with the following fields:
- `timestamp`: When the feedback was recorded
- `question`: The natural language question
- `sql_query`: The generated SQL
- `query_type`: The routing path (direct_single, complex_multi_table, etc.)
- `sql_results_count`: Number of rows returned
- `genai_response`: The AI-generated narrative
- `query_notes`: User notes about the query
- `genai_notes`: User notes about the AI response
- `rating`: Overall rating (1-5)

View analytics in the sidebar:
- Total feedback entries
- Average rating across all queries
- Download all feedback as CSV

## File Structure

```
local_dev/
├── streamlit_app.py                    # Main Streamlit application
├── requirements.txt                    # Python dependencies
├── query_feedback.csv                  # Feedback data (generated)
├── eval/
│   └── nl_sql_pairs_additional.jsonl  # Test questions library
├── main.py                            # FastAPI backend
├── ask606_hybrid.py                   # Hybrid query handler
├── planner.py                         # Template-based SQL planner
├── sql_templates.py                   # SQL template builders
└── .env                               # Environment configuration
```

## Troubleshooting

### "API Error: Connection refused"
- Ensure the FastAPI backend is running on port 8000
- Check that `API_URL` in `.env` matches your backend URL

### "No test questions found"
- Verify `eval/nl_sql_pairs_additional.jsonl` exists
- Check file path in `JSONL_FILE` constant in `streamlit_app.py`

### "Database connection failed"
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database has required tables (`executing_bd_606`, `monthly_data`, etc.)

### Empty SQL query or results
- Check backend logs for errors
- Verify the question classification is working (check Logic Details tab)
- Try simpler questions to isolate the issue

### Streamlit not loading
```bash
# Clear Streamlit cache
streamlit cache clear

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Architecture

```
User Browser (Streamlit UI)
    ↓ HTTP POST
FastAPI Backend (/ask endpoint)
    ↓
Query Classification & Routing
    ├→ Planner (template-based SQL)
    ├→ Direct handlers (single-shot queries)
    └→ Complex multi-table (LLM synthesis)
    ↓
PostgreSQL Database
    ↓
Results + Metadata
    ↓
Streamlit UI (display & feedback)
    ↓
CSV Storage (query_feedback.csv)
```

## Query Types Explained

### Direct Single-Table
- Uses template-based planner
- Deterministic SQL generation
- Fast and accurate for standard patterns
- Examples: "PFOF for Robinhood in April 2024"

### Complex Multi-Table
- Multiple specialized queries executed
- LLM synthesis of results
- Used for trend analysis and comparisons
- Examples: "Compare PFOF trends across all brokers in 2024"

### List/Distinct
- Simple entity enumeration
- Examples: "List all venues in 2024"

## Advanced Configuration

### Custom API Endpoint
```bash
export API_URL=http://your-api-server:8000/ask
streamlit run streamlit_app.py
```

### Custom Feedback Storage
Edit `streamlit_app.py`:
```python
FEEDBACK_CSV = "custom_feedback_location.csv"
```

### Custom Test Questions
Edit or replace `eval/nl_sql_pairs_additional.jsonl`:
```json
{"id": 100, "question": "Your custom question", "table_hint": "table_name", "notes": "Description"}
```

## Contributing

When adding new features to the query system:
1. Test with the Streamlit app
2. Document any new logic details in `extract_logic_details()`
3. Add representative test questions to the JSONL file
4. Review feedback CSV for patterns in user issues

## Support

For issues or questions:
1. Check the Logic Details tab for debugging information
2. Review backend logs (`uvicorn` output)
3. Export feedback CSV for analysis
4. Check database query performance with `EXPLAIN ANALYZE`

## License

Internal tool for 606 query analysis and evaluation.
