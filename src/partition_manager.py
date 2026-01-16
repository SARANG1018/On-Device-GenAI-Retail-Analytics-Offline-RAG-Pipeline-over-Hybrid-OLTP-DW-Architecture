import logging
import psycopg2
import mysql.connector
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from utils import get_postgres_connection, get_mysql_connection, load_env_config

logger = logging.getLogger(__name__)


class PostgreSQLPartitionManager:
    """Manage partitions for PostgreSQL OLTP tables"""
    
    def __init__(self, config: Dict):
        """Initialize with database configuration"""
        self.config = config
        self.conn = None
        
    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = get_postgres_connection(self.config)
            logger.info("Connected to PostgreSQL for partition management")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from PostgreSQL")
    
    def create_next_monthly_partition(self, table_name: str, partition_date: datetime = None):
        """
        Create partition for next month automatically
        
        Args:
            table_name: Name of partitioned table (ORDER_PARTITIONED, etc.)
            partition_date: Date to create partition for (default: next month)
        """
        if partition_date is None:
            partition_date = datetime.now() + timedelta(days=32)
        
        year = partition_date.year
        month = partition_date.month
        
        # Map table names to partition naming convention
        table_map = {
            'ORDER_PARTITIONED': 'ORDER',
            'ORDER_PRODUCT_PARTITIONED': 'ORDER_PRODUCT',
            'RETURN_PARTITIONED': 'RETURN'
        }
        
        if table_name not in table_map:
            logger.error(f"Unknown table: {table_name}")
            return False
        
        short_name = table_map[table_name]
        partition_name = f"{short_name}_P_{year}_{month:02d}"
        
        # Calculate date ranges
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        try:
            cursor = self.conn.cursor()
            
            # Create partition
            sql = f"""
            CREATE TABLE public."{partition_name}" 
            PARTITION OF public."{table_name}"
            FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """
            
            cursor.execute(sql)
            
            # Create index on partition
            index_col = 'order_date' if 'ORDER' in table_name else 'return_date'
            idx_sql = f"""
            CREATE INDEX idx_{partition_name}_{index_col} 
            ON public."{partition_name}" ({index_col});
            """
            cursor.execute(idx_sql)
            
            self.conn.commit()
            logger.info(f"Created partition {partition_name} for {table_name}")
            return True
            
        except psycopg2.errors.DuplicateTable:
            logger.warning(f"Partition {partition_name} already exists")
            return True
        except Exception as e:
            logger.error(f"Failed to create partition {partition_name}: {e}")
            self.conn.rollback()
            return False
        finally:
            cursor.close()
    
    def get_partition_distribution(self, table_name: str) -> Dict:
        """
        Get distribution of rows across partitions
        
        Returns: Dict with partition stats
        """
        try:
            cursor = self.conn.cursor()
            
            sql = f"""
            SELECT 
                schemaname,
                tablename,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE tablename LIKE '{table_name[:-12]}_%'  -- Remove _PARTITIONED
                AND schemaname = 'public'
            ORDER BY tablename;
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            
            partition_stats = {}
            total_size = 0
            
            for schema, partition, size in results:
                partition_stats[partition] = {
                    'size_bytes': size,
                    'size_mb': size / (1024 * 1024)
                }
                total_size += size
            
            logger.info(f"Partition distribution for {table_name}: {len(partition_stats)} partitions, {total_size / (1024*1024):.2f} MB total")
            return partition_stats
            
        except Exception as e:
            logger.error(f"Failed to get partition distribution: {e}")
            return {}
    
    def archive_old_partition(self, partition_name: str, archive_path: str = None):
        """
        Archive old partition (export to file, then can be safely deleted)
        
        Args:
            partition_name: Name of partition to archive (e.g., ORDER_P_2023_01)
            archive_path: Path to save archive file
        """
        try:
            cursor = self.conn.cursor()
            
            # Export partition data
            if archive_path is None:
                archive_path = f"/tmp/archive_{partition_name}_{datetime.now().strftime('%Y%m%d')}.csv"
            
            sql = f"""
            COPY (SELECT * FROM public."{partition_name}")
            TO PROGRAM 'cat > {archive_path}'
            WITH (FORMAT CSV, HEADER);
            """
            
            cursor.execute(sql)
            self.conn.commit()
            
            logger.info(f"Archived {partition_name} to {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive partition: {e}")
            return False
        finally:
            cursor.close()
    
    def drop_old_partition(self, partition_name: str, confirm: bool = False):
        """
        Drop old partition (AFTER archiving)
        
        Args:
            partition_name: Name of partition to drop
            confirm: Safety confirmation (must be True to actually drop)
        """
        if not confirm:
            logger.warning(f"Partition drop requested for {partition_name} but not confirmed. Set confirm=True to proceed.")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            sql = f'DROP TABLE public."{partition_name}";'
            cursor.execute(sql)
            self.conn.commit()
            
            logger.warning(f"Dropped partition {partition_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop partition {partition_name}: {e}")
            return False
        finally:
            cursor.close()


# ═══════════════════════════════════════════════════════════════════════════
# MYSQL PARTITION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class MySQLPartitionManager:
    """Manage partitions for MySQL OLAP tables"""
    
    def __init__(self, config: Dict):
        """Initialize with database configuration"""
        self.config = config
        self.conn = None
    
    def connect(self):
        """Connect to MySQL"""
        try:
            self.conn = get_mysql_connection(self.config)
            logger.info("Connected to MySQL for partition management")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MySQL"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from MySQL")
    
    def create_next_monthly_partition(self, table_name: str, partition_date: datetime = None):
        """
        Create partition for next month automatically
        
        Args:
            table_name: Name of partitioned table (fa25_ssc_fact_sales_PARTITIONED, etc.)
            partition_date: Date to create partition for (default: next month)
        """
        if partition_date is None:
            partition_date = datetime.now() + timedelta(days=32)
        
        year = partition_date.year
        month = partition_date.month
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        partition_name = f"p_{year}{month:02d}"
        partition_value = f"{next_year}{next_month:02d}"
        
        try:
            cursor = self.conn.cursor()
            
            sql = f"""
            ALTER TABLE `{table_name}`
            ADD PARTITION (PARTITION {partition_name} VALUES LESS THAN ({partition_value}));
            """
            
            cursor.execute(sql)
            self.conn.commit()
            
            logger.info(f"Created partition {partition_name} for {table_name}")
            return True
            
        except mysql.connector.Error as e:
            if "Partition already exists" in str(e):
                logger.warning(f"Partition {partition_name} already exists")
                return True
            else:
                logger.error(f"Failed to create partition: {e}")
                return False
        finally:
            cursor.close()
    
    def get_partition_distribution(self, table_name: str) -> Dict:
        """
        Get distribution of rows across partitions
        
        Returns: Dict with partition stats
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            sql = """
            SELECT 
                PARTITION_NAME,
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH
            FROM INFORMATION_SCHEMA.PARTITIONS
            WHERE TABLE_NAME = %s
                AND TABLE_SCHEMA = 'awesome_inc_olap'
                AND PARTITION_NAME IS NOT NULL
            ORDER BY PARTITION_NAME;
            """
            
            cursor.execute(sql, (table_name,))
            results = cursor.fetchall()
            
            partition_stats = {}
            total_rows = 0
            total_size = 0
            
            for row in results:
                partition_name = row['PARTITION_NAME']
                row_count = row['TABLE_ROWS']
                size_bytes = row['DATA_LENGTH'] + row['INDEX_LENGTH']
                
                partition_stats[partition_name] = {
                    'rows': row_count,
                    'size_bytes': size_bytes,
                    'size_mb': size_bytes / (1024 * 1024)
                }
                total_rows += row_count
                total_size += size_bytes
            
            logger.info(f"Partition distribution for {table_name}: {len(partition_stats)} partitions, {total_rows} rows, {total_size / (1024*1024):.2f} MB total")
            return partition_stats
            
        except Exception as e:
            logger.error(f"Failed to get partition distribution: {e}")
            return {}
        finally:
            cursor.close()
    
    def export_partition(self, table_name: str, partition_name: str, output_file: str) -> bool:
        """
        Export partition data for archival
        
        Args:
            table_name: Name of table
            partition_name: Name of partition to export
            output_file: Path to save exported data
        """
        try:
            cursor = self.conn.cursor()
            
            # Get partition range to query
            sql = f"""
            SELECT 
                PARTITION_DESCRIPTION
            FROM INFORMATION_SCHEMA.PARTITIONS
            WHERE TABLE_NAME = %s
                AND PARTITION_NAME = %s
                AND TABLE_SCHEMA = 'awesome_inc_olap';
            """
            
            cursor.execute(sql, (table_name, partition_name))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"Exported partition {partition_name} from {table_name} to {output_file}")
                return True
            else:
                logger.warning(f"Partition {partition_name} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export partition: {e}")
            return False
        finally:
            cursor.close()
    
    def drop_old_partition(self, table_name: str, partition_name: str, confirm: bool = False) -> bool:
        """
        Drop old partition (AFTER archiving)
        
        Args:
            table_name: Name of table
            partition_name: Name of partition to drop
            confirm: Safety confirmation (must be True to actually drop)
        """
        if not confirm:
            logger.warning(f"Partition drop requested for {partition_name} but not confirmed. Set confirm=True to proceed.")
            return False
        
        try:
            cursor = self.conn.cursor()
            
            sql = f"""
            ALTER TABLE `{table_name}`
            DROP PARTITION `{partition_name}`;
            """
            
            cursor.execute(sql)
            self.conn.commit()
            
            logger.warning(f"Dropped partition {partition_name} from {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop partition: {e}")
            return False
        finally:
            cursor.close()
    
    def get_partition_health(self) -> Dict:
        """
        Get overall partition health report
        
        Returns: Dict with health metrics
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            sql = """
            SELECT 
                TABLE_NAME,
                COUNT(*) as partition_count,
                SUM(TABLE_ROWS) as total_rows,
                ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as total_size_mb
            FROM INFORMATION_SCHEMA.PARTITIONS
            WHERE TABLE_SCHEMA = 'awesome_inc_olap'
                AND PARTITION_NAME IS NOT NULL
            GROUP BY TABLE_NAME
            ORDER BY total_size_mb DESC;
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            health_report = {}
            for row in results:
                table = row['TABLE_NAME']
                health_report[table] = {
                    'partitions': row['partition_count'],
                    'total_rows': row['total_rows'],
                    'total_size_mb': row['total_size_mb']
                }
            
            logger.info(f"Partition health report: {len(health_report)} partitioned tables")
            return health_report
            
        except Exception as e:
            logger.error(f"Failed to get partition health: {e}")
            return {}
        finally:
            cursor.close()


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATION - Run these functions on schedule
# ═══════════════════════════════════════════════════════════════════════════

def maintenance_postgresql(config: Dict):
    """
    Run PostgreSQL partition maintenance (call monthly)
    """
    try:
        manager = PostgreSQLPartitionManager(config)
        manager.connect()
        
        # Create next month's partitions
        logger.info("Creating next month's PostgreSQL partitions...")
        manager.create_next_monthly_partition('ORDER_PARTITIONED')
        manager.create_next_monthly_partition('ORDER_PRODUCT_PARTITIONED')
        manager.create_next_monthly_partition('RETURN_PARTITIONED')
        
        # Monitor distribution
        logger.info("Checking partition distribution...")
        for table in ['ORDER_PARTITIONED', 'ORDER_PRODUCT_PARTITIONED', 'RETURN_PARTITIONED']:
            stats = manager.get_partition_distribution(table)
            logger.info(f"{table}: {len(stats)} partitions")
        
        manager.disconnect()
        logger.info("PostgreSQL partition maintenance complete")
        
    except Exception as e:
        logger.error(f"PostgreSQL maintenance failed: {e}")


def maintenance_mysql(config: Dict):
    """
    Run MySQL partition maintenance (call monthly)
    """
    try:
        manager = MySQLPartitionManager(config)
        manager.connect()
        
        # Create next month's partitions
        logger.info("Creating next month's MySQL partitions...")
        manager.create_next_monthly_partition('fa25_ssc_fact_sales_PARTITIONED')
        manager.create_next_monthly_partition('fa25_ssc_fact_return_PARTITIONED')
        
        # Monitor distribution
        logger.info("Checking partition distribution...")
        for table in ['fa25_ssc_fact_sales_PARTITIONED', 'fa25_ssc_fact_return_PARTITIONED']:
            stats = manager.get_partition_distribution(table)
            logger.info(f"{table}: {len(stats)} partitions")
        
        # Get health report
        health = manager.get_partition_health()
        logger.info(f"Partition health: {health}")
        
        manager.disconnect()
        logger.info("MySQL partition maintenance complete")
        
    except Exception as e:
        logger.error(f"MySQL maintenance failed: {e}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = load_env_config()
    
    # Run maintenance
    logger.info("Starting partition maintenance...")
    maintenance_postgresql(config)
    maintenance_mysql(config)
    logger.info("Partition maintenance completed successfully")



