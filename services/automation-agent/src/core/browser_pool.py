#!/usr/bin/env python3
"""
Browser Pool Manager - Manages 20-30 browser instances for distributed monitoring
"""

import asyncio
import random
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import uuid4

from loguru import logger
from src.browsers.agentql_browser import AgentQLBrowser


@dataclass
class BrowserHealth:
    """Track health metrics for each browser instance"""
    browser_id: str
    success_count: int = 0
    failure_count: int = 0
    total_requests: int = 0
    last_used: datetime = None
    last_error: Optional[str] = None
    response_times: deque = None
    score: float = 100.0
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = deque(maxlen=10)
        if self.last_used is None:
            self.last_used = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        """Average response time in seconds"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def update_score(self):
        """Update health score based on metrics"""
        # Base score from success rate (0-70 points)
        success_score = self.success_rate * 70
        
        # Response time score (0-20 points)
        # Under 2s = 20 points, over 10s = 0 points
        if self.avg_response_time <= 2:
            response_score = 20
        elif self.avg_response_time >= 10:
            response_score = 0
        else:
            response_score = 20 * (1 - (self.avg_response_time - 2) / 8)
        
        # Recency score (0-10 points)
        # Used in last 5 min = 10 points
        minutes_since_use = (datetime.now() - self.last_used).total_seconds() / 60
        recency_score = max(0, 10 - minutes_since_use / 30)
        
        self.score = success_score + response_score + recency_score


@dataclass
class BrowserInstance:
    """Represents a single browser in the pool"""
    id: str
    browser: AgentQLBrowser
    profile_name: str
    health: BrowserHealth
    in_use: bool = False
    created_at: datetime = None
    fingerprint: Dict = None
    proxy_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BrowserPool:
    """
    Manages a pool of browser instances for distributed monitoring
    """
    
    def __init__(self, 
                 min_size: int = 20,
                 max_size: int = 30,
                 warmup_interval: int = 600,
                 health_check_interval: int = 300):
        self.min_size = min_size
        self.max_size = max_size
        self.warmup_interval = warmup_interval
        self.health_check_interval = health_check_interval
        
        self.browsers: Dict[str, BrowserInstance] = {}
        self.available_browsers: deque = deque()
        self.in_use_browsers: Set[str] = set()
        
        self.running = False
        self.warmup_task = None
        self.health_check_task = None
        
        logger.info(f"🏊 Browser pool initialized (size: {min_size}-{max_size})")
    
    async def start(self):
        """Start the browser pool and background tasks"""
        self.running = True
        
        # Initialize browsers
        logger.info(f"🚀 Starting browser pool with {self.min_size} instances...")
        await self._initialize_browsers()
        
        # Start background tasks
        self.warmup_task = asyncio.create_task(self._warmup_loop())
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.success(f"✅ Browser pool started with {len(self.browsers)} instances")
    
    async def stop(self):
        """Stop the browser pool and clean up"""
        logger.info("🛑 Stopping browser pool...")
        self.running = False
        
        # Cancel background tasks
        if self.warmup_task:
            self.warmup_task.cancel()
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Close all browsers
        for browser_instance in self.browsers.values():
            try:
                await browser_instance.browser.close()
            except Exception as e:
                logger.error(f"Error closing browser {browser_instance.id}: {e}")
        
        self.browsers.clear()
        self.available_browsers.clear()
        self.in_use_browsers.clear()
        
        logger.info("✅ Browser pool stopped")
    
    async def get_browser(self, priority: str = "normal") -> Optional[BrowserInstance]:
        """
        Get an available browser from the pool
        
        Args:
            priority: "high", "normal", or "low"
            
        Returns:
            BrowserInstance or None if none available
        """
        # Try to get a browser based on health score
        if not self.available_browsers:
            logger.warning("⚠️ No browsers available in pool")
            
            # Try to expand pool if under max size
            if len(self.browsers) < self.max_size:
                await self._add_browser()
            else:
                return None
        
        # Sort available browsers by health score for high priority
        if priority == "high" and len(self.available_browsers) > 1:
            sorted_browsers = sorted(
                [self.browsers[bid] for bid in self.available_browsers],
                key=lambda b: b.health.score,
                reverse=True
            )
            best_browser = sorted_browsers[0]
            self.available_browsers.remove(best_browser.id)
        else:
            # Round-robin for normal priority
            browser_id = self.available_browsers.popleft()
            best_browser = self.browsers[browser_id]
        
        # Mark as in use
        best_browser.in_use = True
        self.in_use_browsers.add(best_browser.id)
        best_browser.health.last_used = datetime.now()
        
        logger.debug(f"🌐 Assigned browser {best_browser.id} (health: {best_browser.health.score:.1f})")
        return best_browser
    
    async def release_browser(self, browser_id: str, success: bool = True, response_time: float = 0):
        """
        Return a browser to the pool and update health metrics
        
        Args:
            browser_id: Browser instance ID
            success: Whether the last operation succeeded
            response_time: Operation response time in seconds
        """
        if browser_id not in self.browsers:
            logger.error(f"Unknown browser ID: {browser_id}")
            return
        
        browser = self.browsers[browser_id]
        
        # Update health metrics
        browser.health.total_requests += 1
        if success:
            browser.health.success_count += 1
        else:
            browser.health.failure_count += 1
        
        if response_time > 0:
            browser.health.response_times.append(response_time)
        
        browser.health.update_score()
        
        # Check if browser needs to be retired
        if browser.health.score < 30 or browser.health.failure_count > 10:
            logger.warning(f"🏥 Retiring unhealthy browser {browser_id} (score: {browser.health.score:.1f})")
            await self._retire_browser(browser_id)
            await self._add_browser()  # Replace with new browser
        else:
            # Return to available pool
            browser.in_use = False
            self.in_use_browsers.discard(browser_id)
            self.available_browsers.append(browser_id)
            
            logger.debug(f"✅ Released browser {browser_id} (health: {browser.health.score:.1f})")
    
    async def _initialize_browsers(self):
        """Initialize the minimum number of browsers"""
        tasks = []
        for i in range(self.min_size):
            tasks.append(self._add_browser(stagger_delay=i * 2))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _add_browser(self, stagger_delay: float = 0) -> Optional[str]:
        """Add a new browser to the pool"""
        if stagger_delay > 0:
            await asyncio.sleep(stagger_delay)
        
        browser_id = str(uuid4())[:8]
        profile_name = f"pool-{browser_id}"
        
        try:
            # Create browser with unique profile
            browser = AgentQLBrowser(profile_name, headless=True)
            await browser.launch()
            
            # Generate unique fingerprint
            fingerprint = self._generate_fingerprint()
            
            # Create browser instance
            instance = BrowserInstance(
                id=browser_id,
                browser=browser,
                profile_name=profile_name,
                health=BrowserHealth(browser_id),
                fingerprint=fingerprint
            )
            
            self.browsers[browser_id] = instance
            self.available_browsers.append(browser_id)
            
            logger.info(f"✅ Added browser {browser_id} to pool (total: {len(self.browsers)})")
            return browser_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add browser: {e}")
            return None
    
    async def _retire_browser(self, browser_id: str):
        """Remove a browser from the pool"""
        if browser_id not in self.browsers:
            return
        
        browser = self.browsers[browser_id]
        
        try:
            await browser.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser {browser_id}: {e}")
        
        # Remove from all collections
        self.browsers.pop(browser_id, None)
        self.in_use_browsers.discard(browser_id)
        
        # Remove from available queue
        temp_queue = deque()
        while self.available_browsers:
            bid = self.available_browsers.popleft()
            if bid != browser_id:
                temp_queue.append(bid)
        self.available_browsers = temp_queue
        
        logger.info(f"🗑️ Retired browser {browser_id} (remaining: {len(self.browsers)})")
    
    async def _warmup_loop(self):
        """Keep browsers warm with periodic activity"""
        while self.running:
            try:
                await asyncio.sleep(self.warmup_interval)
                
                # Warm up idle browsers
                idle_browsers = [
                    b for b in self.browsers.values()
                    if not b.in_use and 
                    (datetime.now() - b.health.last_used).total_seconds() > 300
                ]
                
                for browser in idle_browsers[:5]:  # Warm up to 5 at a time
                    asyncio.create_task(self._warmup_browser(browser))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in warmup loop: {e}")
    
    async def _warmup_browser(self, browser_instance: BrowserInstance):
        """Perform warmup activities on a browser"""
        try:
            browser = browser_instance.browser
            
            # Navigate to a simple page
            await browser.navigate_to("https://www.google.com", wait_until="domcontentloaded")
            
            # Perform some activities
            await asyncio.sleep(random.uniform(2, 5))
            
            # Search for something random
            search_terms = ["electronics", "games", "books", "music", "movies"]
            search_query = random.choice(search_terms)
            
            search_box = await browser.page.query_selector('input[name="q"]')
            if search_box:
                await search_box.type(search_query, delay=random.randint(50, 150))
                await asyncio.sleep(random.uniform(1, 2))
            
            browser_instance.health.last_used = datetime.now()
            logger.debug(f"🔥 Warmed up browser {browser_instance.id}")
            
        except Exception as e:
            logger.error(f"Error warming up browser {browser_instance.id}: {e}")
    
    async def _health_check_loop(self):
        """Periodically check browser health"""
        while self.running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Update health scores
                for browser in self.browsers.values():
                    browser.health.update_score()
                
                # Log pool status
                available = len(self.available_browsers)
                in_use = len(self.in_use_browsers)
                avg_health = sum(b.health.score for b in self.browsers.values()) / len(self.browsers) if self.browsers else 0
                
                logger.info(f"🏊 Pool status - Total: {len(self.browsers)}, Available: {available}, In use: {in_use}, Avg health: {avg_health:.1f}")
                
                # Expand pool if needed
                if available < 3 and len(self.browsers) < self.max_size:
                    await self._add_browser()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    def _generate_fingerprint(self) -> Dict:
        """Generate a unique browser fingerprint"""
        return {
            "user_agent": self._random_user_agent(),
            "viewport": random.choice([
                {"width": 1920, "height": 1080},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
                {"width": 1536, "height": 864}
            ]),
            "timezone": random.choice([
                "America/New_York",
                "America/Chicago", 
                "America/Denver",
                "America/Los_Angeles"
            ]),
            "locale": "en-US",
            "hardware_concurrency": random.choice([4, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16]),
            "color_depth": 24,
            "canvas_noise": random.random()
        }
    
    def _random_user_agent(self) -> str:
        """Generate a random user agent"""
        chrome_versions = ["120.0.6099.130", "121.0.6167.85", "122.0.6261.94"]
        firefox_versions = ["121.0", "122.0", "123.0"]
        
        if random.random() < 0.7:  # 70% Chrome
            version = random.choice(chrome_versions)
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        else:  # 30% Firefox
            version = random.choice(firefox_versions)
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{version}) Gecko/20100101 Firefox/{version}"


# Example usage
if __name__ == "__main__":
    async def test_pool():
        pool = BrowserPool(min_size=5, max_size=10)
        await pool.start()
        
        # Get browsers
        browser1 = await pool.get_browser(priority="high")
        if browser1:
            logger.info(f"Got browser: {browser1.id}")
            await asyncio.sleep(5)
            await pool.release_browser(browser1.id, success=True, response_time=2.5)
        
        await asyncio.sleep(10)
        await pool.stop()
    
    asyncio.run(test_pool())