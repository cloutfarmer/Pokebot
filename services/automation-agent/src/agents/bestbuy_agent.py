"""
Best Buy automation agent with AgentQL integration
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from loguru import logger

from ..browsers.agentql_browser import AgentQLBrowser
from ..config.config_manager import ConfigManager, SKUConfig, RetailerConfig
from ..auth.google_auth import GoogleAuthHandler


class BestBuyAgent:
    """
    Automated Best Buy Pokemon card monitoring and purchasing agent.
    Uses AgentQL for intelligent element detection and handles Best Buy's queue system.
    """
    
    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager
        self.config: Optional[RetailerConfig] = None
        self.browser: Optional[AgentQLBrowser] = None
        self.google_auth: Optional[GoogleAuthHandler] = None
        self.is_monitoring = False
        self.last_check_time: Optional[datetime] = None
        self.successful_purchases = 0
        self.failed_attempts = 0
        self.is_signed_in = False
        
    async def initialize(self) -> None:
        """Initialize the Best Buy agent."""
        logger.info("🏪 Initializing Best Buy agent...")
        
        # Get configuration
        self.config = self.config_manager.get_retailer_config("bestbuy")
        if not self.config:
            raise ValueError("Best Buy configuration not found")
        
        if not self.config.enabled:
            logger.warning("⚠️  Best Buy agent is disabled in configuration")
            return
        
        # Initialize browser
        headless = os.getenv("HEADLESS_MODE", "true").lower() == "true"
        self.browser = AgentQLBrowser("bestbuy-main", headless=headless)
        
        # Get proxy if configured
        proxy = os.getenv("PROXY_ENDPOINT")
        await self.browser.launch(proxy=proxy)
        
        # Initialize Google authentication if configured
        if self.config.authentication and self.config.authentication.use_google_signin:
            self.google_auth = GoogleAuthHandler(self.browser)
            self.google_auth.configure_credentials(
                email=self.config.authentication.google_email,
                password=self.config.authentication.google_password,
                backup_codes=self.config.authentication.google_backup_codes
            )
            logger.info("🔐 Google authentication configured")
        
        logger.success("✅ Best Buy agent initialized")
    
    async def monitor(self) -> None:
        """Main monitoring loop for Best Buy products."""
        if not self.config or not self.config.enabled:
            return
        
        if self.is_monitoring:
            logger.debug("🔄 Best Buy monitoring already in progress, skipping...")
            return
        
        self.is_monitoring = True
        self.last_check_time = datetime.now()
        
        try:
            logger.info("🔍 Starting Best Buy monitoring cycle...")
            
            # Ensure we're signed in if authentication is configured
            if not self.is_signed_in:
                signin_success = await self._ensure_signed_in()
                if not signin_success:
                    logger.warning("⚠️  Could not sign in, continuing with guest access")
            
            # Check each SKU
            for sku in self.config.skus:
                try:
                    await self._check_sku(sku)
                    
                    # Random delay between SKU checks
                    if self.browser:
                        await self.browser.random_delay(2000, 5000)
                    
                except Exception as e:
                    logger.error(f"❌ Error checking SKU {sku.sku}: {e}")
                    self.failed_attempts += 1
            
            logger.debug("✅ Best Buy monitoring cycle completed")
            
        except Exception as e:
            logger.error(f"❌ Error in Best Buy monitoring: {e}")
            
        finally:
            self.is_monitoring = False
    
    async def _check_sku(self, sku: SKUConfig) -> None:
        """Check availability for a specific SKU."""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        logger.debug(f"🔍 Checking Best Buy SKU: {sku.sku} - {sku.name}")
        
        # Build Best Buy product URL
        product_url = f"https://www.bestbuy.com/site/{sku.sku}.p"
        
        # Navigate to product page
        navigation_success = await self.browser.navigate_to(product_url)
        if not navigation_success:
            logger.error(f"❌ Failed to navigate to {product_url}")
            return
        
        # Check if product is available
        is_available = await self._check_product_availability()
        
        if is_available:
            logger.success(f"🚨 POKEMON PRODUCT AVAILABLE: {sku.name} (${sku.max_price})")
            
            # Check current price
            current_price = await self._get_current_price()
            if current_price and current_price <= sku.max_price:
                logger.info(f"💰 Price check passed: ${current_price} <= ${sku.max_price}")
                await self._attempt_purchase(sku, current_price)
            else:
                logger.warning(f"💸 Price too high: ${current_price} > ${sku.max_price}")
        else:
            logger.debug(f"❌ Product not available: {sku.name}")
    
    async def _check_product_availability(self) -> bool:
        """Check if the current product page shows availability."""
        if not self.browser:
            return False
        
        try:
            # Use AgentQL to find add to cart button
            add_to_cart = await self.browser.smart_find(
                "add to cart button that is enabled and clickable",
                'button[data-track="Add to Cart"]:not([disabled])'
            )
            
            if add_to_cart:
                logger.debug("✅ Add to cart button found and enabled")
                return True
            
            # Check for other availability indicators
            availability_indicators = [
                "in stock text or message",
                "available for pickup text",
                "ship it button that is enabled"
            ]
            
            for indicator in availability_indicators:
                element = await self.browser.smart_find(indicator)
                if element:
                    logger.debug(f"✅ Availability indicator found: {indicator}")
                    return True
            
            # Check for out of stock indicators
            out_of_stock_indicators = [
                "sold out message",
                "currently unavailable message", 
                "out of stock text"
            ]
            
            for indicator in out_of_stock_indicators:
                element = await self.browser.smart_find(indicator)
                if element:
                    logger.debug(f"❌ Out of stock indicator found: {indicator}")
                    return False
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking availability: {e}")
            return False
    
    async def _get_current_price(self) -> Optional[float]:
        """Extract current price from the product page."""
        if not self.browser:
            return None
        
        try:
            # Use AgentQL to find price
            price_element = await self.browser.smart_find(
                "current price or sale price of the product",
                '.pricing-price__wrapper .sr-only, .pricing-price__wrapper .current-price'
            )
            
            if price_element and hasattr(price_element, 'text_content'):
                price_text = await price_element.text_content()
                
                # Extract price from text like "$49.99" or "Current Price $49.99"
                import re
                price_match = re.search(r'\$(\d+\.\d+)', price_text)
                if price_match:
                    return float(price_match.group(1))
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting price: {e}")
            return None
    
    async def _attempt_purchase(self, sku: SKUConfig, price: float) -> None:
        """Attempt to purchase the product."""
        if not self.browser:
            return
        
        logger.info(f"🛒 Attempting to purchase: {sku.name} for ${price}")
        
        try:
            # Click Add to Cart with AgentQL
            success = await self.browser.human_click(
                "add to cart button",
                'button[data-track="Add to Cart"]'
            )
            
            if not success:
                logger.error("❌ Failed to click Add to Cart")
                self.failed_attempts += 1
                return
            
            # Wait for response
            await self.browser.random_delay(2000, 4000)
            
            # Check if we're in Best Buy's queue
            queue_detected = await self._handle_queue()
            
            if queue_detected:
                logger.info("⏳ Handled Best Buy queue, checking cart...")
            
            # Verify item was added to cart
            cart_success = await self._verify_cart_addition()
            
            if cart_success:
                logger.success(f"🎉 Successfully added {sku.name} to cart!")
                self.successful_purchases += 1
                
                # Navigate to checkout for manual completion
                await self._navigate_to_checkout()
                
                # Notify user for manual completion
                await self._notify_manual_checkout_required(sku, price)
                
            else:
                logger.error("❌ Failed to add item to cart")
                self.failed_attempts += 1
            
        except Exception as e:
            logger.error(f"❌ Purchase attempt failed: {e}")
            self.failed_attempts += 1
            
            # Take screenshot for debugging
            if os.getenv("SCREENSHOT_ON_ERROR", "true").lower() == "true":
                screenshot_path = await self.browser.take_screenshot(
                    f"bestbuy_error_{sku.sku}_{int(datetime.now().timestamp())}.png"
                )
                logger.info(f"📸 Error screenshot saved: {screenshot_path}")
    
    async def _handle_queue(self) -> bool:
        """Handle Best Buy's queue system if present."""
        if not self.browser:
            return False
        
        try:
            # Check for queue
            queue_element = await self.browser.smart_find(
                "queue waiting message or please wait text",
                '.queue-it-main, .loading-message, [class*="queue"]'
            )
            
            if not queue_element:
                return False
            
            logger.info("⏳ Detected Best Buy queue, waiting...")
            
            # Wait in queue (max 10 minutes)
            max_wait_time = 600  # 10 minutes
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
                # Check if queue is complete
                add_to_cart = await self.browser.smart_find(
                    "add to cart button",
                    'button[data-track="Add to Cart"]'
                )
                
                if add_to_cart:
                    logger.success("✅ Queue complete!")
                    return True
                
                # Check queue position if available
                position_element = await self.browser.smart_find(
                    "queue position number or waiting message"
                )
                
                if position_element and hasattr(position_element, 'text_content'):
                    position_text = await position_element.text_content()
                    logger.info(f"⏳ Queue status: {position_text}")
                
                # Wait before checking again
                await asyncio.sleep(5)
            
            logger.warning("⚠️  Queue timeout reached")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error handling queue: {e}")
            return False
    
    async def _verify_cart_addition(self) -> bool:
        """Verify that item was successfully added to cart."""
        if not self.browser:
            return False
        
        try:
            # Look for cart count or success message
            cart_indicators = [
                "item added to cart message",
                "cart count number that is greater than 0",
                "view cart button",
                "checkout button"
            ]
            
            for indicator in cart_indicators:
                element = await self.browser.smart_find(indicator)
                if element:
                    logger.debug(f"✅ Cart verification: {indicator}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error verifying cart: {e}")
            return False
    
    async def _navigate_to_checkout(self) -> None:
        """Navigate to checkout page."""
        if not self.browser:
            return
        
        try:
            logger.info("🛒 Navigating to checkout...")
            
            # Try to click cart or checkout button
            checkout_success = await self.browser.human_click(
                "go to cart or checkout button",
                '.cart-link, [data-track="cart"], .checkout-button'
            )
            
            if not checkout_success:
                # Fallback: navigate directly to cart
                await self.browser.navigate_to("https://www.bestbuy.com/cart")
            
            await self.browser.random_delay(2000, 3000)
            
        except Exception as e:
            logger.error(f"❌ Error navigating to checkout: {e}")
    
    async def _notify_manual_checkout_required(self, sku: SKUConfig, price: float) -> None:
        """Notify that manual checkout is required."""
        message = f"""
🚨 MANUAL CHECKOUT REQUIRED! 🚨

Product: {sku.name}
Price: ${price}
Store: Best Buy

The item has been added to your cart. Please complete the checkout manually:
1. Review your cart
2. Sign in to your Best Buy account
3. Enter payment and shipping information  
4. Complete the purchase

Browser window is open for manual completion.
        """
        
        logger.critical(message)
        
        # Send Discord notification if configured
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url and os.getenv("ENABLE_DISCORD_NOTIFICATIONS", "false").lower() == "true":
            await self._send_discord_notification(message)
    
    async def _send_discord_notification(self, message: str) -> None:
        """Send Discord webhook notification."""
        try:
            import httpx
            
            webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
            if not webhook_url:
                return
            
            payload = {
                "content": f"🤖 **Pokemon Card Bot Alert**\n```\n{message}\n```"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                
                if response.status_code == 204:
                    logger.debug("📱 Discord notification sent")
                else:
                    logger.warning(f"⚠️  Discord notification failed: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"⚠️  Discord notification error: {e}")
    
    async def stop(self) -> None:
        """Stop the Best Buy agent and cleanup."""
        logger.info("🛑 Stopping Best Buy agent...")
        
        self.is_monitoring = False
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        logger.success("✅ Best Buy agent stopped")
    
    async def _ensure_signed_in(self) -> bool:
        """Ensure user is signed in to Best Buy."""
        if not self.browser:
            return False
        
        logger.info("🔐 Checking Best Buy sign-in status...")
        
        # Navigate to Best Buy if not already there
        page = await self.browser.get_page()
        current_url = page.url
        if "bestbuy.com" not in current_url:
            await self.browser.navigate_to("https://www.bestbuy.com")
        
        # Check if already signed in
        if self.google_auth:
            already_signed_in = await self.google_auth.is_already_signed_in()
            if already_signed_in:
                logger.success("✅ Already signed in to Best Buy")
                self.is_signed_in = True
                return True
        
        # Try to sign in
        if self.config.authentication:
            if self.config.authentication.use_google_signin and self.google_auth:
                return await self._sign_in_with_google()
            else:
                return await self._sign_in_with_email()
        
        return False
    
    async def _sign_in_with_google(self) -> bool:
        """Sign in to Best Buy using Google OAuth."""
        if not self.google_auth or not self.browser:
            return False
        
        logger.info("🔐 Signing in to Best Buy with Google...")
        
        try:
            # Navigate to sign-in page
            await self.browser.navigate_to("https://www.bestbuy.com/identity/signin")
            await self.browser.random_delay(2000, 3000)
            
            # Handle Google Sign-In flow
            success = await self.google_auth.handle_google_signin(
                wait_for_redirect=True,
                expected_redirect_domain="bestbuy.com"
            )
            
            if success:
                self.is_signed_in = True
                logger.success("✅ Successfully signed in to Best Buy with Google")
                return True
            else:
                logger.error("❌ Google sign-in failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google sign-in error: {e}")
            return False
    
    async def _sign_in_with_email(self) -> bool:
        """Sign in to Best Buy using email/password."""
        if not self.browser or not self.config.authentication:
            return False
        
        logger.info("🔐 Signing in to Best Buy with email/password...")
        
        try:
            # Navigate to sign-in page
            await self.browser.navigate_to("https://www.bestbuy.com/identity/signin")
            await self.browser.random_delay(2000, 3000)
            
            # Enter email
            email_success = await self.browser.human_type(
                "email input field",
                self.config.authentication.email,
                'input[type="email"], input[name="email"], #fld-e'
            )
            
            if not email_success:
                logger.error("❌ Failed to enter email")
                return False
            
            # Enter password
            password_success = await self.browser.human_type(
                "password input field",
                self.config.authentication.password,
                'input[type="password"], input[name="password"], #fld-p1'
            )
            
            if not password_success:
                logger.error("❌ Failed to enter password")
                return False
            
            # Click sign-in button
            signin_success = await self.browser.human_click(
                "sign in button",
                'button[type="submit"], .btn-primary, button:has-text("Sign In")'
            )
            
            if not signin_success:
                logger.error("❌ Failed to click sign-in button")
                return False
            
            # Wait for sign-in to complete
            await self.browser.random_delay(3000, 5000)
            
            # Verify sign-in success
            page = await self.browser.get_page()
            if "signin" not in page.url:
                self.is_signed_in = True
                logger.success("✅ Successfully signed in to Best Buy with email")
                return True
            else:
                logger.error("❌ Sign-in failed - still on sign-in page")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email sign-in error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Best Buy agent."""
        return {
            "enabled": self.config.enabled if self.config else False,
            "is_monitoring": self.is_monitoring,
            "is_signed_in": self.is_signed_in,
            "google_auth_configured": self.google_auth is not None,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "successful_purchases": self.successful_purchases,
            "failed_attempts": self.failed_attempts,
            "monitored_skus": len(self.config.skus) if self.config else 0
        }