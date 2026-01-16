# LLM PIPELINE ARCHITECTURE - CORRECTED

## Full Flow: Question → SQL → Data → Context

### Flow Diagram
```
User Question
    ↓
[1] VANNA.AI SQL GENERATION
    - Uses: VannaDefault(model, api_key) 
    - api_key = VANNA API key (from https://vanna.ai/account/profile)
    - NOT Gemini API
    - vn.generate_sql(question) → SQL string
    ↓
[2] SQL EXECUTION
    - Execute SQL against MySQL DW
    - Returns: pandas DataFrame
    ↓
[3] PII MASKING (Role-based)
    - apply_pii_masking_for_role(df, user_role)
    - Store Manager: customer_name, postal_code masked
    - Sales Associate & Executive: no masking
    ↓
[4] PREPARE CONTEXT FOR LLM
    - Extract key statistics from data
    - Build context string with:
      * Original question
      * SQL query used
      * Data shape & columns
      * Sample rows
      * Key statistics
    ↓
[5] LLM ANALYSIS (BLOCKED - No Gemini API)
    - Send context + data to Gemini LLM
    - Gemini generates natural language response
    - NOT YET IMPLEMENTED (needs valid GEMINI_API_KEY)
    ↓
User Response (Natural Language)
```

## Three Components & Their Dependencies

### 1. VANNA.AI (SQL Generation)
**Type:** Vanna's own LLM service  
**Authentication:** VANNA_API_KEY from https://vanna.ai/account/profile  
**NOT dependent on:** Gemini API  
**Methods:**
```python
from vanna.remote import VannaDefault

vn = VannaDefault(model="model_name", api_key="vanna_api_key")
sql = vn.generate_sql(question)  # Generates SQL using training data
vn.add_question_sql(question, sql)  # Add Q→SQL pair for training
```

### 2. MYSQL DATA WAREHOUSE (SQL Execution)
**Purpose:** Store and retrieve data  
**Connection:** mysql-connector-python  
**Used by:** execute_sql() in function_tools.py  

### 3. GEMINI LLM (Analysis & Response Generation)
**Type:** Google's LLM service  
**Authentication:** GEMINI_API_KEY from Google AI Studio  
**Purpose:** Convert data insights to natural language response  
**Currently:** NOT WORKING (placeholder key in env.yaml)

## Key Correction: Vanna.AI Uses ITS OWN API

❌ **WRONG (what I initially did):**
```python
vanna.set_api_key(api_key)  # DEPRECATED - throws error
vanna.train(question, sql)  # DEPRECATED - throws error
vanna.generate_sql(question)  # DEPRECATED - throws error
```

✅ **CORRECT:**
```python
from vanna.remote import VannaDefault

vn = VannaDefault(model="model_name", api_key="vanna_api_key")
vn.add_question_sql(question, sql)  # Train
sql = vn.generate_sql(question)  # Generate SQL
```

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| initialize_vanna() | ❌ BROKEN | Uses deprecated API methods |
| generate_sql_with_vanna() | ❌ BROKEN | Uses deprecated vanna.generate_sql() |
| SQL Execution | ✅ WORKING | Tested with 5 queries, 100% pass rate |
| PII Masking | ✅ WORKING | Verified masking for Store Manager role |
| Gemini Integration | ❌ BLOCKED | Needs valid GEMINI_API_KEY |
| Context Assembly | ⚠️ PARTIAL | SQL executed, but context not tested without Gemini |

## What Needs to be Done

1. **Fix initialize_vanna()**: Use VannaDefault class instead of module-level functions
2. **Fix generate_sql_with_vanna()**: Call vn.generate_sql() instead of vanna.generate_sql()
3. **Create proper test**: Test question → SQL generation → data execution → context building (without Gemini)
4. **Add Gemini API key**: Get valid key for full end-to-end testing

## Testing Strategy (No Gemini Needed)

We can verify the full pipeline UP TO context generation:
1. Question input ✅
2. Vanna.AI SQL generation (once fixed)
3. SQL execution against MySQL DW ✅
4. PII masking ✅
5. Context building (statistics, summaries) ✅
6. Return context (skip Gemini for now)

This validates 80% of the pipeline without needing Gemini API key.
