#!/usr/bin/env python3
"""
Test script to check a single SKU and log to Airtable
"""

import asyncio
import sys
from loguru import logger
from src.browsers.agentql_browser import AgentQLBrowser
from src.integrations.airtable_tracker import AirtableTracker


async def check_single_sku(sku: str, name: str):
    """Check a single SKU availability"""
    browser = None
    airtable = AirtableTracker()
    
    try:
        # Launch browser
        browser = AgentQLBrowser("test-single-sku", headless=False)
        await browser.launch()
        
        logger.info(f"🔍 Checking SKU {sku}: {name}")
        
        # Navigate to product page
        url = f"https://www.bestbuy.com/site/{sku}.p"
        logger.info(f"📍 Navigating to: {url}")
        
        if not await browser.navigate_to(url, wait_until="networkidle"):
            logger.error("❌ Failed to navigate to product page")
            result = {"available": False, "price": None}
        else:
            # Wait for page to fully load
            await asyncio.sleep(5)
            
            # Take screenshot for debugging
            await browser.take_screenshot(f"single_sku_{sku}")
            
            # Check for add to cart button
            add_to_cart = await browser.smart_find(
                "add to cart button",
                'button[data-button-state="ADD_TO_CART"], button:has-text("Add to Cart")'
            )
            
            if add_to_cart:
                is_visible = await add_to_cart.is_visible()
                is_enabled = await add_to_cart.is_enabled()
                logger.info(f"🛒 Add to Cart button found - Visible: {is_visible}, Enabled: {is_enabled}")
                result = {"available": is_visible and is_enabled, "price": None}
            else:
                logger.info("❌ No Add to Cart button found - Product likely out of stock")
                result = {"available": False, "price": None}
            
            # Try to get price
            try:
                price_element = await browser.smart_find(
                    "product price",
                    '.priceView-hero-price span, [class*="pricing"]'
                )
                if price_element:
                    price_text = await price_element.text_content()
                    logger.info(f"💰 Price found: {price_text}")
                    import re
                    price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                    if price_match:
                        result['price'] = float(price_match.group(1))
            except Exception as e:
                logger.warning(f"⚠️ Could not extract price: {e}")
        
        # Log to Airtable
        if airtable.enabled:
            success = airtable.log_stock_check(
                sku=sku,
                product_name=name,
                is_available=result['available'],
                price=result['price'],
                url=url
            )
            if success:
                logger.success(f"✅ Logged to Airtable - Available: {result['available']}, Price: ${result.get('price', 'N/A')}")
            else:
                logger.error("❌ Failed to log to Airtable")
        else:
            logger.warning("⚠️ Airtable is disabled")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error checking SKU: {e}")
        return {"available": False, "price": None}
    finally:
        if browser:
            await browser.close()


async def main():
    """Test all 6 SKUs one by one"""
    test_skus = [
        {
            "sku": "6634940",
            "name": "Pokemon Trading Card Game Holiday Calendar 2025"
        },
        {
            "sku": "6402619", 
            "name": "Pokemon TCG Product - SKU 6402619"
        },
        {
            "sku": "6632394",
            "name": "Pokemon Trading Card Game Scarlet & Violet White Flare Elite Trainer Box"
        },
        {
            "sku": "6632390",
            "name": "Pokemon Trading Card Game Scarlet & Violet White Flare Binder Collection"
        },
        {
            "sku": "6632397",
            "name": "Pokemon Trading Card Game Scarlet & Violet Black Bolt Elite Trainer Box"
        },
        {
            "sku": "6614259",
            "name": "Pokemon Trading Card Game Scarlet & Violet Journey Together Sleeved Booster"
        }
    ]
    
    logger.info(f"🚀 Testing {len(test_skus)} SKUs sequentially...")
    
    results = []
    for i, sku_data in enumerate(test_skus, 1):
        logger.info(f"\n📦 Testing SKU {i}/{len(test_skus)}")
        result = await check_single_sku(sku_data['sku'], sku_data['name'])
        results.append({**sku_data, **result})
        
        # Wait between checks
        if i < len(test_skus):
            logger.info("⏳ Waiting 30s before next check...")
            await asyncio.sleep(30)
    
    # Summary
    logger.info("\n📊 SUMMARY:")
    logger.info("=" * 50)
    available_count = sum(1 for r in results if r['available'])
    logger.info(f"Total SKUs: {len(results)}")
    logger.info(f"Available: {available_count}")
    logger.info(f"Out of Stock: {len(results) - available_count}")
    logger.info("=" * 50)
    
    for r in results:
        status = "✅ IN STOCK" if r['available'] else "❌ OUT OF STOCK"
        price = f"${r['price']}" if r.get('price') else "N/A"
        logger.info(f"{status} - {r['name']} (SKU: {r['sku']}, Price: {price})")


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/test_single_sku.log",
        rotation="100 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    print("""
    🧪 Single SKU Test Script
    ========================
    Testing each SKU individually with detailed logging...
    """)
    
    asyncio.run(main())