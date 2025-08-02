"""
Core automation service that orchestrates all Pokemon card monitoring and purchasing
"""

import asyncio
import os
from typing import Dict, Any

from loguru import logger

from .agents.bestbuy_agent import BestBuyAgent
from .config.config_manager import ConfigManager


class AutomationService:
    """Main service that coordinates all automation agents."""
    
    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.agents: Dict[str, Any] = {}
        self.is_running = False
        self._monitor_task: asyncio.Task | None = None
    
    async def start(self) -> None:
        """Start the automation service and all enabled agents."""
        try:
            logger.info("🔧 Initializing automation service...")
            
            # Load configurations
            await self.config_manager.load_configurations()
            
            # Initialize agents based on configuration
            await self._initialize_agents()
            
            self.is_running = True
            logger.info(f"✅ Automation service started with {len(self.agents)} agents")
            
            # Start monitoring loop
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
        except Exception as e:
            logger.error(f"❌ Failed to start automation service: {e}")
            raise
    
    async def _initialize_agents(self) -> None:
        """Initialize all enabled retail agents."""
        
        # Initialize Best Buy agent if enabled
        if self.config_manager.is_retailer_enabled("bestbuy"):
            logger.info("🏪 Initializing Best Buy agent...")
            try:
                bestbuy_agent = BestBuyAgent(self.config_manager)
                await bestbuy_agent.initialize()
                self.agents["bestbuy"] = bestbuy_agent
                logger.success("✅ Best Buy agent initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Best Buy agent: {e}")
        
        # Add other retailers here (Target, Walmart, etc.)
        # if self.config_manager.is_retailer_enabled("target"):
        #     self.agents["target"] = TargetAgent(self.config_manager)
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs all agent monitoring cycles."""
        monitor_interval = int(os.getenv("MONITOR_INTERVAL_SECONDS", "30"))
        
        while self.is_running:
            try:
                logger.debug("🔄 Starting monitoring cycle...")
                
                # Run monitoring for all agents concurrently
                monitoring_tasks = []
                for name, agent in self.agents.items():
                    if hasattr(agent, 'monitor'):
                        task = asyncio.create_task(
                            agent.monitor(),
                            name=f"monitor_{name}"
                        )
                        monitoring_tasks.append(task)
                
                if monitoring_tasks:
                    # Wait for all monitoring tasks to complete
                    await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                
                logger.debug(f"⏱️  Monitoring cycle complete, waiting {monitor_interval}s...")
                await asyncio.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(5)
    
    async def stop(self) -> None:
        """Stop the automation service and all agents."""
        logger.info("🛑 Stopping automation service...")
        self.is_running = False
        
        # Cancel monitoring task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all agents
        stop_tasks = []
        for name, agent in self.agents.items():
            if hasattr(agent, 'stop'):
                logger.info(f"🔌 Stopping {name} agent...")
                task = asyncio.create_task(agent.stop(), name=f"stop_{name}")
                stop_tasks.append(task)
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.agents.clear()
        logger.success("✅ Automation service stopped")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status information for all agents."""
        status = {
            "is_running": self.is_running,
            "agents": {}
        }
        
        for name, agent in self.agents.items():
            if hasattr(agent, 'get_status'):
                status["agents"][name] = agent.get_status()
            else:
                status["agents"][name] = {"status": "unknown"}
        
        return status