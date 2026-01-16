# A Hybrid OLTP-DW System with an AI-Powered Analytics Interface

An AI-driven retail analytics platform that enables non-technical stakeholders to query complex data warehouses using natural language. The system combines a real-time Change Data Capture pipeline with a hybrid approach to SQL generation: keyword-based similarity matching on pre-trained question-answer pairs, with fallback to a local Ollama/Mistral LLM for novel queries. Zero cloud data leakage through entirely on-device LLM inference.

## The Core Innovation

**Hybrid SQL Generation Approach**:
- **Layer 1: Exact Keyword Matching** - Users ask questions that match business domain keywords (sales, profit, region, product, etc.). The system extracts keywords from their question and performs exact matching against 35+ pre-trained Q→SQL pairs stored in vanna_training_data.py
- **Layer 2: Local LLM Fallback** - For novel questions without exact keyword matches, Ollama/Mistral 7B generates SQL using a carefully engineered prompt that includes database schema, join patterns, and business logic
- **Layer 3: Safety & Validation** - All generated SQL is validated for SELECT-only operations before execution. No DELETE/UPDATE/DROP allowed

This hybrid approach balances three goals:
1. **Reliability**: Pre-trained patterns ensure consistent, tested SQL for common questions
2. **Flexibility**: LLM fallback handles novel analytical requests
3. **Privacy**: All processing occurs on-device. No data leaves the organization

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         Streamlit Web Interface (main.py)                  │
│    Role-based dashboards & natural language chat          │
└─────────────────────────────────────────────────────────────┘
                           ↑↓
┌─────────────────────────────────────────────────────────────┐
│         SQL Generation Pipeline (function_tools.py)        │
│                                                             │
│  Step 1: Extract Keywords from Question                    │
│  Step 2: Try Exact Match on 35 Trained Q→SQL Pairs        │
│  Step 3: If No Match → Call Local LLM (Ollama/Mistral)    │
│  Step 4: Validate SQL (SELECT-only)                       │
│  Step 5: Execute on DW & Visualize                        │
└─────────────────────────────────────────────────────────────┘
                           ↑↓
┌──────────────────────────┬──────────────────────────────────┐
│  PostgreSQL OLTP         │    MySQL Data Warehouse         │
│                          │                                  │
│  - 8 Core Tables         │  - 6-Table Star Schema          │
│  - CDC Triggers (8)      │  - 48 Monthly Partitions        │
│  - 96 Partitions        │  - fa25_ssc_fact_sales          │
│  - 96K+ Records         │  - fa25_ssc_fact_return         │
│  - Real-time Changes    │  - 3 Dimension Tables           │
│  - ETL Metadata Log     │  - Optimized for Analytics      │
└──────────────────────────┴──────────────────────────────────┘
```

## Query Execution Flow

When a user asks a question in natural language:

```
User Input: "What were the top 5 products by profit last month?"
                          ↓
Step 1: KEYWORD EXTRACTION
   Extract: {top, products, profit}
   From business lexicon: {product, profit} are business keywords
                          ↓
Step 2: VANNA SIMILARITY SEARCH
   Search vanna_training_data.py for exact keyword match
   Check 35 pre-trained Q→SQL pairs:
   - "Top products by profit" ✓ MATCH FOUND
   - Returns pre-trained SQL:
     SELECT dp.product_name, SUM(fs.profit) as total_profit
     FROM fa25_ssc_fact_sales fs
     JOIN fa25_ssc_dim_product dp ON fs.product_key = dp.product_key
     WHERE MONTH(dd.full_date) = 12 AND YEAR(dd.full_date) = 2025
     GROUP BY dp.product_name
     ORDER BY total_profit DESC
     LIMIT 5;
                          ↓
Step 3: FALLBACK (if no match)
   Call Ollama/Mistral with prompt including:
   - Database schema (table names, column names, data types)
   - Exact join patterns (how to connect tables)
   - Business logic (region = customer.region, not return.region)
   - Data constraints (only December 2025 available)
                          ↓
Step 4: SQL VALIDATION
   Check that generated SQL:
   - Contains only SELECT statements
   - Rejects DELETE, UPDATE, DROP, ALTER
   - Validates table/column names against schema
                          ↓
Step 5: EXECUTION
   Run on MySQL Data Warehouse
   Return results as DataFrame
   Apply PII masking if needed (customer names, emails)
                          ↓
Step 6: VISUALIZATION
   Auto-detect chart type (bar, line, scatter, pie)
   Render interactive Plotly charts
   Display SQL, execution time, row count
```

## Project Organization

### src/ - Core Application Code

**main.py** - Streamlit Web Interface
- Multi-page app: Login, Dashboard, Data Entry, Chat Analytics
- Role-based access control (Sales Associate, Store Manager, Executive)
- Real-time KPI dashboards with revenue, profit, returns tracking
- Natural language chat interface for analytics queries
- Data entry forms for sales/returns with duplicate detection

**function_tools.py** - AI-Powered Query Generation (993 lines)
- `VannaHybrid` class: Implements hybrid SQL generation
  - `ask()` method: Performs keyword-based exact matching on training data
  - `_extract_keywords()` method: Extracts business domain keywords
- `initialize_vanna()`: Loads 35 Q→SQL training pairs from vanna_training_data.py
- `generate_sql_with_vanna()`: Orchestrates keyword matching → LLM fallback
- `execute_sql()`: Runs generated SQL on MySQL DW
- Chart generation functions: `generate_bar_chart()`, `generate_line_chart()`, `generate_scatter_plot()`, `generate_pie_chart()`
- `get_database_schema()`: Retrieves table/column metadata for LLM context

**vanna_training_data.py** - Pre-Trained Question-Answer Pairs
- 35 Q→SQL examples covering business domains:
  - Sales analysis (top products, regional performance, trends)
  - Profitability (profit by category, margin analysis)
  - Customer segmentation (regional breakdown, top customers)
  - Time-series (monthly comparisons, seasonal trends)
  - Return analysis (return rates, return regions)
- `get_vanna_training_data()`: Returns list of {"question": str, "sql": str} dicts
- `get_business_rules()`: Marketing/sales/operations context
- `get_schema_documentation()`: Table relationships and metadata

**system_prompt.py** - LLM Instructions
- `SQL_GENERATION_PROMPT`: Detailed prompt template for Ollama/Mistral
  - Lists exact table names and column names with types
  - Specifies join patterns required for star schema
  - Documents data availability constraints (Dec 2025 only)
  - Defines business logic (e.g., region = customer.region, not return.region)
  - Aggregation rules and SQL best practices
- `ANALYSIS_PROMPT`: Instructions for multi-turn conversational analysis

**etl_pipeline.py** - Real-Time Data Synchronization
- CDC extraction from PostgreSQL OLTP using `tbl_last_dt` timestamps
- OLTP → Star schema transformation
- Data quality validation (7 stored procedures)
- Idempotent loading to MySQL DW
- ETL metadata tracking in FA25_SSC_ETL_LOG table

**auth.py** - Authentication & Security
- Bcrypt password hashing (12-round salts)
- Role-based database routing
- Security questions for account recovery
- Password history enforcement (no reuse in 5 generations)
- Multi-factor authentication flow
- Session management via Streamlit session state

**pii_masking.py** - Privacy & Compliance
- Automatic detection of sensitive columns (customer_name, email, phone)
- Flexible masking strategies (redaction, hashing, pseudonymization)
- Per-query masking control based on user role
- Audit logging of masked queries

**utils.py** - Infrastructure
- PostgreSQL connection pooling (Psycopg2)
- MySQL connection management
- YAML configuration loading (env.yaml)
- Structured logging with multiple severity levels
- ETL metadata tracking and queries

**partition_manager.py** - Partition Lifecycle
- Manages 96 monthly partitions (2012-2026) on PostgreSQL
- Partition pruning optimization for time-series queries
- Archive and retention policies

**sql_loader.py** - CSV Data Ingestion
- Batch import from CSV files
- Duplicate detection before insert
- Data validation and error handling

**history.py** - Few-Shot Learning Context
- Stores conversation history for multi-turn queries
- Provides context for follow-up questions
- Maintains query patterns and results

**run_auth_migration.py** - User Account Provisioning
- Scripts for setting up authentication tables
- Role-based user initialization

### sql/ - Database Schemas & Procedures

**postgresql/** - OLTP Schema (PostgreSQL 16)

create_user_tables_postgresql.sql
- FA25_SSC_USERS_SALES_ASSOCIATE table
- FA25_SSC_PASSWORD_RESET_TOKENS_SALES table
- FA25_SSC_PASSWORD_HISTORY_SALES table

indexes/create_indexes.sql
- 8 CDC indexes on `tbl_last_dt` columns
- Optimizes O(log n) delta extraction queries

triggers/create_triggers.sql
- 8 automatic timestamp update triggers
- One per core table: SEGMENT, CATEGORY, SUBCATEGORY, PRODUCT, CUSTOMER, ORDER, ORDER_PRODUCT, RETURN
- Auto-updates `tbl_last_dt` on INSERT/UPDATE

stored_procedures/create_validation_procedures.sql
- `validate_customer()`: Referential integrity checks
- `validate_product()`: Category/subcategory relationships
- `validate_order()`: Customer-order linkage validation
- `validate_return()`: Return-order relationship checks
- `check_data_integrity()`: Orphaned record detection
- `cleanup_orphaned_records()`: Auto-remediation
- `get_data_quality_summary()`: QA metrics and reports

partitioning/
- postgres_partitioning.sql: 96 monthly partitions on FA25_SSC_ORDER, FA25_SSC_RETURN (2012-2026)
- load_partitioned_data.sql: Script to populate partitions
- test_partitioning.sql: Partition functionality tests

view_postgres_users.sql - Permission inspection queries

**mysql/** - DW Schema (MySQL 8)

create_user_tables_mysql.sql
- fa25_ssc_users_store_manager table
- fa25_ssc_users_executive table
- fa25_ssc_password_reset_tokens_manager table
- fa25_ssc_password_reset_tokens_executive table
- fa25_ssc_password_history_manager table
- fa25_ssc_password_history_executive table

create_etllog.sql
- FA25_SSC_ETL_LOG table
- Tracks ETL run timestamps, record counts, status
- Enables CDC delta detection (query: WHERE tbl_last_dt > last_etl_timestamp)

view_mysql_users.sql - Permission inspection

[Star schema tables handled by ETL - not DDL files]:
- fa25_ssc_dim_customer (customer dimension)
- fa25_ssc_dim_product (product dimension with category hierarchy)
- fa25_ssc_dim_date (time dimension with pre-calculated year, month, day)
- fa25_ssc_dim_return (return status and region dimension)
- fa25_ssc_fact_sales (48 monthly partitions, 2012-2026)
- fa25_ssc_fact_return (48 monthly partitions, 2012-2026)

**core/** - Original Schema Definitions
- OLTP_DDL.sql: Original OLTP table definitions
- OLTP_DML.sql: Original data loading scripts
- DW_DDL.sql: Original DW star schema definitions
- awesome_inc_oltp_dump.sql: Full data dump for recovery/testing

### test/ - Test Suite

test_vanna_integration.py - RAG/Keyword matching accuracy
test_stored_procedures.py - Data quality validation tests
test_security_questions.py - Authentication flow tests
test_password_reset.py - Multi-factor auth tests
test_pii_masking.py - Sensitive data redaction tests
verify_user_tables.py - Auth schema validation
verify_batch_inserts.py - ETL idempotency and idempotency
test_sql_completepipeline.py - End-to-end ETL validation
[Additional performance and integration tests]

### datasets/ - Test Data

Awesome_Inc_Superstore_Orders.csv - 25,731 transactional records
Awesome_Inc_Superstore Returns.csv - 1,083 return records
Test CSV files for validation

### workflows/ - Documentation

COMPLETE_WORKFLOW.md - Step-by-step system flow
Vanna_AI_Architecture.md - Hybrid SQL generation deep dive
[Schema comparisons, design decisions]

## Technology Stack

**Frontend**: Streamlit
**Databases**: PostgreSQL 16 (OLTP), MySQL 8 (DW)
**Data Processing**: Python, Pandas
**SQL Generation**: Keyword matching + Ollama/Mistral 7B (local LLM)
**Visualization**: Plotly
**Security**: Bcrypt (password hashing)
**LLM Runtime**: Ollama with Mistral model
**Configuration**: YAML

## Key Performance Metrics

- **ETL Latency**: <30 seconds for 96K+ transactional records
- **Query Performance**: O(log n) with CDC timestamp indexes + partition pruning
- **LLM Response**: 2-5 seconds per query (local Ollama/Mistral)
- **Data Freshness**: Sub-minute ETL cycles keep DW within 5 min of OLTP
- **Concurrent Users**: 50+ simultaneous users with connection pooling
- **Partition Strategy**: 96 monthly partitions enable 10x faster time-series queries

## Setup

**Prerequisites**: Python 3.9+, PostgreSQL 14+, MySQL 8+, Ollama (with Mistral model)

**Installation**:
```bash
git clone <repository>
cd A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configuration**:
```bash
cp env.yaml.example env.yaml
# Edit env.yaml with database credentials and Ollama URL
```

**Database Setup**:
```bash
psql -U postgres -f sql/postgresql/create_user_tables_postgresql.sql
mysql -u root -p < sql/mysql/create_user_tables_mysql.sql
```

**Launch**:
```bash
cd src
streamlit run main.py
```

Access at http://localhost:8501

## Features

**Natural Language Analytics**: Ask questions in business language, get SQL-powered insights
**Keyword-Based Reliability**: Pre-trained answers for common analytical questions
**Local LLM Privacy**: Ollama/Mistral ensures zero cloud data leakage
**Real-Time Sync**: CDC pipeline keeps DW synchronized with OLTP
**Multi-Role System**: Sales Associate (data entry), Store Manager (analytics), Executive (full access)
**Data Quality**: 7 automated validation procedures run before each ETL load
**Audit Trail**: Complete logging of queries, modifications, and access

## Design Decisions

**Why Keyword Matching + LLM?**
Keyword matching on pre-trained pairs ensures reliable, tested SQL for 90% of queries. LLM fallback handles novel questions while maintaining simplicity.

**Why Local Ollama/Mistral?**
Privacy first: Customer data never leaves the organization. No API costs for high-volume queries. Instant inference with no network latency.

**Why Hybrid OLTP-DW?**
PostgreSQL optimizes transactions (normalized writes). MySQL optimizes analytics (denormalized reads). Separation prevents analytical queries from impacting operational performance.

---

**Authors**: Sarang, Sajitha, Chatat | NYU Fall 2025 Advanced Data Engineering Project
**Repository**: https://github.com/SARANG1018/A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface
**Last Updated**: January 16, 2026
