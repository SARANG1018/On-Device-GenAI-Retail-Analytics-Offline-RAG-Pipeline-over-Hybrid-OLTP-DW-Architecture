# A Hybrid OLTP-DW System with an AI-Powered Analytics Interface

## The Problem

Modern retail enterprises face three interconnected challenges:

**Challenge 1: Real-Time Data Gap** - Transactional data (PostgreSQL) and analytical data (MySQL) get out of sync. Sales happen instantly, but insights arrive hours or days later. Traditional ETL pipelines are slow and resource-intensive.

**Challenge 2: Analytics Accessibility** - Business users (store managers, executives) need data-driven insights but lack SQL skills. Each question requires a data engineer. This creates bottlenecks and delays critical decisions.

**Challenge 3: AI Pipeline Integration** - Most analytics still rely on manual SQL queries or slow batch processing. How do you bring AI query generation into an enterprise data system safely, without cloud data leakage?

## The Solution

A hybrid ETL-based analytics platform that:

1. **Keeps Data Fresh** - Change Data Capture (CDC) pipeline synchronizes OLTP and DW in under 30 seconds. Only changed records move through the pipeline, not entire datasets.

2. **Democratizes Analytics** - Users ask questions in plain English. The system translates to SQL via a hybrid approach: exact keyword matching on 35 pre-trained business questions, with local Ollama/Mistral LLM fallback for novel queries.

3. **Preserves Privacy** - All processing stays on-device. No data leaves the organization. No cloud API calls. Complete data lineage and audit trails.

## System Architecture

```
PostgreSQL OLTP                      MySQL Data Warehouse
(Real-time Transactions)             (Analytics Optimized)
- 8 Normalized Tables                - 6-Table Star Schema
- CDC Triggers & Indexes             - 48 Monthly Partitions
- 96K+ Records                       - Optimized Joins
     ↓
     ETL Pipeline (CDC-Based)
     - Extract (changed records only)
     - Transform (OLTP → Star Schema)
     - Validate (7 quality checks)
     - Load (idempotent)
     ↓
Streamlit Interface
- Role-based Dashboards
- Natural Language Chat
- Data Entry Forms
     ↓
AI Query Layer
1. Extract keywords from question
2. Exact match on 35 trained Q→SQL pairs
3. If no match → Ollama/Mistral LLM
4. Validate & execute SQL
5. Visualize results
```

## The Innovation: Hybrid Query Generation

**Why Keyword Matching?**
Pre-trained answers (35 carefully curated Q→SQL pairs) ensure 90% of queries get fast, reliable results. No LLM hallucination. No unpredictable SQL generation.

**Why LLM Fallback?**
Novel analytical questions that don't match training data get answered by local Ollama/Mistral. The LLM has full database schema, join patterns, and business rules in its system prompt, enabling accurate SQL generation.

**Why Local LLM?**
Zero data leakage. No API calls to OpenAI/Gemini. 2-5 second query response. Works offline. Compliance-friendly.

**Result**: The system handles common questions instantly (keyword matching) and novel questions accurately (informed LLM) while maintaining complete privacy.

## How It Works: Query Execution

**Standard Question**: "Show me sales by product category"
```
1. Extract keywords: {sales, product, category}
2. Search vanna_training_data.py → MATCH FOUND ✓
3. Return pre-trained SQL
4. Execute on MySQL DW
5. Visualize as bar chart
```

**Novel Question**: "Which regions had highest profit growth last month vs this month?"
```
1. Extract keywords: {profit, growth, region, month}
2. Search vanna_training_data.py → No exact match
3. Call Ollama/Mistral with full database schema & business rules
4. LLM generates SQL (CTEs, window functions, joins)
5. Validate (SELECT-only), execute, visualize
```

## Project Organization

### src/ - Core Application

| File | Purpose |
|------|---------|
| **main.py** | Streamlit web interface with role-based dashboards and chat analytics |
| **function_tools.py** | `VannaHybrid` class: keyword extraction + exact matching + LLM fallback orchestration |
| **vanna_training_data.py** | 35 pre-trained Q→SQL pairs covering sales, profitability, customer, returns |
| **system_prompt.py** | LLM instructions: schema, join patterns, business logic, data constraints |
| **etl_pipeline.py** | CDC extraction, OLTP→DW transformation, 7 validation procedures |
| **auth.py** | Bcrypt authentication, RBAC, multi-factor auth, password history |
| **pii_masking.py** | Automatic PII detection and masking for query results |
| **utils.py** | Database connections, configuration, logging |
| **partition_manager.py** | 96-partition lifecycle management |
| **sql_loader.py** | CSV ingestion with duplicate detection |

### sql/ - Database Schemas

| Folder | Contents |
|--------|----------|
| **postgresql/** | OLTP: 8 tables, CDC triggers, indexes, 96 partitions, 7 validation procedures |
| **mysql/** | DW: 6-table star schema (3 dimensions + 2 facts + date), 48 partitions, auth tables |
| **core/** | Original DDL and sample data |

### test/ - Test Suite (12 files)

Testing for ETL validation, authentication, query generation, data quality, performance

### datasets/ - Sample Data

25,731 orders + 1,083 returns for development and testing

## Technology Stack

- **Frontend**: Streamlit
- **Databases**: PostgreSQL 16 (OLTP), MySQL 8 (DW)
- **Processing**: Python, Pandas
- **AI/LLM**: Vanna.AI, Ollama with Mistral 7B (local, on-device only)
- **Visualization**: Plotly
- **Security**: Bcrypt
- **Config**: YAML

## Setup

**Prerequisites**: Python 3.9+, PostgreSQL 16+, MySQL 8+, Ollama with Mistral

**Installation**:
```bash
git clone https://github.com/SARANG1018/A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface
cd A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Configuration**:
```bash
cp env.yaml.example env.yaml
# Edit env.yaml with PostgreSQL, MySQL, and Ollama credentials
```

**Database Setup**:
```bash
psql -U postgres -f sql/postgresql/create_user_tables_postgresql.sql
mysql -u root -p < sql/mysql/create_user_tables_mysql.sql
```

**Launch Application**:
```bash
cd src
streamlit run main.py
```

Access at `http://localhost:8501`

## Key Achievements

- ✅ **Sub-30 Second ETL** for 96K+ records (CDC-based incremental load)
- ✅ **Keyword-Based Reliability** with 35 pre-trained business questions
- ✅ **Zero Cloud Data Leakage** using local Ollama/Mistral LLM only
- ✅ **Complete Privacy** with PII masking and audit logging
- ✅ **Multi-Role System** with database-level RBAC (Sales Associate, Store Manager, Executive)
- ✅ **7 Data Quality Checks** running automatically before each load
- ✅ **96 Monthly Partitions** enabling 10x faster time-series queries
- ✅ **Real-Time Sync** keeping DW within 5 minutes of OLTP

## Sample Questions

The system comes with starter questions for immediate testing:

```
• Show all product categories
• Show me sales by product category
```

Add more questions to `questions` file to extend the training data.

---

**Authors**: Sarang, Sajitha, Chatat | NYU Fall 2025 Advanced Data Engineering Project

**Repository**: https://github.com/SARANG1018/A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface

**Last Updated**: January 16, 2026
