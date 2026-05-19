# Connect to the CWFIS db, query recent strikes, and export to CSV.

import psycopg2
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys

# Handle both relative and absolute imports
try:
    from .config import DB_CONFIG, OUTPUT_DIR, LOG_LEVEL
except ImportError:
    from config import DB_CONFIG, OUTPUT_DIR, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class LightningDBConnector:
    
    def __init__(self):

        self.host = DB_CONFIG['host']
        self.user = DB_CONFIG['user']
        self.database = DB_CONFIG['database']
        self.table = DB_CONFIG['table']
        self.password = DB_CONFIG.get('password')
        self.conn = None
        
    def connect(self):
        
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                database=self.database,
                password=self.password
            )
            logger.info(f"Connected to {self.database} on {self.host}")
            return self.conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_table_info(self):
       
        if not self.conn:
            self.connect()
        
        try:
            with self.conn.cursor() as cursor:
                # Get table schema
                schema_query = f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{self.table.split(".")[-1]}'
                    ORDER BY ordinal_position;
                """
                cursor.execute(schema_query)
                schema = cursor.fetchall()
                
                # Get row count
                count_query = f"SELECT COUNT(*) FROM {self.table};"
                cursor.execute(count_query)
                row_count = cursor.fetchone()[0]
                
                columns = [col[0] for col in schema]
                
                # The time column is rep_date
                time_col = 'rep_date' if 'rep_date' in columns else None
                
                time_range = None
                if time_col:
                    time_query = f"""
                        SELECT MIN("{time_col}"), MAX("{time_col}") 
                        FROM {self.table};
                    """
                    cursor.execute(time_query)
                    time_range = cursor.fetchone()
                
                return {
                    'schema': schema,
                    'row_count': row_count,
                    'time_range': time_range,
                    'columns': columns,
                    'time_column': time_col
                }
        except psycopg2.Error as e:
            logger.error(f"Error retrieving table info: {e}")
            raise
    
    def query_strikes(self, hours=48):
      
        if not self.conn:
            self.connect()
        
        try:
            # First, get table info to find time column
            info = self.get_table_info()
            time_col = info['time_column']
            
            if not time_col:
                logger.error("Could not find time column in table")
                return pd.DataFrame()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = f"""
                SELECT * FROM {self.table}
                WHERE "{time_col}" >= %s
                ORDER BY "{time_col}" DESC;
            """
            
            df = pd.read_sql(query, self.conn, params=(cutoff_time,))
            logger.info(f"Retrieved {len(df)} strikes from past {hours} hours")
            return df
        except psycopg2.Error as e:
            logger.error(f"Error querying strikes: {e}")
            raise
    
    def export_to_csv(self, df, hours=48):
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        filename = f"CLDN_export_{hours}h_{timestamp}.csv"
        filepath = OUTPUT_DIR['tmp'] / filename
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(df)} records to {filepath}")
        return filepath
