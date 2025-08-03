#!/usr/bin/env python3
"""
Airtable integration for tracking Pokemon card stock availability
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pyairtable import Api, Table, Base
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class AirtableTracker:
    """
    Tracks Pokemon card stock status in Airtable
    """
    
    def __init__(self):
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME", "Pokebot")
        
        if not self.api_key or not self.base_id:
            logger.warning("⚠️ Airtable credentials not configured, logging disabled")
            self.enabled = False
            return
            
        try:
            self.api = Api(self.api_key)
            self.base = self.api.base(self.base_id)
            
            # Check if table exists, create if it doesn't
            if not self._table_exists():
                logger.info(f"📝 Table '{self.table_name}' not found, creating with schema...")
                self._create_table_schema()
            
            self.table = self.api.table(self.base_id, self.table_name)
            self.enabled = True
            logger.success(f"✅ Airtable tracker initialized for table: {self.table_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Airtable: {e}")
            logger.error(f"   Make sure your Personal Access Token has 'schema.bases:write' permissions")
            self.enabled = False
    
    def log_stock_check(self, sku: str, product_name: str, is_available: bool, 
                       price: Optional[float] = None, url: Optional[str] = None) -> bool:
        """
        Log a stock check to Airtable
        
        Args:
            sku: Product SKU
            product_name: Product name
            is_available: Whether product is in stock
            price: Current price if available
            url: Product URL
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False
            
        try:
            # Check if product exists
            existing = self._get_product_record(sku)
            
            timestamp = datetime.now().isoformat()
            status = "In Stock" if is_available else "Out of Stock"
            
            if existing:
                # Update existing record
                record_id = existing['id']
                previous_status = existing['fields'].get('Current Status', 'Unknown')
                
                # Track status changes
                status_changed = previous_status != status
                status_changed_at = timestamp if status_changed else existing['fields'].get('Status Changed At')
                
                # Update check count
                check_count = existing['fields'].get('Check Count', 0) + 1
                
                # Calculate availability duration if went OOS
                availability_duration = None
                if status_changed and not is_available and previous_status == "In Stock":
                    # Product went out of stock
                    in_stock_since = existing['fields'].get('Status Changed At')
                    if in_stock_since:
                        try:
                            start = datetime.fromisoformat(in_stock_since)
                            end = datetime.fromisoformat(timestamp)
                            availability_duration = (end - start).total_seconds() / 60  # minutes
                        except:
                            pass
                
                update_fields = {
                    'Current Status': status,
                    'Last Checked': timestamp,
                    'Check Count': check_count,
                    'Status Changed At': status_changed_at,
                }
                
                if price is not None:
                    update_fields['Current Price'] = price
                    # Track price history
                    price_history = existing['fields'].get('Price History', '')
                    price_history += f"\n{timestamp}: ${price}"
                    update_fields['Price History'] = price_history[-1000:]  # Keep last 1000 chars
                
                if availability_duration:
                    update_fields['Last Availability Duration (min)'] = availability_duration
                
                self.table.update(record_id, update_fields)
                
                if status_changed:
                    logger.info(f"📊 Airtable: {product_name} status changed to {status}")
                
            else:
                # Create new record
                fields = {
                    'SKU': sku,
                    'Product Name': product_name,
                    'Current Status': status,
                    'Last Checked': timestamp,
                    'Status Changed At': timestamp,
                    'Check Count': 1,
                    'Alert Sent': False,
                }
                
                if price is not None:
                    fields['Current Price'] = price
                    fields['Price History'] = f"{timestamp}: ${price}"
                
                if url:
                    fields['Product URL'] = url
                
                self.table.create(fields)
                logger.info(f"📊 Airtable: Created new record for {product_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Airtable logging error: {e}")
            return False
    
    def _get_product_record(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get existing product record by SKU"""
        try:
            records = self.table.all(formula=f"{{SKU}}='{sku}'")
            return records[0] if records else None
        except Exception:
            return None
    
    def update_product_status(self, sku: str, status: str, price: Optional[float] = None) -> bool:
        """
        Quick method to update product status
        
        Args:
            sku: Product SKU
            status: New status
            price: Current price if available
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False
            
        try:
            existing = self._get_product_record(sku)
            if not existing:
                logger.warning(f"⚠️ Product {sku} not found in Airtable")
                return False
                
            update_fields = {
                'Current Status': status,
                'Last Checked': datetime.now().isoformat()
            }
            
            if price is not None:
                update_fields['Current Price'] = price
                
            self.table.update(existing['id'], update_fields)
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update product status: {e}")
            return False
    
    def get_product_history(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get product tracking history
        
        Args:
            sku: Product SKU
            
        Returns:
            Product record with history
        """
        if not self.enabled:
            return None
            
        try:
            record = self._get_product_record(sku)
            return record['fields'] if record else None
        except Exception as e:
            logger.error(f"❌ Failed to get product history: {e}")
            return None
    
    def get_available_products(self) -> List[Dict[str, Any]]:
        """Get all currently available products"""
        if not self.enabled:
            return []
            
        try:
            records = self.table.all(formula="{Current Status}='In Stock'")
            return [r['fields'] for r in records]
        except Exception:
            return []
    
    def mark_alert_sent(self, sku: str) -> bool:
        """Mark that an alert was sent for this product"""
        if not self.enabled:
            return False
            
        try:
            existing = self._get_product_record(sku)
            if existing:
                self.table.update(existing['id'], {'Alert Sent': True})
                return True
            return False
        except Exception:
            return False
    
    def _table_exists(self) -> bool:
        """Check if the table exists in the base"""
        try:
            tables = self.base.schema().tables
            return any(table.name == self.table_name for table in tables)
        except Exception as e:
            logger.warning(f"⚠️ Could not check if table exists: {e}")
            return True  # Assume it exists to avoid creating duplicates
    
    def _create_table_schema(self) -> bool:
        """Create the Pokemon stock tracking table with proper schema"""
        try:
            fields = [
                {
                    "name": "SKU",
                    "type": "singleLineText",
                    "description": "Product SKU identifier"
                },
                {
                    "name": "Product Name",
                    "type": "singleLineText",
                    "description": "Full product name"
                },
                {
                    "name": "Current Status",
                    "type": "singleSelect",
                    "options": {
                        "choices": [
                            {"name": "In Stock", "color": "greenBright"},
                            {"name": "Out of Stock", "color": "redBright"}
                        ]
                    },
                    "description": "Current availability status"
                },
                {
                    "name": "Last Checked",
                    "type": "dateTime",
                    "options": {
                        "dateFormat": {"name": "iso"},
                        "timeFormat": {"name": "24hour"},
                        "timeZone": "utc"
                    },
                    "description": "Timestamp of last availability check"
                },
                {
                    "name": "Status Changed At",
                    "type": "dateTime",
                    "options": {
                        "dateFormat": {"name": "iso"},
                        "timeFormat": {"name": "24hour"},
                        "timeZone": "utc"
                    },
                    "description": "When the status last changed"
                },
                {
                    "name": "Check Count",
                    "type": "number",
                    "options": {
                        "precision": 0
                    },
                    "description": "Total number of availability checks"
                },
                {
                    "name": "Current Price",
                    "type": "currency",
                    "options": {
                        "precision": 2,
                        "symbol": "$"
                    },
                    "description": "Current product price"
                },
                {
                    "name": "Price History",
                    "type": "multilineText",
                    "description": "Historical price changes with timestamps"
                },
                {
                    "name": "Product URL",
                    "type": "url",
                    "description": "Direct link to product page"
                },
                {
                    "name": "Alert Sent",
                    "type": "checkbox",
                    "options": {
                        "icon": "check",
                        "color": "greenBright"
                    },
                    "description": "Whether alert notification was sent"
                },
                {
                    "name": "Last Availability Duration (min)",
                    "type": "number",
                    "options": {
                        "precision": 1
                    },
                    "description": "How long product was available (in minutes)"
                }
            ]
            
            created_table = self.base.create_table(
                name=self.table_name,
                fields=fields,
                description="Pokemon card stock availability tracking with historical data and analytics"
            )
            logger.success(f"✅ Created table '{self.table_name}' with {len(fields)} fields")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create table schema: {e}")
            logger.error(f"   Ensure your Personal Access Token has 'schema.bases:write' scope")
            return False