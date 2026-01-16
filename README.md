# A Hybrid OLTP-DW System with an AI-Powered Analytics Interface

A production-grade data engineering platform that integrates transactional systems with analytical capabilities through Change Data Capture, automated ETL, and natural language query generation. Built to enable stakeholders to derive actionable insights from complex datasets while maintaining data privacy and strict access controls.

## Problem Statement

Organizations face three critical challenges when democratizing data access:

1. **Data Freshness** - How to keep analytical data synchronized with transactional sources in near real-time without full refreshes
2. **Accessibility** - How to enable non-technical stakeholders to query complex datasets without writing SQL
3. **Privacy** - How to ensure sensitive data remains protected while supporting self-service analytics

This system addresses all three through a dual-database architecture with intelligent data synchronization, schema-aware SQL generation, and role-based access controls.

## Solution Architecture

The platform consists of three integrated layers:

**Data Layer**: PostgreSQL normalized OLTP database feeds incremental changes to a MySQL star schema DW through a CDC pipeline. Eight core tables are tracked with automatic timestamp updates on modifications, enabling efficient delta extraction.

**Processing Layer**: A Python-based ETL orchestrator validates data quality through seven stored procedures while transforming normalized records into analytics-optimized structures. The entire pipeline executes in under 30 seconds for 96,000+ transactional records.

**Interface Layer**: A Streamlit web application provides role-based access to data entry, dashboards, and natural language analytics. Users can query datasets by describing what they want in plain English, with the system translating questions to SQL automatically.

## Key Technical Achievements

**Change Data Capture**: Implemented timestamp-based CDC mechanism using PostgreSQL triggers across eight tables. Each table maintains a tbl_last_dt column automatically updated on INSERT/UPDATE, enabling queries to fetch only changed records since the last ETL run.

**Incremental ETL**: Extract phase identifies deltas in O(log n) time using database indexes on CDC timestamps. Transform phase denormalizes OLTP records into star schema dimensions and facts. Validate phase runs data quality checks before load. Result: sub-minute latency for 96K+ records.

**Schema-Aware Query Generation**: Integrated Vanna.AI to interpret natural language queries using the actual database schema as context. The system retrieves table structures, enforces business rules, and generates parameterized SQL through either local LLMs (Ollama/Mistral) or cloud APIs (OpenAI/Gemini).

**Security Infrastructure**: Implemented bcrypt password hashing with 12-round salts, role-based database routing (Sales Associate, Store Manager, Executive), multi-factor authentication through security questions, and comprehensive audit logging for all data modifications.

## Technical Implementation

**Core Modules**:

- **main.py** (2,660 lines) - Streamlit web application with multi-page interface, user authentication, role-based dashboards, data entry forms, and natural language chat interface
- **etl_pipeline.py** (700 lines) - ETL orchestration with CDC extraction, schema transformation, data quality validation, and idempotent loading
- **function_tools.py** (993 lines) - RAG pipeline for query generation, schema retrieval, SQL validation, and visualization
- **auth.py** (575 lines) - Authentication, password security, RBAC, and session management
- **utils.py** - Database connections, configuration management, logging, and metadata tracking

**Database Schema**:

PostgreSQL OLTP contains 8 normalized dimension and fact tables with 96 monthly partitions spanning 2012-2026. CDC infrastructure includes 8 triggers for timestamp management and 8 indexes for efficient delta queries.

MySQL DW implements a 6-table star schema with 48 monthly partitions on fact tables. Materialized metrics are pre-aggregated for dashboard performance. Role-specific authentication tables enable database-level access control.

**Supporting Infrastructure**:

Seven stored procedures validate referential integrity, category relationships, customer-order linkage, and detect orphaned records. ETL metadata is tracked in a dedicated log table. 32 SQL training examples and business rules guide the LLM during query generation.

## Performance Characteristics

- ETL Pipeline: <30 seconds for complete incremental load of 96K+ records
- CDC Query Performance: O(log n) delta extraction using timestamp indexes
- Monthly Partitions: 96 on OLTP, 48 on DW facts for query pruning
- Query Support: 1000+ analytically relevant questions supported
- Data Quality: 7 automated validation checks per load cycle

## Setup and Deployment

**Prerequisites**: Python 3.9+, PostgreSQL 14+, MySQL 8+

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
# Edit env.yaml with database credentials and LLM API keys
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

Access the application at http://localhost:8501

## Project Structure

```
src/
  main.py                    Streamlit web application
  etl_pipeline.py            CDC-based ETL orchestrator
  function_tools.py          RAG pipeline and analytics
  auth.py                    Authentication and RBAC
  utils.py                   Database connections and utilities
  system_prompt.py           LLM configuration
  vanna_training_data.py     SQL examples and business rules
  pii_masking.py             Sensitive data redaction
  partition_manager.py       Partition lifecycle management

sql/
  postgresql/                OLTP schema (8 tables, triggers, indexes)
  mysql/                     DW schema (6 tables, partitions)
  core/                      Schema definitions and utilities

test/
  12 test files covering ETL, security, RAG pipeline, and data quality

datasets/
  CSV files for ingestion testing
```

## Technology Stack

Frontend: Streamlit | OLTP Database: PostgreSQL 16 | Analytical Database: MySQL 8
ETL Framework: Python with Pandas | Query Generation: Vanna AI | Local LLMs: Ollama/Mistral
Authentication: bcrypt (12-round) | Visualization: Plotly | Configuration: YAML

## Data Governance

**Access Control**: Three roles with database-level isolation
**Password Policy**: Bcrypt hashing, 5-generation history enforcement, security question verification
**Sensitive Data**: Automatic detection and redaction of PII columns
**Query Logging**: All queries logged with timestamps for audit trails
**Data Retention**: 90-day retention policy with auto-purge

## Validation and Testing

The project includes 12 comprehensive test files covering:

- End-to-end ETL pipeline validation
- RAG query generation accuracy
- Authentication mechanisms and password policies
- Data quality stored procedures
- PII masking accuracy
- Batch insert idempotency
- Schema consistency

Data quality validation runs automatically before each load cycle, checking referential integrity, detecting orphaned records, and generating quality metrics.

## Production Considerations

- **Partition Management**: Automated lifecycle for 96 monthly partitions with query pruning
- **Connection Pooling**: Psycopg2 connection pooling for PostgreSQL
- **Error Handling**: Structured logging and error recovery with automatic retry
- **Scaling**: Containerization support for horizontal scaling

## Key Features

- **Natural Language Analytics**: Query datasets in plain English
- **Incremental Synchronization**: CDC ensures DW stays in sync without full refreshes
- **Privacy by Design**: Local LLM option ensures zero cloud data leakage
- **Multi-Role System**: Different access levels for sales, management, and executive users
- **Real-Time Dashboards**: KPI dashboards with revenue trends and performance metrics
- **Comprehensive Audit Trail**: All modifications tracked with user and timestamp details

## Author

Sarang with Sajitha and Chahat | NYU Fall 2025 Advanced Data Engineering Project

Repository: https://github.com/SARANG1018/A-Hybrid-OLTP-DW-System-with-an-AI-Powered-Analytics-Interface

---

Last Updated: January 16, 2026
Version: 2.0.0
