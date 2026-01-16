import logging
import yaml
import os
from pathlib import Path
import psycopg2
import mysql.connector
from psycopg2 import pool
from datetime import datetime
import json
from functools import wraps
import traceback


def setup_logger(name, log_file=None, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers - if logger already has handlers, return it as-is
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Error handling decorator
def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        func_name = func.__qualname__
        
        try:
            logger.debug(f"ENTER: {func_name}")
            result = func(*args, **kwargs)
            logger.debug(f"EXIT: {func_name} - Success")
            return result
        
        except Exception as e:
            error_msg = f"ERROR in {func_name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise  # Re-raise so caller can handle
    
    return wrapper


# Environment configuration
def load_env_config(env_file_path='env.yaml'):
    # Look for env.yaml in project root
    if not os.path.exists(env_file_path):
        project_root = Path(__file__).parent.parent
        env_file_path = project_root / 'env.yaml'
    
    try:
        with open(env_file_path, 'r') as f:
            config = yaml.safe_load(f)
        logger = logging.getLogger(__name__)
        logger.info(f"Configuration loaded from {env_file_path}")
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"env.yaml not found at {env_file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing env.yaml: {e}")


# Database connections
postgres_pool = None
mysql_pool = None


def get_postgres_connection(config):
    global postgres_pool
    
    logger = logging.getLogger(__name__)
    
    try:
        pg_config = config.get('POSTGRES', {})
        
        # Validate required config
        required_keys = ['HOST', 'PORT', 'USER', 'PASSWORD', 'DB']
        missing_keys = [k for k in required_keys if not pg_config.get(k)]
        if missing_keys:
            raise ValueError(f"Missing PostgreSQL config keys: {missing_keys}")
        
        if postgres_pool is None:
            logger.info(f"Creating PostgreSQL connection pool to {pg_config.get('HOST')}:{pg_config.get('PORT')}")
            postgres_pool = psycopg2.pool.SimpleConnectionPool(
                5, 50,
                host=pg_config.get('HOST'),
                port=pg_config.get('PORT'),
                user=pg_config.get('USER'),
                password=pg_config.get('PASSWORD'),
                database=pg_config.get('DB')
            )
            logger.info("PostgreSQL connection pool created")
        
        conn = postgres_pool.getconn()
        logger.debug("PostgreSQL connection acquired from pool")
        return conn
    
    except psycopg2.OperationalError as e:
        logger.error(f"PostgreSQL connection error: {e}")
        logger.error("Check: hostname, port, credentials, firewall rules")
        raise
    except psycopg2.DatabaseError as e:
        logger.error(f"PostgreSQL database error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to PostgreSQL: {e}")
        raise


def release_postgres_connection(conn):
    """
    Release PostgreSQL connection back to pool
    
    Args:
        conn: PostgreSQL connection object
    """
    global postgres_pool
    logger = logging.getLogger(__name__)
    
    try:
        if postgres_pool and conn:
            postgres_pool.putconn(conn)
            logger.info("PostgreSQL connection released back to pool")
    except Exception as e:
        logger.error(f"Error releasing PostgreSQL connection: {e}")


def get_mysql_connection(config):
    """
    Create MySQL connection with error handling
    
    Args:
        config: Configuration dictionary
    
    Returns:
        MySQL database connection
    
    Raises:
        mysql.connector.Error: If connection fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        mysql_config = config.get('MYSQL', {})
        
        # Validate required config
        required_keys = ['HOST', 'PORT', 'USER', 'PASSWORD', 'DB']
        missing_keys = [k for k in required_keys if not mysql_config.get(k)]
        if missing_keys:
            logger.warning(f"⚠ MySQL not configured. Missing keys: {missing_keys}")
            logger.info("Using default localhost config")
        
        logger.info(f"Connecting to MySQL at {mysql_config.get('HOST')}:{mysql_config.get('PORT')}")
        
        conn = mysql.connector.connect(
            host=mysql_config.get('HOST', 'localhost'),
            port=mysql_config.get('PORT', 3306),
            user=mysql_config.get('USER', 'root'),
            password=mysql_config.get('PASSWORD', ''),
            database=mysql_config.get('DB', 'awesome_olap')
        )
        logger.info("MySQL connection established")
        return conn
    
    except mysql.connector.errors.ProgrammingError as e:
        logger.error(f"MySQL authentication error: {e}")
        logger.error("Check: username, password, database name")
        raise
    except mysql.connector.errors.DatabaseError as e:
        logger.error(f"MySQL database error: {e}")
        raise
    except mysql.connector.Error as e:
        logger.error(f"MySQL connection error: {e}")
        logger.error("Check: host, port, service running, firewall rules")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MySQL: {e}")
        raise


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def execute_query(conn, query, fetch_all=True):
    """
    Execute a query on PostgreSQL and return results
    
    Args:
        conn: PostgreSQL connection
        query: SQL query string
        fetch_all: If True, fetch all results; if False, fetch one
    
    Returns:
        Query results (list of tuples or single tuple)
    """
    logger = logging.getLogger(__name__)
    
    try:
        cursor = conn.cursor()
        logger.debug(f"Executing query: {query[:100]}...")
        cursor.execute(query)
        
        if fetch_all:
            results = cursor.fetchall()
        else:
            results = cursor.fetchone()
        
        cursor.close()
        logger.info(f"Query executed successfully, rows returned: {len(results) if fetch_all else 1}")
        return results
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise


# ============================================================================
# CDC TRACKING (Change Data Capture via TBL_LAST_DT)
# ============================================================================

def get_last_etl_run_timestamp(config, table_name='FA25_SSC_ETL_LOG'):
    """
    Get the timestamp of the last successful ETL run from MySQL DW
    
    This enables INCREMENTAL loads - we only extract records changed since last run
    
    Args:
        config: Configuration dictionary
        table_name: Name of ETL log table (default: FA25_SSC_ETL_LOG)
    
    Returns:
        Timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        Returns '1900-01-01 00:00:00' if first run
    """
    logger = logging.getLogger(__name__)
    
    try:
        conn = get_mysql_connection(config)
        cursor = conn.cursor()
        
        # Query last successful ETL run
        sql = f"""
        SELECT MAX(run_timestamp) as last_run 
        FROM {table_name} 
        WHERE status = 'SUCCESS'
        """
        
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0]:
            last_timestamp = result[0].strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"CDC: Last ETL run was at {last_timestamp}")
            return last_timestamp
        else:
            logger.info("CDC: First ETL run - will extract all records")
            return '1900-01-01 00:00:00'
    
    except Exception as e:
        logger.error(f"Error getting last ETL run timestamp: {e}")
        logger.warning("CDC: Defaulting to first run (will extract all records)")
        return '1900-01-01 00:00:00'


def save_etl_run_metadata(config, status, records_processed, table_name='FA25_SSC_ETL_LOG'):
    """
    Save ETL run metadata to MySQL DW for CDC tracking
    
    This logs each ETL run for audit trail and enables incremental loads
    
    Args:
        config: Configuration dictionary
        status: 'SUCCESS' or 'FAILED'
        records_processed: Number of records processed
        table_name: Name of ETL log table (default: FA25_SSC_ETL_LOG)
    
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        conn = get_mysql_connection(config)
        cursor = conn.cursor()
        
        sql = f"""
        INSERT INTO {table_name} (run_timestamp, status, records_extracted, created_at)
        VALUES (NOW(), %s, %s, NOW())
        """
        
        cursor.execute(sql, (status, records_processed))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"CDC: ETL run logged - Status: {status}, Records: {records_processed}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving ETL run metadata: {e}")
        return False


def get_changed_records_since_last_run(config, table_name, last_timestamp):
    """
    Query PostgreSQL OLTP for records changed since last ETL run
    
    Uses CDC column (TBL_LAST_DT) to get only changed records
    Enables incremental load instead of full scan
    
    Args:
        config: Configuration dictionary
        table_name: Table name to query (TBL_SALES, TBL_RETURNS, etc.)
        last_timestamp: Timestamp of last ETL run
    
    Returns:
        List of changed records, or empty list if none
    """
    logger = logging.getLogger(__name__)
    
    try:
        conn = get_postgres_connection(config)
        cursor = conn.cursor()
        
        sql = f"""
        SELECT * FROM {table_name}
        WHERE TBL_LAST_DT > '{last_timestamp}'
        ORDER BY TBL_LAST_DT ASC
        """
        
        cursor.execute(sql)
        changed_records = cursor.fetchall()
        
        cursor.close()
        release_postgres_connection(conn)
        
        logger.info(f"CDC: Found {len(changed_records)} changed records in {table_name} since {last_timestamp}")
        return changed_records
    
    except Exception as e:
        logger.error(f"Error querying changed records from {table_name}: {e}")
        return []


def get_cdc_status():
    """
    Get current CDC (Change Data Capture) status for debugging
    
    Returns:
        Dictionary with CDC statistics
    """
    return {
        "tracking_method": "TBL_LAST_DT column with database triggers",
        "extract_strategy": "Incremental - only changed records since last run",
        "timestamp_source": "FA25_SSC_ETL_LOG table in MySQL DW",
        "database_trigger": "PostgreSQL trigger sets TBL_LAST_DT = NOW() on INSERT/UPDATE",
        "full_scan_fallback": "First run defaults to '1900-01-01 00:00:00' to get all records"
    }


# Initialize logger at module level
logger = setup_logger(
    name='awesome_inc_app',
    log_file='logs/app.log',
    level=logging.INFO
)




