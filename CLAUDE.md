# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

🗺 Plan & Review

### Before starting work
- Write a plan to `.claude/tasks/TASK_NAME.md`.
- The plan should be a detailed implementation plan and the reasoning behind them, as well as tasks broken down.
- Don’t over plan it, always think MVP.
- Once you write the plan, firstly ask me to review it. Do not continue until I approve the plan.

### While implementing
- You should update the plan as you work.
- After you complete tasks in the plan, you should update and append detailed descriptions of the changes you made, so following tasks can be easily hand over to other engineers.

## Project Overview

This is a Python-based Pokemon card monitoring and purchasing automation system built with Playwright, AgentQL, and multi-threading. The system uses advanced AI-powered element detection and parallel processing:

- **Multi-Threaded Monitoring**: Monitors up to 6 Best Buy Pokemon products simultaneously
- **Airtable Integration**: Persistent stock tracking with historical data and analytics
- **AgentQL Intelligence**: AI-powered element detection that adapts to website changes
- **Best Buy Automation**: Complete monitoring and cart automation with stealth features
- **Google OAuth**: Automated sign-in with 2FA and backup code support

## Development Commands

### Main System Commands
Navigate to `services/automation-agent/` and run:
- `python setup.py` - Run automated setup script (dependencies, browsers, configuration)
- `python -m src.main` - Start single-product monitoring
- `python src/multi_thread_monitor.py` - Start multi-threaded monitoring (recommended)
- `python src/multi_tab_monitor.py` - Alternative: single browser with multiple tabs

### Development & Testing Commands
- `pip install -r requirements.txt` - Install Python dependencies
- `playwright install` - Install browser dependencies  
- `python -m src.browsers.agentql_browser` - Test AgentQL browser functionality
- `python -m src.agents.bestbuy_agent` - Test Best Buy agent directly

### Configuration Commands
- `cp .env.template .env` - Create environment configuration
- `nano .env` - Edit API keys and credentials
- `nano retailer_configs/bestbuy.json` - Configure products to monitor
- `nano auth_configs/bestbuy.json` - Configure account authentication

## Architecture

### Current Project Structure
```
services/automation-agent/
├── 🏠 src/
│   ├── main.py                     # Single-product monitoring entry point
│   ├── multi_thread_monitor.py     # Multi-threaded monitoring (6 products)
│   ├── multi_tab_monitor.py        # Alternative: single browser approach
│   ├── automation_service.py       # Main orchestrator
│   │
│   ├── 📊 integrations/
│   │   └── airtable_tracker.py     # Stock tracking and analytics
│   │
│   ├── 🧠 browsers/
│   │   └── agentql_browser.py      # AgentQL-powered browser automation
│   │
│   ├── 🏪 agents/
│   │   └── bestbuy_agent.py        # Best Buy-specific automation
│   │
│   ├── 🔐 auth/
│   │   └── google_auth.py          # Google OAuth automation
│   │
│   ├── ⚙️ config/
│   │   └── config_manager.py       # Configuration management
│   │
│   └── 🛠️ utils/
│       └── logger_config.py        # Logging utilities
│
├── 🏪 retailer_configs/            # Product monitoring configurations
├── 🔐 auth_configs/                # Account authentication settings
├── 📸 browser-profiles/            # Browser data and screenshots
└── 📝 logs/                        # Application logs
```

### Planned Scalable Architecture (Phase 4)
```
services/automation-agent/
├── 🏠 src/
│   ├── 🎯 core/                    # Core infrastructure
│   │   ├── browser_pool.py         # Browser pool manager (20-30 instances)
│   │   ├── proxy_manager.py        # Proxy rotation system
│   │   ├── detection_engine.py     # Multi-method detection
│   │   ├── alert_service.py        # WebSocket alert server
│   │   └── orchestrator.py         # Multi-retailer orchestration
│   │
│   ├── 🏪 agents/                  # Retailer-specific agents
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── bestbuy_agent.py        # Best Buy (implemented)
│   │   ├── target_agent.py         # Target (Shape Security)
│   │   ├── walmart_agent.py        # Walmart (PerimeterX)
│   │   ├── pokemoncenter_agent.py  # Pokemon Center (Triple protection)
│   │   └── costco_agent.py         # Costco (Membership required)
│   │
│   ├── 🛡️ stealth/                 # Anti-detection systems
│   │   ├── fingerprint_manager.py  # Browser fingerprinting
│   │   ├── behavior_simulator.py   # Human behavior simulation
│   │   ├── shape_bypass.py         # Shape Security bypass
│   │   └── perimeterx_bypass.py   # PerimeterX bypass
│   │
│   └── 📱 notifications/           # Alert channels
│       ├── websocket_server.py     # Real-time dashboard
│       ├── discord_alerts.py       # Discord webhooks
│       ├── sms_alerts.py          # Twilio SMS
│       └── push_alerts.py         # Firebase push
│
├── ⚙️ config/                      # Enhanced configuration
│   ├── proxy_config.json          # Proxy provider settings
│   ├── monitoring_config.json     # Pool and timing settings
│   └── stealth_profiles.json      # Detection avoidance profiles
│
└── 📊 .claude/tasks/              # Development task tracking
    ├── browser-pool-implementation.md
    ├── proxy-integration.md
    ├── multi-retailer-scaling.md
    ├── alert-infrastructure.md
    └── detection-avoidance.md
```

### Multi-Threading Architecture
- **Thread Pool**: Each SKU monitored in independent browser instance
- **Parallel Processing**: 6 products monitored simultaneously
- **Resource Management**: Configurable thread limits and staggered startup
- **Error Isolation**: Failure in one thread doesn't affect others
- **Load Balancing**: Randomized delays prevent overwhelming servers

### AgentQL Integration  
- **AI Element Detection**: Natural language queries ("find add to cart button")
- **Adaptive Automation**: Works even when websites change layouts
- **Fallback Selectors**: Combines AI with traditional CSS selectors
- **Smart Retry Logic**: Automatically handles page loading and timing issues

### Configuration Files
- `skus.json` - Contains 6 Best Buy Pokemon products with URLs and price limits
- `retailer_configs/bestbuy.json` - Product priorities, quantities, and purchase limits
- `auth_configs/bestbuy.json` - Account credentials and authentication settings
- `.env` - API keys (AgentQL, Airtable), monitoring settings, proxy configuration

### Proxy Configuration (Phase 4)
The system will support multiple proxy providers:
- **Residential Proxies**: PacketStream ($1/GB), Bright Data ($15/GB), IPRoyal ($7/GB)
- **Mobile Proxies**: Soax (3G/4G/5G), ProxyEmpire (US mobile IPs)
- **Distribution**: 10 direct, 10 residential, 5 mobile, 5 premium proxies across 30 browsers

### Key Dependencies
- **AgentQL**: AI-powered web automation and element detection
- **Playwright**: Cross-browser automation with stealth capabilities
- **Airtable**: Stock tracking database with historical analytics
- **Loguru**: Advanced logging with rotation and filtering
- **Asyncio**: Asynchronous programming for concurrent operations

### Planned Dependencies (Phase 4)
- **aiohttp**: Async HTTP client for API calls
- **websockets**: WebSocket server for real-time alerts
- **redis**: High-performance caching and queuing
- **fake-useragent**: Dynamic user agent generation
- **pyppeteer-stealth**: Additional stealth plugins

## Testing Strategy

The project uses manual testing and live monitoring validation. Key testing approaches:
- **AgentQL Browser Testing**: `python -m src.browsers.agentql_browser`
- **Best Buy Agent Testing**: `python -m src.agents.bestbuy_agent`
- **Multi-Threading Testing**: `python src/multi_thread_monitor.py` with short durations
- **Airtable Integration Testing**: Configure test Airtable base and monitor logging

## Development Notes

- **Current Status**: Phase 3 Complete - Multi-threading and analytics ready
- **AI-Powered**: Uses AgentQL for adaptive element detection and automation
- **Anti-Detection**: Comprehensive stealth features with human behavior simulation
- **Production Ready**: Robust error handling, logging, and configuration management
- **Scalable Architecture**: Thread pool design supports easy expansion to more products
- **Data Tracking**: Complete stock history and analytics via Airtable integration
- **Future Enhancement**: Ready for proxy integration and multi-retailer expansion

## Phase 4 Planning: Scale & Multi-Retailer Support

### Browser Pool Architecture
- **Pool Size**: 20-30 persistent browser instances
- **Load Distribution**: Round-robin assignment with health scoring
- **Session Warming**: Periodic activity to maintain "human" presence
- **Fingerprint Diversity**: Unique canvas, WebGL, audio fingerprints per browser

### Multi-Retailer Support
- **Target**: Shape Security bypass implementation
- **Walmart**: PerimeterX handling with sensor data generation
- **Pokemon Center**: Triple-layer protection (DataDome + Incapsula + hCaptcha)
- **Costco**: Membership verification and basic protection

### Alert Infrastructure
- **WebSocket Server**: Real-time dashboard and notifications
- **Multi-Channel**: Discord, SMS (Twilio), Push (Firebase), Email
- **Priority Queue**: High-priority SKUs get instant alerts
- **Latency Target**: < 1 second from detection to notification

### Detection Avoidance
- **Behavioral Simulation**: Mouse movements, typing patterns, scroll behavior
- **Navigation Patterns**: Natural browsing with search engine entry points
- **Request Throttling**: Adaptive delays based on detection risk
- **Stealth Profiles**: Maximum, Balanced, and Performance modes