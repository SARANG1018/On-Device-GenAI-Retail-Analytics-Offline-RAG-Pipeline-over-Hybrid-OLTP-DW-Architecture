# Awesome Inc. Analytics System

A comprehensive data management and analytics solution featuring:
- **OLTP Database** (MySQL) for transactional data
- **Data Warehouse** (PostgreSQL) for analytical queries
- **ETL Pipeline** for data synchronization
- **RAG-Powered Chatbot** for natural language queries
- **Streamlit Web App** for user interface

---

## Project Structure

```
Project/
├── src/
│   ├── utils.py              # Logger, DB connections, utilities
│   ├── system_prompt.py      # LLM system message
│   ├── history.py            # Few-shot examples for RAG
│   ├── function_tools.py     # RAG pipeline & visualization tools
│   └── main.py               # Streamlit web application
├── env.yaml                  # Configuration file
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `env.yaml` with your database credentials and API keys:

```yaml
POSTGRES:
  HOST: localhost
  PORT: 5432
  USER: postgres
  PASSWORD: your_password
  DB: awesome_dw

MYSQL:
  HOST: localhost
  PORT: 3306
  USER: root
  PASSWORD: your_password
  DB: awesome_oltp

LLM:
  OPENAI_API_KEY: sk-your_key_here
  GEMINI_API_KEY: your_key_here
  MODEL: gpt-4
```

### 3. Setup Databases

**PostgreSQL (Data Warehouse):**
```sql
CREATE DATABASE awesome_dw;
-- Run DW schema setup (from your teammates)
```

**MySQL (OLTP):**
```sql
CREATE DATABASE awesome_oltp;
-- Run OLTP schema setup (from your teammates)
```

### 4. Run Streamlit App

```bash
cd src
streamlit run main.py
```

The app will be available at `http://localhost:8501`

---

## File Descriptions

### `utils.py`
- Logger setup and configuration
- PostgreSQL connection pooling
- MySQL connection management
- Configuration loading from `env.yaml`

**Key Functions:**
- `setup_logger()` - Initialize logger
- `load_env_config()` - Load YAML configuration
- `get_postgres_connection()` - Get PostgreSQL connection
- `get_mysql_connection()` - Get MySQL connection

### `system_prompt.py`
Contains the system message sent to LLM to define its behavior for SQL generation.

**Key Functions:**
- `get_system_prompt()` - Return LLM system message

### `history.py`
Few-shot examples to help LLM understand query patterns and visualization recommendations.

**Key Functions:**
- `get_examples()` - Return all examples
- `get_example_for_question()` - Get relevant example by keywords
- `format_examples_for_prompt()` - Format examples for LLM prompt

### `function_tools.py`
Core RAG pipeline and visualization tools.

**Tools Dictionary:**
```python
tools = {
    "sql_executor": execute_sql,
    "bar_chart": generate_bar_chart,
    "line_chart": generate_line_chart,
    "scatter_plot": generate_scatter_plot,
    "pie_chart": generate_pie_chart,
    "get_schema": get_database_schema
}
```

**Key Functions:**
- `process_question()` - Main orchestration function
- `build_augmented_prompt()` - Build LLM prompt with context
- `call_llm_api()` - Call GPT-4 or Gemini API
- `extract_sql_from_response()` - Parse SQL from LLM response
- `execute_sql()` - Execute on PostgreSQL
- `generate_*_chart()` - Visualization functions

### `main.py`
Streamlit web application with:
- User authentication & role-based access
- Dashboard with KPIs
- Data entry forms (Sales, Returns)
- Chat interface for LLM queries
- Settings page

**Key Functions:**
- `login_page()` - Authentication
- `dashboard_page()` - Analytics dashboard
- `data_entry_page()` - Forms for data entry
- `chat_page()` - LLM chatbot interface
- `settings_page()` - User settings

---

## Usage Flow

### 1. User Logs In
- Authenticate with username, password, and role
- Different roles have different access levels

### 2. Data Entry (Store Manager/Associate)
- Navigate to "Data Entry"
- Fill out sales or return forms
- Data inserted into MySQL OLTP

### 3. ETL Pipeline Runs (Backend)
- Scheduled job extracts changes from OLTP
- Transforms to star schema
- Loads into PostgreSQL DW

### 4. Analytics Query (Executive/Manager)
- Navigate to "Chat Analytics"
- Type natural language question
- RAG pipeline:
  - Retrieves schema from DW
  - Builds prompt with examples
  - Calls LLM (GPT-4/Gemini)
  - LLM generates SQL
  - Executes on DW
  - Generates visualization
- Results displayed: SQL + Data + Chart

---

## RAG Pipeline Flow

```
User Question
    ↓
Get Schema from PostgreSQL
    ↓
Get Examples from history.py
    ↓
Build Augmented Prompt (schema + examples + system prompt + question)
    ↓
Call LLM API (GPT-4/Gemini)
    ↓
Extract SQL from Response
    ↓
Validate & Execute SQL on PostgreSQL
    ↓
Generate Visualization (Bar/Line/Scatter/Pie)
    ↓
Display Results in Streamlit
```

---

## Logging

Logs are stored in `logs/app.log` with the following levels:
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages
- **ERROR**: Error messages

Configure log level in `env.yaml`:
```yaml
LOG:
  LEVEL: INFO
  FILE: logs/app.log
```

---

## Troubleshooting

### "Connection refused" error
- Ensure PostgreSQL and MySQL are running
- Check credentials in `env.yaml`
- Verify database names

### "Import could not be resolved"
- Install dependencies: `pip install -r requirements.txt`
- Verify Python environment

### LLM API errors
- Check API keys in `env.yaml`
- Verify API key permissions
- Check rate limiting

### Streamlit errors
- Ensure you're running from `src` directory
- Check log file: `logs/app.log`

---

## Next Steps

1. **Database Setup** (Your teammates)
   - Create OLTP schema in MySQL
   - Create DW schema in PostgreSQL
   - Set up ETL pipeline

2. **Testing**
   - Run sample data entry
   - Run ETL pipeline
   - Test chat queries

3. **Deployment**
   - Deploy on cloud (AWS/Azure/GCP)
   - Set up Docker container
   - Configure production environment

---

## Team Collaboration

- **Teammates**: Working on MySQL OLTP and PostgreSQL DW
- **Your Role**: Building RAG pipeline and Streamlit frontend
- **Integration Points**:
  - `function_tools.py` queries DW for data
  - `main.py` inserts to OLTP via forms
  - Both use `utils.py` for connections

---

## API References

- **OpenAI GPT-4**: https://platform.openai.com/docs/api-reference
- **Google Gemini**: https://ai.google.dev/docs
- **Streamlit**: https://docs.streamlit.io
- **Plotly**: https://plotly.com/python
- **Psycopg2**: https://www.psycopg.org/psycopg2/docs

---

## Support & Questions

For issues or questions:
1. Check `logs/app.log` for error details
2. Refer to function documentation in code
3. Review README sections above
4. Consult with team members

---

**Last Updated**: November 4, 2025
**Version**: 1.0.0
