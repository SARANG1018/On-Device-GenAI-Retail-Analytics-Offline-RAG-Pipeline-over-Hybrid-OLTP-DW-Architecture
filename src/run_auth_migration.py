#!/usr/bin/env python3
import psycopg2
import mysql.connector
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_postgres_migration(conn_string: str, sql_file: str):
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Execute SQL
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"PostgreSQL Migration completed successfully from {sql_file}")
        return True
    
    except Exception as e:
        logger.error(f"PostgreSQL Migration failed: {e}")
        return False


def run_mysql_migration(host: str, user: str, password: str, database: str, sql_file: str):
    """
    Execute SQL migration file on MySQL
    
    Args:
        host: MySQL host
        user: MySQL user
        password: MySQL password
        database: MySQL database
        sql_file: Path to SQL file to execute
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for statement in statements:
            cursor.execute(statement)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"MySQL Migration completed successfully from {sql_file}")
        return True
    
    except Exception as e:
        logger.error(f"MySQL Migration failed: {e}")
        return False


if __name__ == "__main__":
    import yaml
    
    # Load config
    try:
        with open('env.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config_path = Path(__file__).parent / 'env.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    logger.info("=" * 70)
    logger.info("USER AUTHENTICATION MIGRATION")
    logger.info("=" * 70)
    
    # =====================================================================
    # PostgreSQL OLTP Migration (Sales Associate Users)
    # =====================================================================
    logger.info("\n[1/2] PostgreSQL OLTP Migration...")
    logger.info("-" * 70)
    
    pg_config = config['POSTGRES']
    pg_conn_string = f"postgresql://{pg_config['USER']}:{pg_config['PASSWORD']}@{pg_config['HOST']}:{pg_config['PORT']}/{pg_config['DB']}"
    pg_sql_file = Path(__file__).parent.parent / 'sql' / 'postgresql' / 'create_user_tables_postgresql.sql'
    
    logger.info(f"Database: {pg_config['HOST']}:{pg_config['PORT']}/{pg_config['DB']}")
    logger.info(f"Table: fa25_ssc_users_sales_associate (Sales Associate credentials)")
    
    pg_success = run_postgres_migration(pg_conn_string, str(pg_sql_file))
    
    if pg_success:
        logger.info("✓ PostgreSQL OLTP ready for Sales Associate authentication")
    else:
        logger.error("✗ PostgreSQL OLTP migration failed")
    
    # =====================================================================
    # MySQL OLAP Migration (Store Manager & Executive Users)
    # =====================================================================
    logger.info("\n[2/2] MySQL OLAP Migration...")
    logger.info("-" * 70)
    
    mysql_config = config['MYSQL']
    mysql_sql_file = Path(__file__).parent.parent / 'sql' / 'mysql' / 'create_user_tables_mysql.sql'
    
    logger.info(f"Database: {mysql_config['HOST']}:{mysql_config['PORT']}/{mysql_config['DB']}")
    logger.info(f"Tables: fa25_ssc_users_store_manager (Store Manager credentials)")
    logger.info(f"        fa25_ssc_users_executive (Executive credentials)")
    
    mysql_success = run_mysql_migration(
        mysql_config['HOST'],
        mysql_config['USER'],
        mysql_config['PASSWORD'],
        mysql_config['DB'],
        str(mysql_sql_file)
    )
    
    if mysql_success:
        logger.info("✓ MySQL OLAP ready for Store Manager and Executive authentication")
    else:
        logger.error("✗ MySQL OLAP migration failed")
    
    # =====================================================================
    # Summary
    # =====================================================================
    logger.info("\n" + "=" * 70)
    if pg_success and mysql_success:
        logger.info("SUCCESS: All user authentication tables created!")
        logger.info("=" * 70)
        logger.info("\nDatabase Structure:")
        logger.info("  PostgreSQL OLTP:    fa25_ssc_users_sales_associate")
        logger.info("  MySQL OLAP:         fa25_ssc_users_store_manager")
        logger.info("  MySQL OLAP:         fa25_ssc_users_executive")
        logger.info("\nUsers can now:")
        logger.info("  1. Signup with their role")
        logger.info("  2. Login without re-signup after refresh")
        logger.info("  3. Reset password via security questions")
        logger.info("=" * 70)
    else:
        logger.error("FAILED: Some migrations did not complete")
        logger.error("=" * 70)



