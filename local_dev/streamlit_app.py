import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import os
import csv as csv_module

# IMPORTANT: Enable LLM intent extraction for Neuro-Symbolic engine
os.environ["USE_LLM_INTENT"] = "true"

# Page configuration
st.set_page_config(
    page_title="606 Query Analysis Tool",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []
if 'current_response' not in st.session_state:
    st.session_state.current_response = None
if 'query_notes' not in st.session_state:
    st.session_state.query_notes = ""
if 'genai_notes' not in st.session_state:
    st.session_state.genai_notes = ""
if 'rating' not in st.session_state:
    st.session_state.rating = 3
if 'use_semantic_hints' not in st.session_state:
    st.session_state.use_semantic_hints = False

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/ask")
FEEDBACK_CSV = "query_feedback.csv"
JSONL_FILE = "eval/nl_sql_pairs_additional.jsonl"

def load_jsonl_questions():
    """Load questions from JSONL file"""
    questions = []

    # Try multiple possible paths
    possible_paths = [
        JSONL_FILE,
        os.path.join(os.getcwd(), JSONL_FILE),
        os.path.join(os.path.dirname(__file__), JSONL_FILE),
    ]

    jsonl_path = None
    for path in possible_paths:
        if os.path.exists(path):
            jsonl_path = path
            break

    if jsonl_path is None:
        st.warning(f"JSONL file not found. Tried paths:\n" + "\n".join(f"- {p}" for p in possible_paths))
        st.info(f"Current working directory: {os.getcwd()}")
        return questions

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            line_num = 0
            for line in f:
                line_num += 1
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    questions.append({
                        'id': data.get('id'),
                        'question': data.get('question'),
                        'table_hint': data.get('table_hint'),
                        'notes': data.get('notes', '')
                    })
                except json.JSONDecodeError as e:
                    st.warning(f"Error parsing line {line_num}: {str(e)}")
                    continue

    except Exception as e:
        st.error(f"Error loading JSONL file from {jsonl_path}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

    if questions:
        # Success - silently loaded
        pass
    else:
        st.warning(f"No questions loaded from {jsonl_path}")

    return questions

def call_api(question, use_semantic_hints=False):
    """Call the FastAPI /ask endpoint"""
    try:
        response = requests.post(
            API_URL,
            json={"question": question, "use_semantic_hints": use_semantic_hints},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def extract_logic_details(response_data):
    """Extract logic details from the API response for the second tab"""
    details = {}

    # Extract classification tags
    if 'query_classification' in response_data:
        classification = response_data['query_classification']
        details['Classification Tags'] = classification

    # Extract triggered words/patterns
    if 'tags' in response_data:
        tags = response_data['tags']
        triggered_words = []

        # Analyze which keywords triggered which decisions
        if tags.get('mentions_pfof'):
            triggered_words.append("PFOF-related keywords detected")
        if tags.get('mentions_volume'):
            triggered_words.append("Volume-related keywords detected")
        if tags.get('mentions_broker'):
            triggered_words.append("Broker/executing BD keywords detected")
        if tags.get('mentions_venue'):
            triggered_words.append("Venue keywords detected")
        if tags.get('mentions_month') or tags.get('mentions_year'):
            triggered_words.append(f"Time period: {tags.get('month', 'N/A')}/{tags.get('year', 'N/A')}")

        details['Triggered Keywords'] = triggered_words
        details['All Tags'] = tags

    # Extract query intent
    if 'query_intent' in response_data:
        details['Query Intent'] = response_data['query_intent']

    # Extract query type/routing
    if 'query_type' in response_data:
        details['Query Type'] = response_data['query_type']

    # Extract table selection
    if 'table' in response_data:
        details['Selected Table'] = response_data['table']
    elif 'tables_queried' in response_data:
        details['Tables Queried'] = response_data['tables_queried']

    # Extract heuristics/calculations
    heuristics = []
    if 'semantic_hints_used' in response_data:
        heuristics.append(f"Semantic Hints: {response_data['semantic_hints_used']}")
    if 'operation' in response_data:
        heuristics.append(f"Operation: {response_data['operation']}")
    if 'metric' in response_data:
        heuristics.append(f"Metric: {response_data['metric']}")
    if 'dimensions' in response_data:
        heuristics.append(f"Dimensions: {', '.join(response_data['dimensions'])}")

    details['Heuristics & Calculations'] = heuristics if heuristics else ["No specific heuristics recorded"]

    return details

def format_logic_details(details):
    """Format logic details for display"""
    output = []

    for key, value in details.items():
        output.append(f"### {key}")

        if isinstance(value, list):
            for item in value:
                output.append(f"- {item}")
        elif isinstance(value, dict):
            output.append(f"```json\n{json.dumps(value, indent=2)}\n```")
        else:
            output.append(f"{value}")

        output.append("")  # Empty line

    return "\n".join(output)

def save_feedback():
    """Save feedback data to CSV"""
    if not st.session_state.current_response:
        return

    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': st.session_state.current_response.get('question', ''),
        'sql_query': st.session_state.current_response.get('sql', ''),
        'query_type': st.session_state.current_response.get('query_type', ''),
        'sql_results_count': len(st.session_state.current_response.get('results', [])),
        'genai_response': st.session_state.current_response.get('response', ''),
        'semantic_hints': st.session_state.current_response.get('semantic_hints_used', False),
        'query_notes': st.session_state.query_notes,
        'genai_notes': st.session_state.genai_notes,
        'rating': st.session_state.rating
    }

    # Define column order
    column_order = ['timestamp', 'question', 'sql_query', 'query_type', 'sql_results_count',
                   'genai_response', 'semantic_hints', 'query_notes', 'genai_notes', 'rating']

    # Check if file exists and has correct columns
    file_exists = os.path.exists(FEEDBACK_CSV)
    needs_migration = False

    if file_exists:
        try:
            # Only read header to check columns
            existing_df = pd.read_csv(FEEDBACK_CSV, nrows=0)
            if 'semantic_hints' not in existing_df.columns:
                needs_migration = True
        except Exception as e:
            # If we can't read the file at all, show error and don't try to save
            st.error(f"Error reading existing CSV file: {e}")
            st.error("Please run: python scripts/fix_csv.py")
            return

    # If migration needed, read old file and add semantic_hints column
    if needs_migration:
        try:
            old_df = pd.read_csv(FEEDBACK_CSV)
            old_df['semantic_hints'] = False
            # Reorder columns to match new schema
            old_df = old_df[column_order]
            old_df.to_csv(FEEDBACK_CSV, mode='w', header=True, index=False, quoting=csv_module.QUOTE_ALL)
            st.info("Migrated CSV to include semantic_hints column")
        except Exception as e:
            st.error(f"Error migrating CSV: {e}")
            st.error("Please run: python scripts/fix_csv.py")
            return

    # Append new entry
    df = pd.DataFrame([feedback_entry])
    try:
        if file_exists and not needs_migration:
            df.to_csv(FEEDBACK_CSV, mode='a', header=False, index=False, quoting=csv_module.QUOTE_ALL)
        elif not file_exists:
            df.to_csv(FEEDBACK_CSV, mode='w', header=True, index=False, quoting=csv_module.QUOTE_ALL)
        else:
            # After migration, append new entry
            df.to_csv(FEEDBACK_CSV, mode='a', header=False, index=False, quoting=csv_module.QUOTE_ALL)
    except Exception as e:
        st.error(f"Error saving feedback: {e}")
        return

    st.success("Feedback saved successfully!")

    # Clear notes after saving
    st.session_state.query_notes = ""
    st.session_state.genai_notes = ""
    st.session_state.rating = 3

def reset_feedback():
    """Reset feedback CSV file"""
    try:
        # Define column headers
        headers = ['timestamp', 'question', 'sql_query', 'query_type', 'sql_results_count',
                  'genai_response', 'semantic_hints', 'query_notes', 'genai_notes', 'rating']
        
        # Create empty DataFrame with headers
        df = pd.DataFrame(columns=headers)
        
        # Write to CSV
        df.to_csv(FEEDBACK_CSV, index=False, quoting=csv_module.QUOTE_ALL)
        
        st.toast("Feedback data has been reset!", icon="🗑️")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error resetting feedback: {e}")

# Main UI
st.title("🔍 606 Query Analysis Tool")
st.markdown("Enter a natural language question to analyze the query generation process")

# Load questions from JSONL
jsonl_questions = load_jsonl_questions()

# Question input mode selector
input_mode = st.radio(
    "Question input mode:",
    ["Manual Entry", "Select from Test Questions"],
    horizontal=True
)

question = ""

if input_mode == "Manual Entry":
    # Manual question input
    question = st.text_input(
        "Enter your question:",
        placeholder="e.g., What venue received the most volume in January 2024?",
        key="question_input"
    )
else:
    # Select from JSONL questions
    if jsonl_questions:
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_question = st.selectbox(
                "Select a test question:",
                options=jsonl_questions,
                format_func=lambda x: f"[ID:{x['id']}] {x['question']}",
                key="question_selector"
            )
            if selected_question:
                question = selected_question['question']
                st.info(f"**Table Hint:** {selected_question['table_hint']} | **Notes:** {selected_question['notes']}")
        with col2:
            st.metric("Total Questions", len(jsonl_questions))
    else:
        st.warning(f"No test questions found in {JSONL_FILE}")

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    submit_button = st.button("Generate Query", type="primary", use_container_width=True)
# with col2:
#     st.session_state.use_semantic_hints = st.checkbox(
#         "Use Semantic Hints",
#         value=st.session_state.use_semantic_hints,
#         help="Enable LangChain semantic hints for complex query patterns"
#     )

# Process query
if submit_button and question:
    with st.spinner("Processing query..."):
        response = call_api(question, st.session_state.use_semantic_hints)

        if response:
            st.session_state.current_response = response
            st.session_state.query_notes = ""
            st.session_state.genai_notes = ""

# Display results if available
if st.session_state.current_response:
    response = st.session_state.current_response

    st.markdown("---")

    # Top section: LLM-Generated Query with tabs
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("📝 Generated Query")
    with col2:
        st.info("Neuro-Symbolic v1.3")

    tab1, tab2 = st.tabs(["SQL Query", "Logic Details"])

    with tab1:
        sql_query = response.get('sql', 'No SQL query generated')
        st.code(sql_query, language="sql")

    with tab2:
        logic_details = extract_logic_details(response)
        formatted_details = format_logic_details(logic_details)
        st.markdown(formatted_details)

    # Notes section for query
    st.markdown("#### Query Notes")
    st.session_state.query_notes = st.text_area(
        "Add notes about the query (mistakes, improvements, etc.):",
        value=st.session_state.query_notes,
        height=100,
        key="query_notes_input"
    )

    st.markdown("---")

    # Middle section: SQL Results
    st.subheader("📊 SQL Results")

    results = response.get('results', [])
    if results:
        if isinstance(results, list) and len(results) > 0:
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)

            # Download button
            csv = df_results.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No results returned")
    else:
        st.info("No results available")

    st.markdown("---")

    # Bottom section: GenAI Response
    st.subheader("🤖 GenAI Response")

    genai_response = response.get('response', 'No narrative response generated')
    st.markdown(f"**Response:** {genai_response}")

    # Notes section for GenAI response
    st.markdown("#### GenAI Response Notes")
    st.session_state.genai_notes = st.text_area(
        "Add notes about the GenAI response (accuracy, clarity, etc.):",
        value=st.session_state.genai_notes,
        height=100,
        key="genai_notes_input"
    )

    st.markdown("---")

    # Overall rating
    st.subheader("⭐ Overall Rating")
    col1, col2, col3 = st.columns([2, 1, 3])

    with col1:
        st.session_state.rating = st.slider(
            "Rate the overall query generation:",
            min_value=1,
            max_value=5,
            value=st.session_state.rating,
            help="1 = Poor, 5 = Excellent"
        )

    with col2:
        if st.button("💾 Save Feedback", type="primary", use_container_width=True):
            save_feedback()

    # Display saved feedback count
    if os.path.exists(FEEDBACK_CSV):
        try:
            feedback_df = pd.read_csv(FEEDBACK_CSV)
            st.info(f"Total feedback entries: {len(feedback_df)}")
        except Exception as e:
            st.error(f"Error reading feedback CSV: {e}")

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This tool helps analyze and evaluate the query generation process.

    **Features:**
    - View generated SQL queries
    - Inspect logic details and heuristics
    - Review SQL results
    - Read GenAI narrative responses
    - Add notes and ratings
    - Export feedback to CSV

    **Query Types:**
    - Direct single-table queries
    - Complex multi-table queries
    - Template-based (planner) queries
    """)

    st.markdown("---")

    st.header("📁 Feedback Data")
    if os.path.exists(FEEDBACK_CSV):
        try:
            feedback_df = pd.read_csv(FEEDBACK_CSV)
            st.metric("Total Entries", len(feedback_df))

            if len(feedback_df) > 0:
                # Check if rating column exists and has valid data
                if 'rating' in feedback_df.columns and feedback_df['rating'].notna().any():
                    avg_rating = feedback_df['rating'].mean()
                    st.metric("Average Rating", f"{avg_rating:.2f}")
                else:
                    st.info("No ratings yet")

                # Download all feedback
                csv_data = feedback_df.to_csv(index=False)
                st.download_button(
                    label="Download All Feedback",
                    data=csv_data,
                    file_name=f"all_feedback_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
                # Reset button
                st.markdown("---")
                if st.button("🗑️ Reset Feedback Data", type="secondary", help="Clear all feedback entries and reset count to 0"):
                    reset_feedback()
                    
        except Exception as e:
            st.error(f"Error reading feedback CSV: {e}")
            st.error("Try running: python scripts/fix_csv.py")
    else:
        st.info("No feedback data yet")

    st.markdown("---")

    st.header("⚙️ Settings")
    st.text_input("API URL:", value=API_URL, disabled=True)
