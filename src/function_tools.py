import logging
import re
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Any, Optional

from utils import get_mysql_connection, load_env_config
from system_prompt import get_analysis_prompt, get_sql_generation_prompt
from vanna_training_data import get_vanna_training_data, get_business_rules, get_schema_documentation
from pii_masking import PIIMasking

# Import Vanna for SQL generation (LOCAL AGENT - Vanna 2.0.1)
try:
    from vanna import Agent
    from vanna.integrations.mysql import MySQLRunner
    VANNA_AVAILABLE = True
except ImportError as e:
    VANNA_AVAILABLE = False
    Agent = None
    MySQLRunner = None

logger = logging.getLogger("awesome_inc_app")
if not VANNA_AVAILABLE:
    logger.warning("Vanna.AI not installed. SQL generation will not work.")


# ============================================================================
# DATABASE TOOLS
# ============================================================================

def get_database_schema(conn) -> Dict[str, List[str]]:
    """
    Fetch database schema from MySQL DW (star schema)
    
    Args:
        conn: MySQL DW connection
    
    Returns:
        Dictionary with table names and their columns
    """
    try:
        schema = {}
        cursor = conn.cursor()
        
        # Get all tables in database
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
        """)
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Get columns for each table
            cursor.execute(f"""
                SELECT COLUMN_NAME, COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}' 
                AND TABLE_SCHEMA = DATABASE()
            """)
            columns = cursor.fetchall()
            schema[table_name] = [(col, dtype) for col, dtype in columns]
        
        cursor.close()
        logger.info(f"Database schema fetched from MySQL DW: {len(schema)} tables")
        logger.info(f"Tables available: {', '.join(schema.keys())}")
        return schema
    
    except Exception as e:
        logger.error(f"Error fetching database schema from MySQL DW: {e}")
        raise


def execute_sql(conn, sql_query: str) -> pd.DataFrame:
    """
    Execute SQL query on MySQL DW and return results as DataFrame
    
    Args:
        conn: MySQL DW connection
        sql_query: SQL query string
    
    Returns:
        pandas DataFrame with query results
    """
    try:
        logger.info(f"Executing SQL query on MySQL DW: {sql_query[:100]}...")
        
        df = pd.read_sql(sql_query, conn)
        logger.info(f"Query executed successfully, rows returned: {len(df)}")
        return df
    
    except Exception as e:
        logger.error(f"Error executing SQL on MySQL DW: {e}")
        raise


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================

def generate_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Bar Chart") -> go.Figure:
    """
    Generate bar chart from DataFrame
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    try:
        logger.debug(f"Generating bar chart: {title}")
        
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), 
                   y_col: y_col.replace('_', ' ').title()},
            hover_data={x_col: True, y_col: True}
        )
        fig.update_layout(xaxis_tickangle=-45, height=500)
        logger.info("Bar chart generated successfully")
        return fig
    
    except Exception as e:
        logger.error(f"Error generating bar chart: {e}")
        raise


def generate_line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Line Chart") -> go.Figure:
    """
    Generate line chart from DataFrame
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    try:
        logger.debug(f"Generating line chart: {title}")
        
        fig = px.line(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), 
                   y_col: y_col.replace('_', ' ').title()},
            markers=True
        )
        fig.update_layout(height=500)
        logger.info("Line chart generated successfully")
        return fig
    
    except Exception as e:
        logger.error(f"Error generating line chart: {e}")
        raise


def generate_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Scatter Plot") -> go.Figure:
    """
    Generate scatter plot from DataFrame
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    try:
        logger.debug(f"Generating scatter plot: {title}")
        
        fig = px.scatter(
            df, 
            x=x_col, 
            y=y_col,
            title=title,
            labels={x_col: x_col.replace('_', ' ').title(), 
                   y_col: y_col.replace('_', ' ').title()}
        )
        fig.update_layout(height=500)
        logger.info("Scatter plot generated successfully")
        return fig
    
    except Exception as e:
        logger.error(f"Error generating scatter plot: {e}")
        raise


def generate_pie_chart(df: pd.DataFrame, values_col: str, labels_col: str, title: str = "Pie Chart") -> go.Figure:
    """
    Generate pie chart from DataFrame
    
    Args:
        df: DataFrame with data
        values_col: Column name for values
        labels_col: Column name for labels
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    try:
        logger.debug(f"Generating pie chart: {title}")
        
        fig = px.pie(
            df, 
            values=values_col, 
            names=labels_col,
            title=title
        )
        fig.update_layout(height=500)
        logger.info("Pie chart generated successfully")
        return fig
    
    except Exception as e:
        logger.error(f"Error generating pie chart: {e}")
        raise


# Define all tools as a dictionary
tools = {
    "sql_executor": execute_sql,
    "bar_chart": generate_bar_chart,
    "line_chart": generate_line_chart,
    "scatter_plot": generate_scatter_plot,
    "pie_chart": generate_pie_chart,
    "get_schema": get_database_schema
}


# ============================================================================
# VANNA.AI INTEGRATION
# ============================================================================

# Global Vanna client (initialized once)
_vanna_client = None


def initialize_vanna(config: Dict, force_reinit: bool = False) -> Any:
    """
    Initialize Vanna 2.0.1 for local SQL generation with similarity search
    
    This implementation:
    1. Loads 21 Q->SQL training pairs
    2. Provides similarity search matching for trained questions
    3. Falls back to Ollama/Mistral for novel questions
    
    Args:
        config: Configuration with MySQL settings
        force_reinit: Force re-initialization
    
    Returns:
        VannaHybrid instance with training data and similarity search
    """
    global _vanna_client
    
    if _vanna_client is not None and not force_reinit:
        logger.debug("Using cached Vanna client")
        return _vanna_client
    
    try:
        logger.info("=" * 80)
        logger.info("INITIALIZING VANNA WITH SIMILARITY SEARCH")
        logger.info("=" * 80)
        
        # Load training data (35 Q->SQL examples)
        logger.info("Loading training data (35 Q->SQL pairs)...")
        training_data = get_vanna_training_data()
        logger.info(f"[OK] Loaded {len(training_data)} training examples")
        
        # Create Vanna hybrid agent with similarity search
        _vanna_client = VannaHybrid(training_data, config)
        
        logger.info("=" * 80)
        logger.info("[OK] VANNA HYBRID READY")
        logger.info(f"  > Similarity search on {len(training_data)} trained Q->SQL pairs")
        logger.info("  > Fallback to Ollama/Mistral for novel questions")
        logger.info("=" * 80)
        
        return _vanna_client
        
    except Exception as e:
        logger.error(f"Error initializing Vanna: {e}")
        import traceback
        traceback.print_exc()
        return None


class VannaHybrid:
    """
    Hybrid Vanna implementation with EXACT KEYWORD MATCHING:
    1. Keyword-based exact match on trained Q->SQL pairs (100% only)
    2. Fallback to Ollama/Mistral for novel questions
    
    Business Keywords:
    - Metrics: sales, profit, revenue, quantity, discount, shipping_cost
    - Dimensions: region, category, product, customer, date, country, state, city
    - Operations: total, average, sum, count, top, highest, lowest, trend, return, margin
    """
    
    # Business domain keywords
    METRICS = {
        'sales', 'profit', 'revenue', 'quantity', 'discount', 'shipping', 
        'cost', 'price', 'margin', 'rate', 'return'
    }
    
    DIMENSIONS = {
        'region', 'category', 'product', 'customer', 'date', 'country', 
        'state', 'city', 'month', 'year', 'day', 'subcategory', 'segment'
    }
    
    OPERATIONS = {
        'total', 'sum', 'average', 'avg', 'count', 'top', 'highest', 'lowest',
        'trend', 'analysis', 'compare', 'performance', 'distribution', 'breakdown'
    }
    
    def __init__(self, training_data: List[Dict], config: Dict):
        """
        Initialize with training data
        
        Args:
            training_data: List of {"question": str, "sql": str} dicts
            config: Configuration dict
        """
        self.training_data = training_data
        self.config = config
        self.ready = True
        logger.debug(f"VannaHybrid initialized with {len(training_data)} training pairs")
    
    def ask(self, user_question: str, similarity_threshold: float = 1.0) -> Optional[str]:
        """
        Ask question - uses EXACT keyword matching on trained pairs ONLY
        
        Threshold is fixed at 1.0 (100% exact match required)
        
        Args:
            user_question: User's natural language question
            similarity_threshold: Ignored (always uses 1.0 for exact match)
        
        Returns:
            SQL string if exact match found, None if should fallback to Mistral
        """
        try:
            # Extract business keywords from user question
            user_keywords = self._extract_keywords(user_question)
            
            logger.debug(f"User keywords: {user_keywords}")
            
            # Try exact keyword match on training data
            for trained_pair in self.training_data:
                trained_question = trained_pair.get('question', '')
                trained_keywords = self._extract_keywords(trained_question)
                
                logger.debug(f"Trained keywords: {trained_keywords}")
                
                # EXACT MATCH: All user keywords must be in trained keywords
                # (order and phrasing don't matter, only key business terms)
                if user_keywords == trained_keywords:
                    match_score = 1.0
                    logger.info(f"[VANNA] Found EXACT keyword match (score: {match_score:.2f})")
                    logger.debug(f"[VANNA] Trained question: {trained_question}")
                    return trained_pair['sql']
            
            # No exact match found
            logger.info("[VANNA] No exact keyword match found - will use Mistral LLM")
            return None
        
        except Exception as e:
            logger.warning(f"Vanna keyword matching failed: {e}")
            return None
    
    def _extract_keywords(self, question: str) -> set:
        """
        Extract business keywords from a question
        
        Extracts only: metrics, dimensions, and operations
        Ignores: common words, articles, prepositions
        
        Args:
            question: Natural language question
        
        Returns:
            Set of extracted business keywords (lowercase)
        """
        try:
            # Normalize: lowercase, remove punctuation
            normalized = question.lower()
            # Remove common punctuation
            for char in "?!'.,:;":
                normalized = normalized.replace(char, " ")
            
            # Split into words
            words = set(normalized.split())
            
            # Keep only business-relevant keywords
            keywords = set()
            
            # Check against known business keywords
            for word in words:
                # Check if word matches or is part of a business term
                if word in self.METRICS or word in self.DIMENSIONS or word in self.OPERATIONS:
                    keywords.add(word)
                # Check for partial matches (e.g., "shipping_cost" > "shipping")
                elif any(word.startswith(metric) for metric in self.METRICS):
                    keywords.add(word)
                elif any(word.startswith(dim) for dim in self.DIMENSIONS):
                    keywords.add(word)
            
            return keywords
        
        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            return set()




def generate_sql_with_vanna(vanna_client: Any, user_question: str, config: Dict, conversation_history: List[Dict] = None) -> str:
    """
    Generate SQL using hybrid approach:
    1. Try Vanna similarity search on 21 trained Q->SQL pairs
    2. Fallback to Ollama/Mistral LLM for novel questions
    
    Args:
        vanna_client: VannaHybrid instance with training data
        user_question: User's natural language question
        config: Configuration dictionary
        conversation_history: Previous conversation turns for context
    
    Returns:
        SQL query string
    """
    try:
        logger.info(f"Generating SQL: {user_question[:100]}...")
        
        # Step 1: Try Vanna exact keyword match on trained pairs
        if vanna_client is not None and hasattr(vanna_client, 'ask'):
            try:
                logger.info("      > Checking Vanna.AI training data...")
                sql_from_vanna = vanna_client.ask(user_question, similarity_threshold=1.0)
                
                if sql_from_vanna:
                    # Found a good match in training data
                    logger.info("       MATCH FOUND in Vanna.AI training data!")
                    logger.info(f"      > Using pre-trained SQL query")
                    return sql_from_vanna
                else:
                    logger.info("      > No exact match in training data")
            
            except AttributeError:
                # ask() method doesn't exist - will fall through to LLM
                logger.info("      > Vanna.ask() not available")
            except Exception as e:
                logger.warning(f"      [WARNING] Vanna similarity search error: {e}")
        
        # Step 2: Fallback to Ollama/Mistral for novel questions
        logger.info("      > Falling back to Ollama/Mistral LLM for novel query...")
        logger.info(f"      > Model: {config.get('LLM', {}).get('OLLAMA_MODEL', 'mistral')}")
        
        ollama_url = config.get('LLM', {}).get('OLLAMA_URL', 'http://localhost:11434')
        ollama_model = config.get('LLM', {}).get('OLLAMA_MODEL', 'mistral')
        
        try:
            import requests
            
            # Get SQL generation prompt with schema validation
            sql_gen_prompt = get_sql_generation_prompt()
            
            sql_prompt = f"""{sql_gen_prompt}

QUESTION TO ANSWER: {user_question}"""
            
            # Add conversation context if available (for follow-up questions)
            if conversation_history and len(conversation_history) > 0:
                sql_prompt += "\n\nPREVIOUS CONVERSATION CONTEXT (for reference if question references 'top customer', 'these customers', etc.):\n"
                
                for idx, turn in enumerate(conversation_history[-2:], 1):  # Last 2 turns
                    q = turn.get('question', 'N/A')
                    sql_prompt += f"Q{idx}: {q}\n"
                    
                    # Include key insight to understand what data was shown
                    if 'key_insight' in turn:
                        sql_prompt += f"Result: {turn.get('key_insight', '')}\n"
                    
                    # If SQL available, show it for reference
                    if 'sql' in turn:
                        prev_sql = turn.get('sql', '')
                        if len(prev_sql) < 200:
                            sql_prompt += f"SQL used: {prev_sql}\n"
                    
                    sql_prompt += "\n"
            
            sql_prompt += "\nRemember: Generate ONLY ONE valid SELECT query. No explanations, no markdown, no multiple queries."
            
            # Call Ollama API
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": sql_prompt,
                    "stream": False,
                    "temperature": config.get('LLM', {}).get('TEMPERATURE', 0.3)
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '').strip()
                logger.info(f"       LLM response received ({len(raw_response)} chars)")
                
                # Extract FIRST SQL block from response
                # Handles cases where LLM returns multiple numbered analyses
                sql_query = None
                
                # Try to extract SQL from markdown code block
                import re
                sql_blocks = re.findall(r'```(?:sql)?\n(.*?)\n```', raw_response, re.DOTALL)
                
                if sql_blocks:
                    # Use the first SQL block found
                    sql_query = sql_blocks[0].strip()
                    logger.info("      > SQL extracted from markdown code block")
                elif raw_response.startswith("```"):
                    # Fallback: simple split if no explicit sql marker
                    parts = raw_response.split("```")
                    if len(parts) >= 2:
                        sql_query = parts[1].strip()
                        if sql_query.startswith("sql\n"):
                            sql_query = sql_query[4:].strip()
                    logger.info("      > SQL extracted from code fence")
                
                if not sql_query:
                    # If still no SQL found, try to find SELECT statement
                    select_match = re.search(r'(SELECT\s+.*?;)', raw_response, re.DOTALL | re.IGNORECASE)
                    if select_match:
                        sql_query = select_match.group(1).strip()
                        logger.info("      > SQL extracted via regex SELECT match")
                
                if sql_query:
                    logger.info("       SQL SUCCESSFULLY GENERATED by Mistral")
                    return sql_query
                else:
                    raise Exception("Could not extract SQL from LLM response")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error with Ollama: {e}")
            raise
    
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise


# ============================================================================
# LLM INTEGRATION - DATA ANALYSIS ONLY
# Note: SQL generation is now handled by Vanna.AI
# ============================================================================

def generate_analysis_response(user_question: str, data_df: pd.DataFrame, config: Dict, conversation_history: List[Dict] = None) -> str:
    """
    Generate natural language response by analyzing query results
    
    Args:
        user_question: Original user question
        data_df: Query results as DataFrame
        config: Configuration with API keys
        conversation_history: Previous conversation turns
    
    Returns:
        Natural language analysis of the data
    """
    logger.info("Generating natural language analysis of results")
    
    try:
        # Format data for LLM analysis
        data_summary = data_df.to_string()
        
        # Get analysis system prompt
        system_analysis_prompt = get_analysis_prompt()
        
        # Build analysis prompt with system context
        # Build analysis prompt with context
        analysis_prompt = f"""{system_analysis_prompt}

Question: {user_question}

Data:
{data_summary}
"""
        
        # Add conversation history if available (last 2-3 turns for multi-turn context)
        if conversation_history and len(conversation_history) > 0:
            analysis_prompt += "\n\nPrevious Conversation:\n"
            
            for idx, turn in enumerate(conversation_history[-2:], 1):  # Last 2 turns
                analysis_prompt += f"Q{idx}: {turn.get('question', 'N/A')}\n"
                
                if 'analysis' in turn:
                    prev_analysis = turn.get('analysis', '')
                    # Keep first 400 chars
                    if len(prev_analysis) > 400:
                        prev_analysis = prev_analysis[:400] + "..."
                    analysis_prompt += f"A{idx}: {prev_analysis}\n\n"
        
        analysis_prompt += "\n\nProvide your analysis:"
        
        # Use Ollama/Mistral for analysis
        try:
            logger.info("      > Using Ollama/Mistral for analysis...")
            import requests
            
            ollama_url = config.get('LLM', {}).get('OLLAMA_URL', 'http://localhost:11434')
            ollama_model = config.get('LLM', {}).get('OLLAMA_MODEL', 'mistral')
            logger.info(f"      > Model: {ollama_model}")
            logger.info(f"      > URL: {ollama_url}")
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": analysis_prompt,
                    "stream": False,
                    "temperature": 0.7  # Slightly higher for more natural language
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_response = result.get('response', '').strip()
                
                # Clean up the response: remove control characters and extra whitespace
                analysis_response = ''.join(char for char in analysis_response if char.isprintable() or char in '\n\t ')
                analysis_response = '\n'.join(line.rstrip() for line in analysis_response.split('\n'))
                analysis_response = analysis_response.strip()
                
                logger.info(f"       Analysis generated using Mistral ({len(analysis_response)} chars)")
                return analysis_response
            else:
                raise Exception(f"Ollama error: {response.status_code}")
        
        except Exception as ollama_error:
            logger.error(f"      ✗ Ollama/Mistral failed: {ollama_error}")
            # Final fallback: return basic summary
            logger.warning("      > Using fallback basic summary")
            return f"Query returned {len(data_df)} rows. Please review the data table above."
    
    except Exception as e:
        logger.error(f"Error generating analysis response: {e}")
        return f"Error analyzing data: {e}"
        # Final fallback
        return f"Query returned {len(data_df)} rows. Please review the data table above."


# ============================================================================
# PII MASKING FOR STORE MANAGER
# ============================================================================

def apply_pii_masking_for_role(df: pd.DataFrame, user_role: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply PII masking based on user role
    
    For Store Manager role:
    - Mask customer_name: "Alice Johnson" > "A*** J***"
    - Mask postal_code: "10001" > "100**"
    - Keep all business metrics unmasked (sales, profit, etc.)
    
    Args:
        df: Query results DataFrame
        user_role: User role (Sales Associate, Store Manager, Executive)
    
    Returns:
        Tuple of (masked_df, original_df)
        - masked_df: For default display (with PII masked)
        - original_df: For optional toggle view
    """
    try:
        original_df = df.copy()
        masked_df = df.copy()
        
        logger.info(f"Applying PII masking for role: {user_role}")
        
        # Only apply masking for Store Manager role
        if user_role == "Store Manager":
            # Define masking mappings for this role
            # Only mask customer PII, keep business metrics visible
            masking_mappings = {
                'customer_name': 'name',
                'postal_code': 'postal_code'
                # Note: sales, profit, shipping_cost, discount NOT masked
                # These are business metrics needed for analysis
            }
            
            # Apply masking to each column
            for column, mask_type in masking_mappings.items():
                if column not in masked_df.columns:
                    logger.debug(f"Column '{column}' not found in query results")
                    continue
                
                logger.info(f"Masking column: {column} (type: {mask_type})")
                
                if mask_type == 'name':
                    # Apply name masking: "Alice Johnson" > "A*** J***"
                    masked_df[column] = masked_df[column].apply(
                        lambda x: PIIMasking.mask_name(x, level=PIIMasking.LEVEL_PARTIAL) 
                        if pd.notna(x) else x
                    )
                
                elif mask_type == 'postal_code':
                    # Apply postal code masking: "10001" > "100**"
                    masked_df[column] = masked_df[column].apply(
                        lambda x: PIIMasking.mask_postal_code(x, show_digits=3) 
                        if pd.notna(x) else x
                    )
            
            logger.info(f"PII masking applied successfully for {user_role}")
            logger.debug(f"Masked columns: {list(masking_mappings.keys())}")
        
        else:
            # For other roles (Sales Associate, Executive), no masking
            logger.info(f"No masking applied for role: {user_role}")
        
        return masked_df, original_df
    
    except Exception as e:
        logger.error(f"Error applying PII masking: {e}")
        # Fallback: return original data if masking fails
        return df.copy(), df.copy()


# ============================================================================
# MAIN ORCHESTRATION FUNCTION
# ============================================================================

def process_question(user_question: str, config: Dict = None, conversation_history: List[Dict] = None, user_role: str = None) -> Dict[str, Any]:
    """
    Main orchestration function - processes user question end-to-end with conversation memory
    
    Implements the correct chatbot flow:
    1. Generate SQL from question
    2. Execute SQL to get data
    3. Apply PII masking based on user role (Store Manager gets masked PII)
    4. Analyze data with LLM to generate natural language response
    5. Return insights (not SQL/table) to user
    
    Args:
        user_question: Natural language question from user
        config: Configuration dictionary (loads from env.yaml if None)
        conversation_history: List of previous conversation turns (optional, for multi-turn context)
        user_role: User role (Sales Associate, Store Manager, Executive) - used for PII masking
    
    Returns:
        Dictionary with:
        - natural_response: LLM's natural language analysis ← SHOW THIS TO USER
        - data: Results DataFrame (masked for Store Manager)
        - data_original: Original unmasked DataFrame (for toggle)
        - conversation_turn: Data to store in conversation history
        - error: Error message if any
    """
    
    logger.info("="*80)
    logger.info("PIPELINE START")
    logger.info("="*80)
    logger.info(f"Question: {user_question}")
    logger.info(f"User Role: {user_role}")
    logger.info(f"Context Turns: {len(conversation_history) if conversation_history else 0}")
    logger.info("="*80)
    
    result = {
        "natural_response": None,
        "data": None,
        "data_original": None,
        "error": None,
        "conversation_turn": None
    }
    
    try:
        # Load config if not provided
        if config is None:
            config = load_env_config()
        
        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = []
        
        # =====================================================================
        # STEP 1: Generate SQL Query using Vanna.AI (Backend only, hidden from user)
        # =====================================================================
        logger.info("\nSTEP 1: Connecting to MySQL Data Warehouse...")
        conn = get_mysql_connection(config)
        logger.info("   [SUCCESS] Connected to MySQL OLAP database")
        
        logger.info("\nSTEP 2: Initializing SQL Generator...")
        vanna_client = initialize_vanna(config)
        logger.info("   [SUCCESS] Vanna.AI initialized with training data")
        
        logger.info("\nSTEP 3: Generating SQL Query...")
        logger.info("   > Trying Vanna.AI similarity search first...")
        
        # Pass conversation context for follow-up questions
        sql_query = generate_sql_with_vanna(vanna_client, user_question, config, conversation_history)
        logger.info(f"   [SUCCESS] SQL Generated: {sql_query[:100]}...")
        logger.info(f"   > Full SQL length: {len(sql_query)} characters")
        
        # =====================================================================
        # STEP 2: Execute SQL to get data
        # =====================================================================
        logger.info("\nSTEP 4: Executing SQL on MySQL DW...")
        data_df = tools["sql_executor"](conn, sql_query)
        logger.info("   [SUCCESS] Query executed successfully")
        logger.info(f"   > Rows returned: {len(data_df)}")
        logger.info(f"   > Columns: {list(data_df.columns)}")
        
        # =====================================================================
        # STEP 2.5: Apply PII Masking based on user role
        # =====================================================================
        logger.info("\nSTEP 5: Applying PII Masking...")
        if user_role is None:
            user_role = "Sales Associate"  # Default role if not specified
        
        logger.info(f"   > User role: {user_role}")
        data_df_masked, data_df_original = apply_pii_masking_for_role(data_df, user_role)
        
        # Store both masked and original for later use
        result["data"] = data_df_masked  # Default display (masked)
        result["data_original"] = data_df_original  # For toggle option
        
        if user_role == "Store Manager":
            logger.info("   [SUCCESS] PII masking applied (customer_name, postal_code)")
        else:
            logger.info(f"   > No masking required for {user_role}")
        
        # =====================================================================
        # STEP 3: Generate Natural Language Response (LLM analyzes data)
        # =====================================================================
        logger.info("\nSTEP 6: Generating Natural Language Analysis...")
        logger.info(f"   > Building context with {len(data_df_masked)} rows")
        logger.info(f"   > Including {len(conversation_history) if conversation_history else 0} previous turns for context")
        logger.info("   > Calling LLM (Gemini/Mistral fallback)...")
        
        natural_response = generate_analysis_response(
            user_question, 
            data_df_masked,  # Analyze masked data
            config, 
            conversation_history
        )
        result["natural_response"] = natural_response
        logger.info(f"   [SUCCESS] Natural language response generated ({len(natural_response)} chars)")
        
        # =====================================================================
        # STEP 4: Extract key insight and store conversation turn
        # =====================================================================
        logger.info("\nSTEP 7: Storing Conversation Context...")
        key_insight = _extract_key_insight(data_df, user_question)
        
        # Store this turn in conversation history for next turn
        result["conversation_turn"] = {
            "question": user_question,  # Changed from user_question to question for consistency
            "sql": sql_query,
            "num_rows": len(data_df),
            "columns": data_df.columns.tolist(),
            "key_insight": key_insight,
            "analysis": natural_response  # Store full response for context (used in generate_analysis_response)
        }
        logger.info("   [SUCCESS] Conversation turn saved for multi-turn context")
        
        logger.info("\n" + "="*80)
        logger.info("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80 + "\n")
        
        # Close connection
        conn.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        result["error"] = str(e)
        return result


def _extract_key_insight(df: pd.DataFrame, user_question: str) -> str:
    """
    Extract key insight from results for conversation history
    
    Args:
        df: Results DataFrame
        user_question: User's question
    
    Returns:
        Brief insight summary
    """
    try:
        if df.empty:
            return "No results found"
        
        # Try to get the most important numeric column
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            main_col = numeric_cols[0]
            max_val = df[main_col].max()
            min_val = df[main_col].min()
            avg_val = df[main_col].mean()
            
            insight = f"Values range: {min_val:.2f} to {max_val:.2f}, avg: {avg_val:.2f}. Total rows: {len(df)}"
            return insight
        else:
            return f"Retrieved {len(df)} rows"
    
    except Exception as e:
        logger.debug(f"Error extracting insight: {e}")
        return f"Retrieved {len(df)} rows"


def _determine_and_generate_chart(df: pd.DataFrame, user_question: str) -> Tuple[str, go.Figure]:
    """
    Determine chart type and generate appropriate visualization
    
    Args:
        df: Results DataFrame
        user_question: User's original question
    
    Returns:
        Tuple of (chart_type, figure)
    """
    try:
        # Simple heuristic to determine chart type
        question_lower = user_question.lower()
        
        if "trend" in question_lower or "over time" in question_lower:
            chart_type = "line_chart"
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = tools["line_chart"](df, cols[0], cols[1], title=user_question)
            else:
                fig = go.Figure()
        
        elif "breakdown" in question_lower or "reason" in question_lower:
            chart_type = "pie_chart"
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = tools["pie_chart"](df, cols[1], cols[0], title=user_question)
            else:
                fig = go.Figure()
        
        elif "correlation" in question_lower or "relationship" in question_lower:
            chart_type = "scatter_plot"
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = tools["scatter_plot"](df, cols[0], cols[1], title=user_question)
            else:
                fig = go.Figure()
        
        else:
            # Default to bar chart
            chart_type = "bar_chart"
            cols = df.columns.tolist()
            if len(cols) >= 2:
                fig = tools["bar_chart"](df, cols[0], cols[1], title=user_question)
            else:
                fig = go.Figure()
        
        logger.info(f"Chart type determined: {chart_type}")
        return chart_type, fig
    
    except Exception as e:
        logger.error(f"Error determining chart type: {e}")
        return "table", go.Figure()





