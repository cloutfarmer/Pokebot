# 🤖 Pokebot - Multi-Site Pokémon Card Bot

A modular bot system for monitoring and purchasing Pokémon cards from multiple retailers at MSRP prices.

## 🎯 Project Overview

This bot system uses a "scout and agents" architecture:
- **Scout Service**: Monitors SKUs from a file and detects stock changes
- **Purchasing Agents**: Execute purchases when stock is detected (coming in Phase 2)
- **Account Manager**: Manages accounts and proxies (coming in Phase 2)

## 🏗️ Architecture

```
┌─────────────────┐
│ SKU File Watcher│ (watches skus.json for changes)
└─────────────────┘
         │
         ▼
┌─────────────────┐    stock events    ┌─────────────────┐
│  Scout Service  │ ──────────────────▶ │  Future: Queue  │
│ (Site Modules)  │                     │                 │
└─────────────────┘                     └─────────────────┘
```

## 🚀 Current Status - Phase 0 Complete ✅

### ✅ Completed
- [x] Git repository setup
- [x] Basic project structure (monorepo)
- [x] TypeScript configuration
- [x] CI/CD pipeline (GitHub Actions)
- [x] Scout service foundation
- [x] File-based SKU monitoring
- [x] Basic stock checking for Walmart & Best Buy

### 🔄 Current Capabilities
- Monitors SKUs from `skus.json` file
- Checks stock every 30 seconds (with jitter)
- Supports Walmart and Best Buy (basic HTML scraping)
- Auto-reloads when SKU file changes
- Logs stock alerts to console

## 📋 Development Roadmap

### Phase 1: Enhanced Scout (Next - 2 weeks)
- [ ] Better stock detection algorithms
- [ ] Proxy rotation support
- [ ] Rate limiting and anti-detection
- [ ] JSON API endpoints for faster checking
- [ ] Error handling and retry logic

### Phase 2: Purchasing Agents (2 weeks)
- [ ] Basic HTTP checkout automation
- [ ] Account management system
- [ ] Simple queue system (Redis or in-memory)

### Phase 3: Advanced Features (2 weeks)
- [ ] CAPTCHA solving integration
- [ ] Headless browser automation (Playwright)
- [ ] Stealth techniques

### Phase 4: Additional Sites (3 weeks)
- [ ] Costco support
- [ ] Pokémon Center support (hard)
- [ ] Target support (very hard)

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+ 
- npm 9+

### Quick Start

1. **Clone and install:**
   ```bash
   git clone <your-repo-url>
   cd pokebot
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Update SKUs:**
   Edit `skus.json` with the products you want to monitor:
   ```json
   {
     "walmart": [
       {
         "sku": "123456789",
         "name": "Pokemon TCG: Elite Trainer Box",
         "url": "https://www.walmart.com/ip/123456789",
         "price_limit": 60.00
       }
     ]
   }
   ```

4. **Run the scout:**
   ```bash
   cd services/scout
   npm install
   npm run dev
   ```

## 📁 Project Structure

```
pokebot/
├── .github/workflows/     # CI/CD pipelines
├── services/
│   ├── scout/            # Stock monitoring service ✅
│   ├── agents/           # Purchasing agents (Phase 2)
│   ├── account-manager/  # Account/proxy management (Phase 2)
│   └── shared/           # Shared utilities (Phase 2)
├── skus.json            # Products to monitor ✅
├── .env.example         # Environment template ✅
└── README.md           # This file ✅
```

## 🎮 Usage

### Running the Scout
```bash
cd services/scout
npm run dev
```

The scout will:
1. Load SKUs from `skus.json`
2. Start monitoring each product every 30 seconds
3. Log stock alerts when items become available
4. Auto-reload if you update the SKU file

### Example Output
```
🤖 Pokebot Scout starting up...
📋 Loaded SKUs: walmart: 1 items, bestbuy: 1 items
🚀 Starting stock monitoring...
📊 walmart - Pokemon TCG: Elite Trainer Box: Out of stock
📊 bestbuy - Pokemon TCG: Premium Collection: Out of stock
🚨 STOCK ALERT: Pokemon TCG: Elite Trainer Box is IN STOCK at walmart!
   URL: https://www.walmart.com/ip/123456789
   Price Limit: $60.00
```

## 🔧 Configuration

### Environment Variables
- `NODE_ENV`: development/production
- `PROXY_USERNAME/PASSWORD/ENDPOINT`: Proxy settings (Phase 1)
- `TWOCAPTCHA_API_KEY`: CAPTCHA solver (Phase 3)

### SKU File Format
```json
{
  "retailer_name": [
    {
      "sku": "product_id",
      "name": "Human readable name",
      "url": "Direct product URL",
      "price_limit": 99.99
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm test`
5. Submit a pull request

## ⚠️ Legal Notice

This bot is for educational purposes. Always respect retailers' Terms of Service and rate limits. Use responsibly.

## 📈 Performance Notes

- Current polling: 30 seconds + random jitter
- Memory usage: ~50MB for scout service
- Network: ~1 request per SKU per 30 seconds

## 🐛 Known Issues

- Basic HTML scraping may break if sites change
- No proxy rotation yet (Phase 1)
- No CAPTCHA handling (Phase 3)
- Limited error recovery

## 📞 Support

- Create an issue for bugs
- Check the roadmap for planned features
- See `docs/` for detailed architecture info (coming soon)

---

**Current Phase**: 0 Complete ✅ | **Next**: Phase 1 Enhanced Scout
