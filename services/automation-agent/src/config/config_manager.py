"""
Configuration management for retail automation
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger
from pydantic import BaseModel, Field


class SKUConfig(BaseModel):
    """Configuration for a specific SKU to monitor."""
    sku: str
    name: str
    max_price: float
    quantity: int = 1
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")


class AuthConfig(BaseModel):
    """Authentication configuration for a retailer."""
    email: str
    password: str
    payment_method: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    shipping_address: Optional[Dict[str, Any]] = None
    # Google OAuth configuration
    use_google_signin: bool = False
    google_email: Optional[str] = None
    google_password: Optional[str] = None
    google_backup_codes: Optional[List[str]] = None


class RetailerLimits(BaseModel):
    """Purchase limits and constraints for a retailer."""
    max_quantity: int = 2
    max_price: float = 100.0
    cooldown_seconds: int = 30


class RetailerConfig(BaseModel):
    """Complete configuration for a retailer."""
    enabled: bool = True
    skus: List[SKUConfig] = []
    authentication: Optional[AuthConfig] = None
    limits: RetailerLimits = RetailerLimits()


class ConfigManager:
    """Manages configuration for all retailers and automation settings."""
    
    def __init__(self) -> None:
        self.base_dir = Path(__file__).parent.parent.parent
        self.retailer_configs_dir = self.base_dir / "retailer_configs"
        self.auth_configs_dir = self.base_dir / "auth_configs"
        self.retailer_configs: Dict[str, RetailerConfig] = {}
        
        # Ensure config directories exist
        self.retailer_configs_dir.mkdir(exist_ok=True)
        self.auth_configs_dir.mkdir(exist_ok=True)
    
    async def load_configurations(self) -> None:
        """Load all retailer configurations."""
        logger.info("📁 Loading retailer configurations...")
        
        # Load configurations for supported retailers
        retailers = ["bestbuy", "target", "walmart", "pokemoncenter", "costco"]
        
        for retailer in retailers:
            try:
                await self._load_retailer_config(retailer)
            except Exception as e:
                logger.warning(f"⚠️  Failed to load {retailer} config: {e}")
        
        enabled_count = sum(1 for config in self.retailer_configs.values() if config.enabled)
        logger.success(f"✅ Loaded {len(self.retailer_configs)} configs, {enabled_count} enabled")
    
    async def _load_retailer_config(self, retailer: str) -> None:
        """Load configuration for a specific retailer."""
        config_file = self.retailer_configs_dir / f"{retailer}.json"
        auth_file = self.auth_configs_dir / f"{retailer}.json"
        
        # Create default config if it doesn't exist
        if not config_file.exists():
            await self._create_default_config(retailer, config_file)
        
        # Create default auth if it doesn't exist
        if not auth_file.exists():
            await self._create_default_auth(retailer, auth_file)
        
        # Load config data
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Load auth data
        auth_data = None
        if auth_file.exists():
            with open(auth_file, 'r') as f:
                auth_data = json.load(f)
        
        # Combine config and auth
        if auth_data:
            config_data["authentication"] = auth_data
        
        # Create retailer config object
        self.retailer_configs[retailer] = RetailerConfig(**config_data)
        logger.debug(f"📋 Loaded configuration for {retailer}")
    
    async def _create_default_config(self, retailer: str, config_file: Path) -> None:
        """Create a default configuration file for a retailer."""
        default_skus = {
            "bestbuy": [
                {
                    "sku": "6418599",
                    "name": "Pokemon Scarlet & Violet Elite Trainer Box",
                    "max_price": 49.99,
                    "quantity": 1,
                    "priority": "high"
                }
            ],
            "target": [
                {
                    "sku": "086-01-4568",
                    "name": "Pokemon Scarlet & Violet Booster Pack",
                    "max_price": 4.99,
                    "quantity": 10,
                    "priority": "medium"
                }
            ]
        }
        
        default_config = {
            "enabled": True,
            "skus": default_skus.get(retailer, []),
            "limits": {
                "max_quantity": 2,
                "max_price": 100.0,
                "cooldown_seconds": 30
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"📄 Created default configuration for {retailer}")
    
    async def _create_default_auth(self, retailer: str, auth_file: Path) -> None:
        """Create a template authentication file for a retailer."""
        default_auth = {
            "email": "your_email@example.com",
            "password": "your_password",
            "payment_method": "ending_in_1234",
            "billing_address": {
                "first_name": "John",
                "last_name": "Doe",
                "address1": "123 Main St",
                "city": "Anytown",
                "state": "NY",
                "zip": "12345",
                "phone": "555-123-4567"
            },
            "use_google_signin": False,
            "google_email": "your_google_email@gmail.com",
            "google_password": "your_google_password",
            "google_backup_codes": [
                "12345678",
                "87654321"
            ]
        }
        
        with open(auth_file, 'w') as f:
            json.dump(default_auth, f, indent=2)
        
        logger.warning(f"⚠️  Created template auth file for {retailer} - UPDATE WITH REAL CREDENTIALS!")
    
    def get_retailer_config(self, retailer: str) -> Optional[RetailerConfig]:
        """Get configuration for a specific retailer."""
        return self.retailer_configs.get(retailer)
    
    def is_retailer_enabled(self, retailer: str) -> bool:
        """Check if a retailer is enabled for monitoring."""
        config = self.retailer_configs.get(retailer)
        return config.enabled if config else False
    
    def get_enabled_retailers(self) -> List[str]:
        """Get list of all enabled retailers."""
        return [
            name for name, config in self.retailer_configs.items() 
            if config.enabled
        ]
    
    def get_high_priority_skus(self, retailer: str) -> List[SKUConfig]:
        """Get all high priority SKUs for a retailer."""
        config = self.get_retailer_config(retailer)
        if not config:
            return []
        
        return [sku for sku in config.skus if sku.priority == "high"]