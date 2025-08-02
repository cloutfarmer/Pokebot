# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-service Pokémon card monitoring and purchasing bot system built with TypeScript and Node.js. The project uses a monorepo architecture with npm workspaces to manage multiple services:

- **Scout Service**: Monitors SKUs from `skus.json` and detects stock changes via web scraping
- **Local Monitor Service**: Monitors local stores for Pokemon products by ZIP code 
- **Agents Service**: Future purchasing automation (not yet implemented)
- **Account Manager**: Future account/proxy management (not yet implemented)

## Development Commands

### Root Level Commands
- `npm run dev` - Start development environment with Docker Compose
- `npm run build` - Build all workspace services  
- `npm run test` - Run tests across all workspaces
- `npm run lint` - Run ESLint on TypeScript files
- `npm run lint:fix` - Fix ESLint issues automatically
- `npm run format` - Format code with Prettier
- `npm run setup` - Install dependencies and start Redis/PostgreSQL containers

### Service-Specific Commands
Navigate to individual service directories (`services/scout/`, `services/local-monitor/`) and run:
- `npm run dev` - Run service in development mode with ts-node
- `npm run build` - Compile TypeScript to JavaScript  
- `npm run start` - Run compiled JavaScript
- `npm test` - Run Jest tests for that service

### Local Monitor Dashboard (File-Based)
The local-monitor service includes a simple file-based interface:
- `npm run status` - Show current monitoring status and recent findings
- `npm run watch` - Live-updating status display (refreshes every 5 seconds)
- `npm run logs` - Follow live logs
- `cat data/summary.txt` - View full text summary
- `cat data/status.json` - View JSON status data
- `cat data/stores.json` - View discovered stores data
- `cat data/products-found.json` - View recent Pokemon product findings

## Architecture

### Monorepo Structure
```
services/
├── scout/           # Stock monitoring via SKU file watching
├── local-monitor/   # Local store inventory checking  
├── agents/          # Future: purchasing automation
├── account-manager/ # Future: account/proxy management
└── shared/          # Future: shared utilities
```

### Scout Service Architecture
- Watches `skus.json` for changes using chokidar
- Polls retailer websites every 30 seconds (with jitter) for stock status
- Currently supports Walmart and Best Buy via HTML scraping
- Uses axios for HTTP requests with browser-like User-Agent headers
- Implements basic out-of-stock detection by searching for keywords in HTML

### Local Monitor Service  
- Monitors local stores by ZIP code within specified radius
- Uses StoreLocator to find nearby stores
- Currently implements Best Buy local inventory checking
- Configurable via `services/local-monitor/config/local-config.json`
- Includes notification system for stock alerts

### Configuration Files
- `skus.json` - Contains retailer SKUs to monitor with price limits
- `services/local-monitor/config/local-config.json` - Local monitoring configuration
- TypeScript config uses strict mode with comprehensive error checking

### Key Dependencies
- **chokidar**: File watching for SKU updates
- **axios**: HTTP client for web scraping
- **dotenv**: Environment variable management
- **ts-node**: Development-time TypeScript execution

## Testing Strategy

The project uses Jest for testing. Test files follow the pattern `*.test.ts` or `*.spec.ts` and are excluded from TypeScript compilation.

## Development Notes

- The project is currently in "Phase 0" - basic stock monitoring only
- Web scraping uses simple HTML text analysis for stock detection
- No proxy rotation or anti-detection measures implemented yet
- Future phases will add purchasing automation, CAPTCHA solving, and additional retailers
- All services use TypeScript with strict mode enabled
- The system is designed to be modular for easy extension to new retailers