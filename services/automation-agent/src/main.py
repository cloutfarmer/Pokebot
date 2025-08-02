#!/usr/bin/env python3
"""
Main entry point for the Pokemon Card Automation Agent
"""

import asyncio
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from .automation_service import AutomationService
from .utils.logger_config import setup_logging


async def main() -> None:
    """Main entry point for the automation agent."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    # Setup logging
    setup_logging()
    
    logger.info("🚀 Starting Pokemon Card Automation Agent...")
    
    # Initialize automation service
    automation_service = AutomationService()
    
    # Setup graceful shutdown
    def signal_handler(signum: int, frame) -> None:
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(automation_service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await automation_service.start()
        
        # Keep the service running
        while automation_service.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in automation service: {e}")
        sys.exit(1)
    finally:
        await automation_service.stop()
        logger.info("✅ Automation agent stopped")


if __name__ == "__main__":
    asyncio.run(main())