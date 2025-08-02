"""
Google Sign-In automation for retailers that use OAuth
"""

import asyncio
import re
from typing import Optional, Dict, Any

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..browsers.agentql_browser import AgentQLBrowser


class GoogleAuthHandler:
    """
    Handles Google Sign-In automation for retailers.
    Supports various Google OAuth flows and 2FA handling.
    """
    
    def __init__(self, browser: AgentQLBrowser):
        self.browser = browser
        self.google_email: Optional[str] = None
        self.google_password: Optional[str] = None
        self.backup_codes: Optional[list] = None
        
    def configure_credentials(self, email: str, password: str, backup_codes: Optional[list] = None):
        """Configure Google account credentials."""
        self.google_email = email
        self.google_password = password
        self.backup_codes = backup_codes or []
        
    async def handle_google_signin(self, 
                                 wait_for_redirect: bool = True,
                                 expected_redirect_domain: str = "") -> bool:
        """
        Handle complete Google Sign-In flow.
        
        Args:
            wait_for_redirect: Whether to wait for redirect back to retailer
            expected_redirect_domain: Domain to expect redirect to
            
        Returns:
            True if sign-in successful, False otherwise
        """
        if not self.google_email or not self.google_password:
            logger.error("❌ Google credentials not configured")
            return False
            
        logger.info("🔐 Starting Google Sign-In flow...")
        
        try:
            page = await self.browser.get_page()
            
            # Step 1: Click Google Sign-In button
            google_signin_success = await self._click_google_signin_button()
            if not google_signin_success:
                return False
            
            # Step 2: Enter email
            email_success = await self._enter_email()
            if not email_success:
                return False
            
            # Step 3: Enter password
            password_success = await self._enter_password()
            if not password_success:
                return False
            
            # Step 4: Handle 2FA if present
            twofa_success = await self._handle_2fa()
            if not twofa_success:
                return False
            
            # Step 5: Handle consent/permissions if present
            consent_success = await self._handle_consent()
            if not consent_success:
                return False
            
            # Step 6: Wait for redirect back to retailer
            if wait_for_redirect:
                redirect_success = await self._wait_for_redirect(expected_redirect_domain)
                if not redirect_success:
                    return False
            
            logger.success("✅ Google Sign-In completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Sign-In failed: {e}")
            return False
    
    async def _click_google_signin_button(self) -> bool:
        """Click the Google Sign-In button on retailer page."""
        logger.debug("🔍 Looking for Google Sign-In button...")
        
        # Common Google Sign-In button patterns
        google_button_queries = [
            "Sign in with Google button",
            "Continue with Google button", 
            "Google login button",
            "Sign up with Google button"
        ]
        
        google_button_selectors = [
            '[data-provider="google"]',
            '[data-testid*="google"]',
            '.google-signin-button',
            '.btn-google',
            'button[aria-label*="Google"]',
            'button[title*="Google"]',
            'a[href*="accounts.google.com"]',
            'button:has-text("Google")',
            'button:has-text("Continue with Google")',
            'button:has-text("Sign in with Google")'
        ]
        
        # Try AgentQL queries first
        for query in google_button_queries:
            for selector in google_button_selectors:
                success = await self.browser.human_click(query, selector)
                if success:
                    logger.debug(f"✅ Clicked Google Sign-In button: {query}")
                    await self.browser.random_delay(2000, 4000)
                    return True
        
        logger.error("❌ Could not find Google Sign-In button")
        return False
    
    async def _enter_email(self) -> bool:
        """Enter email address on Google Sign-In page."""
        logger.debug("📧 Entering Google email...")
        
        try:
            page = await self.browser.get_page()
            
            # Wait for Google login page
            await page.wait_for_url("**/accounts.google.com/**", timeout=10000)
            
            # Enter email
            email_success = await self.browser.human_type(
                "email input field",
                self.google_email,
                'input[type="email"], #identifierId, input[autocomplete="username"]'
            )
            
            if not email_success:
                logger.error("❌ Failed to enter email")
                return False
            
            # Click Next button
            next_success = await self.browser.human_click(
                "next button to continue",
                '#identifierNext, button[jsname="LgbsSe"], #next'
            )
            
            if not next_success:
                logger.error("❌ Failed to click Next after email")
                return False
            
            await self.browser.random_delay(2000, 4000)
            logger.debug("✅ Email entered successfully")
            return True
            
        except PlaywrightTimeoutError:
            logger.error("❌ Timeout waiting for Google login page")
            return False
        except Exception as e:
            logger.error(f"❌ Error entering email: {e}")
            return False
    
    async def _enter_password(self) -> bool:
        """Enter password on Google Sign-In page."""
        logger.debug("🔑 Entering Google password...")
        
        try:
            page = await self.browser.get_page()
            
            # Wait for password field to appear
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            
            # Enter password
            password_success = await self.browser.human_type(
                "password input field",
                self.google_password,
                'input[type="password"], input[autocomplete="current-password"]'
            )
            
            if not password_success:
                logger.error("❌ Failed to enter password")
                return False
            
            # Click Next/Sign In button
            signin_success = await self.browser.human_click(
                "sign in or next button",
                '#passwordNext, button[jsname="LgbsSe"], #signin, button[type="submit"]'
            )
            
            if not signin_success:
                logger.error("❌ Failed to click Sign In button")
                return False
            
            await self.browser.random_delay(3000, 5000)
            logger.debug("✅ Password entered successfully")
            return True
            
        except PlaywrightTimeoutError:
            logger.error("❌ Timeout waiting for password field")
            return False
        except Exception as e:
            logger.error(f"❌ Error entering password: {e}")
            return False
    
    async def _handle_2fa(self) -> bool:
        """Handle 2FA verification if present."""
        logger.debug("🔒 Checking for 2FA...")
        
        try:
            page = await self.browser.get_page()
            
            # Check if 2FA is required
            twofa_indicators = [
                'input[aria-label*="verification"]',
                'input[placeholder*="code"]',
                '#totpPin',
                '[data-testid="totpPin"]',
                'input[autocomplete="one-time-code"]'
            ]
            
            twofa_field = None
            for selector in twofa_indicators:
                try:
                    twofa_field = await page.wait_for_selector(selector, timeout=3000)
                    if twofa_field:
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not twofa_field:
                logger.debug("✅ No 2FA required")
                return True
            
            logger.info("🔒 2FA verification required")
            
            # Handle different 2FA methods
            return await self._handle_2fa_methods()
            
        except Exception as e:
            logger.debug(f"Error checking 2FA: {e}")
            return True  # Assume no 2FA if error
    
    async def _handle_2fa_methods(self) -> bool:
        """Handle various 2FA verification methods."""
        page = await self.browser.get_page()
        
        # Method 1: Try backup codes if available
        if self.backup_codes:
            logger.info("🔑 Trying backup codes...")
            
            # Look for "Try another way" or "Use backup code" link
            try_another_way = await self.browser.smart_find(
                "try another way or use backup code link",
                'a:has-text("Try another way"), a:has-text("backup"), button:has-text("Try another way")'
            )
            
            if try_another_way:
                await try_another_way.click()
                await self.browser.random_delay(2000, 3000)
                
                # Look for backup code option
                backup_code_option = await self.browser.smart_find(
                    "backup code option or enter backup code",
                    'a:has-text("backup"), button:has-text("backup"), [data-action*="backup"]'
                )
                
                if backup_code_option:
                    await backup_code_option.click()
                    await self.browser.random_delay(1000, 2000)
                    
                    # Enter backup code
                    for backup_code in self.backup_codes:
                        backup_success = await self.browser.human_type(
                            "backup code input field",
                            backup_code,
                            'input[type="text"], input[autocomplete="one-time-code"]'
                        )
                        
                        if backup_success:
                            # Click Next
                            next_success = await self.browser.human_click(
                                "next or verify button",
                                'button[type="submit"], #next, button:has-text("Next")'
                            )
                            
                            if next_success:
                                await self.browser.random_delay(3000, 5000)
                                
                                # Check if successful (no longer on 2FA page)
                                still_on_2fa = await page.locator('input[autocomplete="one-time-code"]').count()
                                if still_on_2fa == 0:
                                    logger.success("✅ 2FA completed with backup code")
                                    return True
        
        # Method 2: Prompt user for manual 2FA
        logger.warning("⚠️  2FA verification detected - Manual intervention required")
        logger.info("📱 Please complete 2FA verification manually...")
        logger.info("🔍 Waiting for 2FA completion (max 2 minutes)...")
        
        # Wait for user to complete 2FA manually
        max_wait_time = 120  # 2 minutes
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            # Check if still on 2FA page
            try:
                current_url = page.url
                if "challenge" not in current_url and "verify" not in current_url:
                    logger.success("✅ 2FA completed manually")
                    return True
                
                # Check if 2FA fields are gone
                twofa_fields = await page.locator('input[autocomplete="one-time-code"]').count()
                if twofa_fields == 0:
                    logger.success("✅ 2FA completed manually")
                    return True
                    
            except Exception:
                pass
            
            await asyncio.sleep(5)
        
        logger.error("❌ 2FA verification timeout")
        return False
    
    async def _handle_consent(self) -> bool:
        """Handle Google consent/permissions page if present."""
        logger.debug("📋 Checking for consent page...")
        
        try:
            page = await self.browser.get_page()
            
            # Wait a moment for page to load
            await self.browser.random_delay(2000, 3000)
            
            # Check for consent/permissions page
            consent_indicators = [
                'button:has-text("Continue")',
                'button:has-text("Allow")',
                'button:has-text("Accept")',
                'button[data-testid="continue"]',
                '#submit_approve_access'
            ]
            
            for selector in consent_indicators:
                consent_button = await page.locator(selector).first
                if await consent_button.is_visible():
                    logger.debug("📋 Found consent page, clicking continue...")
                    await consent_button.click()
                    await self.browser.random_delay(2000, 4000)
                    logger.debug("✅ Consent handled")
                    return True
            
            logger.debug("✅ No consent page required")
            return True
            
        except Exception as e:
            logger.debug(f"Error handling consent: {e}")
            return True  # Assume no consent needed if error
    
    async def _wait_for_redirect(self, expected_domain: str = "") -> bool:
        """Wait for redirect back to retailer site."""
        logger.debug("🔄 Waiting for redirect to retailer...")
        
        try:
            page = await self.browser.get_page()
            
            # Wait for redirect (max 30 seconds)
            max_wait_time = 30
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
                current_url = page.url
                
                # Check if we're back on retailer site
                if "accounts.google.com" not in current_url:
                    if expected_domain:
                        if expected_domain in current_url:
                            logger.success(f"✅ Redirected to {expected_domain}")
                            return True
                    else:
                        logger.success("✅ Redirected from Google")
                        return True
                
                await asyncio.sleep(1)
            
            logger.error("❌ Redirect timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error waiting for redirect: {e}")
            return False
    
    async def is_already_signed_in(self) -> bool:
        """Check if user is already signed in to retailer via Google."""
        try:
            page = await self.browser.get_page()
            
            # Common signed-in indicators
            signin_indicators = [
                "account menu or profile dropdown",
                "sign out link or button",
                "my account link",
                "user profile picture or avatar"
            ]
            
            signin_selectors = [
                '.account-menu',
                '[data-testid*="account"]',
                'a:has-text("Sign Out")',
                'button:has-text("Sign Out")',
                'a:has-text("My Account")',
                '.user-avatar',
                '.profile-menu'
            ]
            
            # Check for signed-in indicators
            for i, query in enumerate(signin_indicators):
                if i < len(signin_selectors):
                    element = await self.browser.smart_find(query, signin_selectors[i])
                    if element:
                        logger.debug("✅ Already signed in")
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking sign-in status: {e}")
            return False