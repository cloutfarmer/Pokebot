#!/usr/bin/env python3
"""
Proxy Manager - Handles multiple proxy providers with intelligent rotation
"""

import asyncio
import json
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp
from loguru import logger


class ProxyTier(Enum):
    """Proxy quality tiers"""
    DIRECT = "direct"              # No proxy (home IP)
    DATACENTER = "datacenter"      # Basic datacenter proxies
    RESIDENTIAL = "residential"    # Residential IPs
    PREMIUM = "premium"            # Premium residential
    MOBILE = "mobile"              # Mobile 4G/5G


@dataclass
class ProxyInfo:
    """Information about a proxy"""
    id: str
    provider: str
    tier: ProxyTier
    endpoint: str  # host:port or full URL
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "US"
    state: Optional[str] = None
    city: Optional[str] = None
    asn: Optional[str] = None
    last_used: datetime = field(default_factory=datetime.now)
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = True
    sticky_session_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0
    
    @property
    def health_score(self) -> float:
        """Calculate proxy health score (0-100)"""
        # Base score from success rate
        base_score = self.success_rate * 80
        
        # Penalty for high failure count
        failure_penalty = min(self.failure_count * 2, 20)
        
        # Bonus for recent usage
        hours_since_use = (datetime.now() - self.last_used).total_seconds() / 3600
        recency_bonus = max(0, 20 - hours_since_use)
        
        return max(0, base_score - failure_penalty + recency_bonus)
    
    def to_playwright_proxy(self) -> Dict:
        """Convert to Playwright proxy format"""
        proxy_config = {
            "server": f"http://{self.endpoint}"
        }
        
        if self.username and self.password:
            proxy_config["username"] = self.username
            proxy_config["password"] = self.password
        
        return proxy_config


class ProxyProvider(ABC):
    """Abstract base class for proxy providers"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider"""
        pass
    
    @abstractmethod
    async def get_proxies(self, count: int = 10) -> List[ProxyInfo]:
        """Get a list of available proxies"""
        pass
    
    @abstractmethod
    async def report_failure(self, proxy: ProxyInfo, error: str):
        """Report a proxy failure"""
        pass
    
    @abstractmethod
    async def refresh_session(self, proxy: ProxyInfo) -> bool:
        """Refresh proxy session if supported"""
        pass


class PacketStreamProvider(ProxyProvider):
    """PacketStream residential proxy provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.endpoints = []
    
    async def initialize(self) -> bool:
        """Initialize PacketStream connection"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Get available endpoints (mock implementation)
            self.endpoints = [
                f"residential-{i:03d}.packetstream.io:31111"
                for i in range(1, 21)  # 20 endpoints
            ]
            
            logger.info(f"✅ PacketStream initialized with {len(self.endpoints)} endpoints")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PacketStream: {e}")
            return False
    
    async def get_proxies(self, count: int = 10) -> List[ProxyInfo]:
        """Get PacketStream proxies"""
        proxies = []
        
        for i, endpoint in enumerate(random.sample(self.endpoints, min(count, len(self.endpoints)))):
            proxy = ProxyInfo(
                id=f"ps_{i:03d}",
                provider="packetstream",
                tier=ProxyTier.RESIDENTIAL,
                endpoint=endpoint,
                username=f"user_{self.api_key}",
                password=self.api_key,
                country="US",
                state=random.choice(["CA", "TX", "NY", "FL", "IL"])
            )
            proxies.append(proxy)
        
        return proxies
    
    async def report_failure(self, proxy: ProxyInfo, error: str):
        """Report PacketStream proxy failure"""
        logger.warning(f"⚠️ PacketStream proxy {proxy.id} failed: {error}")
        # Could implement API call to report bad IP
    
    async def refresh_session(self, proxy: ProxyInfo) -> bool:
        """PacketStream supports session refresh"""
        # Make API call to rotate IP
        return True


class BrightDataProvider(ProxyProvider):
    """Bright Data premium residential provider"""
    
    def __init__(self, username: str, password: str, zone: str = "residential"):
        self.username = username
        self.password = password
        self.zone = zone
        self.endpoints = []
    
    async def initialize(self) -> bool:
        """Initialize Bright Data"""
        try:
            # Bright Data provides sticky sessions through different ports
            self.endpoints = [
                f"zproxy.lum-superproxy.io:{24000 + i}"
                for i in range(50)  # 50 session endpoints
            ]
            
            logger.info(f"✅ Bright Data initialized with {len(self.endpoints)} endpoints")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bright Data: {e}")
            return False
    
    async def get_proxies(self, count: int = 10) -> List[ProxyInfo]:
        """Get Bright Data proxies"""
        proxies = []
        
        for i, endpoint in enumerate(random.sample(self.endpoints, min(count, len(self.endpoints)))):
            # Bright Data uses session IDs for sticky sessions
            session_id = f"session_{random.randint(1000, 9999)}"
            
            proxy = ProxyInfo(
                id=f"bd_{i:03d}",
                provider="brightdata",
                tier=ProxyTier.PREMIUM,
                endpoint=endpoint,
                username=f"{self.username}-session-{session_id}",
                password=self.password,
                country="US"
            )
            proxies.append(proxy)
        
        return proxies
    
    async def report_failure(self, proxy: ProxyInfo, error: str):
        """Report Bright Data failure"""
        logger.warning(f"⚠️ Bright Data proxy {proxy.id} failed: {error}")
    
    async def refresh_session(self, proxy: ProxyInfo) -> bool:
        """Refresh by changing session ID"""
        new_session = f"session_{random.randint(1000, 9999)}"
        proxy.username = proxy.username.replace(
            proxy.username.split('-session-')[1],
            new_session
        )
        return True


class SoaxMobileProvider(ProxyProvider):
    """Soax mobile proxy provider"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.endpoints = []
    
    async def initialize(self) -> bool:
        """Initialize Soax mobile"""
        try:
            # Mobile proxy endpoints
            self.endpoints = [
                f"mobile-{i:02d}.soax.com:8080"
                for i in range(1, 11)  # 10 mobile endpoints
            ]
            
            logger.info(f"✅ Soax mobile initialized with {len(self.endpoints)} endpoints")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Soax: {e}")
            return False
    
    async def get_proxies(self, count: int = 5) -> List[ProxyInfo]:
        """Get Soax mobile proxies"""
        proxies = []
        
        for i, endpoint in enumerate(self.endpoints[:count]):
            proxy = ProxyInfo(
                id=f"soax_{i:02d}",
                provider="soax",
                tier=ProxyTier.MOBILE,
                endpoint=endpoint,
                username=self.username,
                password=self.password,
                country="US"
            )
            proxies.append(proxy)
        
        return proxies
    
    async def report_failure(self, proxy: ProxyInfo, error: str):
        """Report Soax failure"""
        logger.warning(f"⚠️ Soax mobile proxy {proxy.id} failed: {error}")
    
    async def refresh_session(self, proxy: ProxyInfo) -> bool:
        """Mobile proxies auto-rotate"""
        return True


class ProxyManager:
    """
    Manages multiple proxy providers with intelligent rotation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.providers: Dict[str, ProxyProvider] = {}
        self.proxy_pool: List[ProxyInfo] = []
        self.browser_proxy_map: Dict[str, str] = {}  # browser_id -> proxy_id
        self.geographic_distribution: Dict[str, int] = {}
        
        self.config = self._load_config(config_path)
        self.running = False
        self.refresh_task = None
        
        logger.info("🌐 Proxy manager initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load proxy configuration"""
        default_config = {
            "providers": {
                "packetstream": {"enabled": False, "allocation": 40},
                "brightdata": {"enabled": False, "allocation": 30},
                "soax": {"enabled": False, "allocation": 15},
                "direct": {"enabled": True, "allocation": 15}
            },
            "geographic_distribution": {
                "preferred_states": ["CA", "TX", "NY", "FL", "IL", "PA", "OH"],
                "max_per_state": 5
            },
            "session_settings": {
                "sticky_duration_minutes": 30,
                "refresh_interval_minutes": 60,
                "max_failures_before_blacklist": 5
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load proxy config: {e}")
        
        return default_config
    
    async def start(self):
        """Start the proxy manager"""
        self.running = True
        
        # Initialize providers
        await self._initialize_providers()
        
        # Load initial proxy pool
        await self._refresh_proxy_pool()
        
        # Start background refresh task
        self.refresh_task = asyncio.create_task(self._refresh_loop())
        
        logger.success(f"✅ Proxy manager started with {len(self.proxy_pool)} proxies")
    
    async def stop(self):
        """Stop the proxy manager"""
        logger.info("🛑 Stopping proxy manager...")
        self.running = False
        
        if self.refresh_task:
            self.refresh_task.cancel()
        
        # Close provider sessions
        for provider in self.providers.values():
            if hasattr(provider, 'session') and provider.session:
                await provider.session.close()
        
        logger.info("✅ Proxy manager stopped")
    
    async def _initialize_providers(self):
        """Initialize all enabled proxy providers"""
        config = self.config["providers"]
        
        # PacketStream
        if config["packetstream"]["enabled"]:
            api_key = os.getenv("PACKETSTREAM_API_KEY")
            if api_key:
                provider = PacketStreamProvider(api_key)
                if await provider.initialize():
                    self.providers["packetstream"] = provider
        
        # Bright Data
        if config["brightdata"]["enabled"]:
            username = os.getenv("BRIGHTDATA_USERNAME")
            password = os.getenv("BRIGHTDATA_PASSWORD")
            if username and password:
                provider = BrightDataProvider(username, password)
                if await provider.initialize():
                    self.providers["brightdata"] = provider
        
        # Soax Mobile
        if config["soax"]["enabled"]:
            username = os.getenv("SOAX_USERNAME")
            password = os.getenv("SOAX_PASSWORD")
            if username and password:
                provider = SoaxMobileProvider(username, password)
                if await provider.initialize():
                    self.providers["soax"] = provider
        
        logger.info(f"✅ Initialized {len(self.providers)} proxy providers")
    
    async def _refresh_proxy_pool(self):
        """Refresh the proxy pool from all providers"""
        new_pool = []
        
        # Get proxies from each provider based on allocation
        for provider_name, provider in self.providers.items():
            allocation = self.config["providers"][provider_name]["allocation"]
            count = max(1, allocation // 5)  # Rough allocation to count
            
            try:
                proxies = await provider.get_proxies(count)
                new_pool.extend(proxies)
                logger.debug(f"Got {len(proxies)} proxies from {provider_name}")
            except Exception as e:
                logger.error(f"Failed to get proxies from {provider_name}: {e}")
        
        # Add direct connections
        direct_count = self.config["providers"]["direct"]["allocation"] // 5
        for i in range(direct_count):
            direct_proxy = ProxyInfo(
                id=f"direct_{i:02d}",
                provider="direct",
                tier=ProxyTier.DIRECT,
                endpoint="",  # No proxy
                country="US"
            )
            new_pool.append(direct_proxy)
        
        # Filter out blacklisted proxies and update pool
        active_proxies = [p for p in new_pool if p.is_active and p.health_score > 20]
        self.proxy_pool = active_proxies
        
        logger.info(f"🔄 Refreshed proxy pool: {len(self.proxy_pool)} active proxies")
    
    async def get_proxy_for_browser(self, browser_id: str, tier: ProxyTier = ProxyTier.RESIDENTIAL) -> Optional[ProxyInfo]:
        """
        Get a proxy for a specific browser
        
        Args:
            browser_id: Browser instance ID
            tier: Preferred proxy tier
            
        Returns:
            ProxyInfo or None
        """
        # Check if browser already has a sticky proxy
        if browser_id in self.browser_proxy_map:
            proxy_id = self.browser_proxy_map[browser_id]
            proxy = next((p for p in self.proxy_pool if p.id == proxy_id), None)
            
            if proxy and proxy.sticky_session_until and datetime.now() < proxy.sticky_session_until:
                logger.debug(f"🔗 Using sticky proxy {proxy_id} for browser {browser_id}")
                return proxy
            else:
                # Session expired, remove mapping
                self.browser_proxy_map.pop(browser_id, None)
        
        # Find suitable proxy
        suitable_proxies = [
            p for p in self.proxy_pool
            if p.tier == tier and p.is_active and p.health_score > 50
        ]
        
        # Fallback to any tier if preferred not available
        if not suitable_proxies:
            suitable_proxies = [
                p for p in self.proxy_pool
                if p.is_active and p.health_score > 30
            ]
        
        if not suitable_proxies:
            logger.warning(f"⚠️ No suitable proxies available for tier {tier}")
            return None
        
        # Select proxy with geographic distribution
        proxy = self._select_proxy_with_distribution(suitable_proxies)
        
        # Set up sticky session
        sticky_duration = self.config["session_settings"]["sticky_duration_minutes"]
        proxy.sticky_session_until = datetime.now() + timedelta(minutes=sticky_duration)
        
        # Map browser to proxy
        self.browser_proxy_map[browser_id] = proxy.id
        proxy.last_used = datetime.now()
        
        logger.info(f"🌐 Assigned {proxy.tier.value} proxy {proxy.id} to browser {browser_id}")
        return proxy
    
    def _select_proxy_with_distribution(self, proxies: List[ProxyInfo]) -> ProxyInfo:
        """Select proxy ensuring geographic distribution"""
        # Count current state distribution
        state_counts = {}
        for browser_id, proxy_id in self.browser_proxy_map.items():
            proxy = next((p for p in self.proxy_pool if p.id == proxy_id), None)
            if proxy and proxy.state:
                state_counts[proxy.state] = state_counts.get(proxy.state, 0) + 1
        
        # Prefer proxies from underrepresented states
        max_per_state = self.config["geographic_distribution"]["max_per_state"]
        
        for proxy in sorted(proxies, key=lambda p: p.health_score, reverse=True):
            if not proxy.state or state_counts.get(proxy.state, 0) < max_per_state:
                return proxy
        
        # Fallback to best proxy if all states are saturated
        return max(proxies, key=lambda p: p.health_score)
    
    async def report_proxy_result(self, browser_id: str, success: bool, error: str = ""):
        """Report proxy usage result"""
        if browser_id not in self.browser_proxy_map:
            return
        
        proxy_id = self.browser_proxy_map[browser_id]
        proxy = next((p for p in self.proxy_pool if p.id == proxy_id), None)
        
        if not proxy:
            return
        
        # Update proxy metrics
        if success:
            proxy.success_count += 1
        else:
            proxy.failure_count += 1
            
            # Report to provider
            if proxy.provider in self.providers:
                await self.providers[proxy.provider].report_failure(proxy, error)
            
            # Blacklist if too many failures
            max_failures = self.config["session_settings"]["max_failures_before_blacklist"]
            if proxy.failure_count >= max_failures:
                proxy.is_active = False
                logger.warning(f"🚫 Blacklisted proxy {proxy_id} after {proxy.failure_count} failures")
                
                # Remove browser mapping
                self.browser_proxy_map.pop(browser_id, None)
    
    async def _refresh_loop(self):
        """Background task to refresh proxy pool"""
        while self.running:
            try:
                refresh_interval = self.config["session_settings"]["refresh_interval_minutes"] * 60
                await asyncio.sleep(refresh_interval)
                
                await self._refresh_proxy_pool()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in proxy refresh loop: {e}")
    
    def get_pool_status(self) -> Dict:
        """Get proxy pool status"""
        status = {
            "total_proxies": len(self.proxy_pool),
            "active_proxies": len([p for p in self.proxy_pool if p.is_active]),
            "by_tier": {},
            "by_provider": {},
            "avg_health": 0
        }
        
        if self.proxy_pool:
            for proxy in self.proxy_pool:
                # By tier
                tier = proxy.tier.value
                if tier not in status["by_tier"]:
                    status["by_tier"][tier] = 0
                status["by_tier"][tier] += 1
                
                # By provider
                if proxy.provider not in status["by_provider"]:
                    status["by_provider"][proxy.provider] = 0
                status["by_provider"][proxy.provider] += 1
            
            # Average health
            status["avg_health"] = sum(p.health_score for p in self.proxy_pool) / len(self.proxy_pool)
        
        return status


# Example usage
if __name__ == "__main__":
    async def test_proxy_manager():
        # Set environment variables for testing
        os.environ["PACKETSTREAM_API_KEY"] = "test_key"
        
        manager = ProxyManager()
        await manager.start()
        
        # Get a proxy for a browser
        proxy = await manager.get_proxy_for_browser("browser_001", ProxyTier.RESIDENTIAL)
        if proxy:
            logger.info(f"Got proxy: {proxy.id} ({proxy.tier.value})")
            
            # Simulate usage
            await manager.report_proxy_result("browser_001", success=True)
        
        # Print status
        status = manager.get_pool_status()
        logger.info(f"Pool status: {json.dumps(status, indent=2)}")
        
        await manager.stop()
    
    asyncio.run(test_proxy_manager())