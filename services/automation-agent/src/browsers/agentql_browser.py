"""
AgentQL-powered browser automation with stealth features
"""

import asyncio
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

import agentql
from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class AgentQLBrowser:
    """
    Browser automation using AgentQL for intelligent element detection
    and Playwright for browser control with anti-detection features.
    """
    
    def __init__(self, profile_id: str, headless: bool = True) -> None:
        self.profile_id = profile_id
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Anti-detection settings
        self.user_agent = UserAgent()
        self.profile_dir = Path(__file__).parent.parent.parent / "browser-profiles" / profile_id
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # AgentQL session
        self.agentql_session: Optional[agentql.Session] = None
    
    async def launch(self, proxy: Optional[str] = None) -> None:
        """Launch browser with stealth configuration."""
        logger.info(f"🚀 Launching browser profile: {self.profile_id}")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Browser launch options with anti-detection
            launch_options = {
                "headless": self.headless,
                "args": self._get_chrome_args(),
            }
            
            # Add proxy if provided
            if proxy:
                launch_options["proxy"] = {"server": proxy}
            
            # Launch Chromium with stealth features
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Create context with anti-detection settings
            context_options = await self._get_context_options()
            self.context = await self.browser.new_context(**context_options)
            
            # Configure context for stealth
            await self._configure_stealth_context()
            
            # Create page
            self.page = await self.context.new_page()
            
            # Initialize AgentQL session
            await self._initialize_agentql()
            
            logger.success(f"✅ Browser launched successfully: {self.profile_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to launch browser: {e}")
            await self.close()
            raise
    
    def _get_chrome_args(self) -> List[str]:
        """Get Chrome arguments for anti-detection."""
        return [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--hide-scrollbars",
            "--metrics-recording-only",
            "--mute-audio",
            "--no-default-browser-check",
            "--no-pings",
            "--password-store=basic",
            "--use-mock-keychain",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--enable-features=NetworkService,NetworkServiceLogging",
            "--force-color-profile=srgb",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-crash-reporter",
            "--disable-oopr-debug-crash-dump",
            "--no-crash-upload",
            "--disable-low-res-tiling",
        ]
    
    async def _get_context_options(self) -> Dict[str, Any]:
        """Get browser context options with randomized fingerprint."""
        # Random viewport sizes (common resolutions)
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
            {"width": 1280, "height": 720},
        ]
        
        viewport = random.choice(viewports)
        user_agent_string = self.user_agent.random
        
        return {
            "viewport": viewport,
            "user_agent": user_agent_string,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation"],
            "extra_http_headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
        }
    
    async def _configure_stealth_context(self) -> None:
        """Configure additional stealth measures."""
        if not self.context:
            return
        
        # Remove webdriver property and other automation indicators
        await self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000 - Math.random() * 10,
                        connectionInfo: 'h2',
                        finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 5,
                        finishLoadTime: Date.now() / 1000 - Math.random() * 3,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000 - Math.random() * 8,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'h2',
                        requestTime: Date.now() / 1000 - Math.random() * 15,
                        startLoadTime: Date.now() / 1000 - Math.random() * 12,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: true,
                        wasNpnNegotiated: true
                    };
                },
                csi: function() {
                    return {
                        onloadT: Date.now(),
                        startE: Date.now() - Math.random() * 1000,
                        tran: 15
                    };
                }
            };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
    
    async def _initialize_agentql(self) -> None:
        """Initialize AgentQL session for intelligent element detection."""
        if not self.page:
            raise RuntimeError("Page not available for AgentQL initialization")
        
        try:
            # Get AgentQL API key from environment
            api_key = os.getenv("AGENTQL_API_KEY")
            if not api_key:
                logger.warning("⚠️  No AgentQL API key found, using basic selectors")
                return
            
            # Configure AgentQL with API key
            agentql.configure(api_key=api_key)
            
            # Wrap the page with AgentQL
            self.agentql_session = await agentql.wrap_async(self.page)
            logger.success("🧠 AgentQL session initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  AgentQL initialization failed: {e}")
            # Continue without AgentQL - fallback to standard selectors
            self.agentql_session = None
    
    async def smart_find(self, description: str, fallback_selector: str = "") -> Optional[Any]:
        """
        Use AgentQL to intelligently find elements, with fallback to CSS selectors.
        
        Args:
            description: Natural language description of the element
            fallback_selector: CSS selector to use if AgentQL fails
        
        Returns:
            Element if found, None otherwise
        """
        if not self.page:
            raise RuntimeError("Page not available")
        
        # Try AgentQL first
        if self.agentql_session:
            try:
                # Use AgentQL's get_by_prompt method for natural language queries
                element = await self.agentql_session.get_by_prompt(description)
                if element:
                    logger.debug(f"🧠 AgentQL found: {description}")
                    return element
            except Exception as e:
                logger.debug(f"AgentQL query failed: {e}")
                
                # Try query_elements as backup
                try:
                    elements = await self.agentql_session.query_elements(description)
                    if elements:
                        logger.debug(f"🧠 AgentQL found via query_elements: {description}")
                        return elements[0] if isinstance(elements, list) else elements
                except Exception as e2:
                    logger.debug(f"AgentQL query_elements also failed: {e2}")
        
        # Fallback to CSS selector
        if fallback_selector:
            try:
                element = await self.page.query_selector(fallback_selector)
                if element:
                    logger.debug(f"🎯 CSS selector found: {fallback_selector}")
                    return element
            except Exception as e:
                logger.debug(f"CSS selector failed: {e}")
        
        logger.debug(f"❌ Element not found: {description}")
        return None
    
    async def human_click(
        self, 
        element_description: str, 
        fallback_selector: str = "",
        delay_range: tuple = (100, 300)
    ) -> bool:
        """
        Click an element with human-like behavior.
        
        Args:
            element_description: Natural language description for AgentQL
            fallback_selector: CSS selector fallback
            delay_range: Random delay range in milliseconds
        
        Returns:
            True if click was successful, False otherwise
        """
        element = await self.smart_find(element_description, fallback_selector)
        if not element:
            return False
        
        try:
            # Random delay before action
            await self.random_delay(delay_range[0], delay_range[1])
            
            # Human-like click with slight offset
            box = await element.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2 + random.randint(-5, 5)
                y = box["y"] + box["height"] / 2 + random.randint(-5, 5)
                
                await self.page.mouse.move(x, y)
                await self.random_delay(50, 150)
                await self.page.mouse.click(x, y)
                
                logger.debug(f"✅ Clicked: {element_description}")
                return True
        
        except Exception as e:
            logger.debug(f"❌ Click failed: {e}")
        
        return False
    
    async def human_type(
        self, 
        element_description: str, 
        text: str,
        fallback_selector: str = "",
        delay_range: tuple = (50, 150)
    ) -> bool:
        """
        Type text with human-like behavior.
        
        Args:
            element_description: Natural language description for AgentQL
            text: Text to type
            fallback_selector: CSS selector fallback
            delay_range: Random delay range between keystrokes
        
        Returns:
            True if typing was successful, False otherwise
        """
        element = await self.smart_find(element_description, fallback_selector)
        if not element:
            return False
        
        try:
            await element.click()
            await self.random_delay(100, 200)
            
            # Clear existing text
            await self.page.keyboard.press("Control+a")
            await self.random_delay(50, 100)
            
            # Type with human-like delays
            for char in text:
                await self.page.keyboard.type(char)
                await self.random_delay(delay_range[0], delay_range[1])
            
            logger.debug(f"✅ Typed in: {element_description}")
            return True
        
        except Exception as e:
            logger.debug(f"❌ Typing failed: {e}")
        
        return False
    
    async def random_delay(self, min_ms: int = 100, max_ms: int = 300) -> None:
        """Add random delay to simulate human behavior."""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def navigate_to(self, url: str, wait_until: str = "networkidle") -> bool:
        """Navigate to URL with error handling."""
        if not self.page:
            raise RuntimeError("Page not available")
        
        try:
            logger.debug(f"🌐 Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            await self.random_delay(1000, 2000)
            return True
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot for debugging."""
        if not self.page:
            raise RuntimeError("Page not available")
        
        if not filename:
            filename = f"screenshot_{self.profile_id}_{int(asyncio.get_event_loop().time())}.png"
        
        screenshot_path = self.profile_dir / filename
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        
        logger.debug(f"📸 Screenshot saved: {screenshot_path}")
        return str(screenshot_path)
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        logger.info(f"🔌 Closing browser profile: {self.profile_id}")
        
        try:
            if self.agentql_session:
                await self.agentql_session.stop()
            
            if self.page:
                await self.page.close()
            
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
                
        except Exception as e:
            logger.warning(f"⚠️  Error during browser cleanup: {e}")
        
        logger.success(f"✅ Browser closed: {self.profile_id}")