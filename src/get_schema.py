"""
Quick script to retrieve and save table schema.
"""

import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Connect
conn = psycopg2.connect(
    host=os.getenv('HOST'),
    user=os.getenv('USER'),
    database=os.getenv('DATABASE'),
    password=os.getenv('PASSWORD')
)

try:
    with conn.cursor() as cursor:
        # Get all columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'bt' AND table_name = 'cldn_strikes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        # Save to file
        output_file = Path(__file__).parent.parent / 'SCHEMA.txt'
        with open(output_file, 'w') as f:
            f.write("CLDN Strikes Table Schema\n")
            f.write("=" * 60 + "\n\n")
            for col_name, col_type, nullable in columns:
                null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                f.write(f"  {col_name:<30} {col_type:<20} {null_str}\n")
        
        print(f"\nSchema saved to: {output_file}")
        print(f"\nColumns ({len(columns)} total):")
        for col_name, col_type, nullable in columns:
            print(f"  {col_name:<30} {col_type:<20}")

finally:
    conn.close()
