#!/usr/bin/env python3
"""
Utility to reset/clear Airtable data for fresh monitoring runs
"""

import os
import sys
from dotenv import load_dotenv
from pyairtable import Api
from loguru import logger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()


def reset_airtable_data():
    """Delete all records from the Pokebot Airtable"""
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "Pokebot")
    
    if not api_key or not base_id:
        logger.error("❌ Airtable credentials not configured")
        return False
    
    try:
        api = Api(api_key)
        table = api.table(base_id, table_name)
        
        # Get all records
        logger.info(f"📊 Fetching all records from {table_name}...")
        all_records = table.all()
        
        if not all_records:
            logger.info("✅ Table is already empty")
            return True
        
        # Delete all records
        logger.info(f"🗑️  Deleting {len(all_records)} records...")
        record_ids = [record['id'] for record in all_records]
        
        # Airtable allows batch deletion of up to 10 records at a time
        for i in range(0, len(record_ids), 10):
            batch = record_ids[i:i+10]
            table.batch_delete(batch)
            logger.info(f"   Deleted batch {i//10 + 1}/{(len(record_ids)-1)//10 + 1}")
        
        logger.success(f"✅ Successfully cleared {len(all_records)} records from {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset Airtable: {e}")
        return False


if __name__ == "__main__":
    print("""
    🗑️  Airtable Data Reset Utility
    ================================
    This will delete ALL records from your Pokebot Airtable.
    """)
    
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_airtable_data()
    else:
        print("❌ Operation cancelled")