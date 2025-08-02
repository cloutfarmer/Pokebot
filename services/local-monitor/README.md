# Local Pokemon Monitor Service

A specialized service for monitoring local retail stores for Pokemon Trading Card Game products. This service checks physical store locations within a specified radius for in-stock Pokemon products and sends alerts when items are found.

## Features

- **Multi-Retailer Support**: Currently supports Best Buy with framework for Target, Walgreens, and GameStop
- **Geographic Targeting**: Monitor stores within a specified radius of ZIP codes
- **Real-time Notifications**: Console alerts with detailed store and product information
- **Configurable Monitoring**: Customizable check intervals and search terms
- **Mock Data Testing**: Includes simulation mode for testing without hitting real APIs

## Architecture

```
Local Monitor Service
├── Store Locator (finds nearby stores)
├── Retailer Monitors (check inventory at specific stores)
│   └── Best Buy Monitor (implemented)
│   └── Target Monitor (TODO)
│   └── Walgreens Monitor (TODO)
└── Notifier (sends alerts)
    ├── Console notifications ✅
    ├── Email notifications (TODO)
    └── Webhook notifications (TODO)
```

## Configuration

Edit `config/local-config.json` to customize:

```json
{
  "zip_codes": ["07748", "10001"],
  "radius_miles": 25,
  "check_interval_minutes": 15,
  "retailers": {
    "bestbuy": {
      "enabled": true,
      "search_terms": ["pokemon", "trading card game", "tcg"]
    }
  },
  "notifications": {
    "console": true,
    "email": false,
    "webhook": false
  }
}
```

## Installation & Usage

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Run production build
npm start
```

## Sample Output

When Pokemon products are found, you'll see alerts like:

```
============================================================
🚨 LOCAL POKEMON STOCK ALERT! 🚨
============================================================

📍 BESTBUY - Holmdel
   Distance: 1.5 miles
   Address: 2130 State Route 35, Holmdel, NJ 07733
   Phone: (732) 946-1500
   Hours: Opens at 10 am

   🎮 Products Found:
      • Pokemon Trading Card Game: Scarlet & Violet Elite Trainer Box
        💰 $49.99
        📦 Available for pickup today
        🔗 https://www.bestbuy.com/site/pokemon-tcg/12345
--------------------------------------------------
   ⏰ Last checked: 8:43:40 AM

🏃‍♂️ Better hurry - local stock moves fast!
============================================================
```

## Development Roadmap

### Phase 1: Foundation ✅
- [x] Basic service architecture
- [x] Store locator with mock data
- [x] Best Buy monitor with simulation
- [x] Console notifications
- [x] Configuration system

### Phase 2: Real API Integration (Next)
- [ ] Implement actual Best Buy store locator API
- [ ] Implement Best Buy inventory checking API
- [ ] Add proxy support for API calls
- [ ] Add rate limiting and retry logic

### Phase 3: Additional Retailers
- [ ] Target store locator and inventory
- [ ] Walgreens store locator and inventory  
- [ ] GameStop store locator and inventory
- [ ] CVS/Pharmacy support

### Phase 4: Enhanced Notifications
- [ ] Email notifications (nodemailer)
- [ ] Discord webhook integration
- [ ] Slack webhook integration
- [ ] SMS notifications (Twilio)

### Phase 5: Advanced Features
- [ ] Web dashboard for monitoring
- [ ] Historical stock tracking
- [ ] Price tracking and alerts
- [ ] Product image recognition
- [ ] Mobile app notifications

## API Integration Notes

### Best Buy
- Store Locator: Need to reverse engineer their store finder API
- Inventory: Look for store-specific product availability endpoints
- Rate Limits: Unknown, will need testing with proxies

### Target
- Store Locator: `https://api.target.com/store_locators/v2/stores`
- Inventory: Store-specific TCIN (Target.com Item Number) lookups
- Anti-Bot: Shape Security makes this challenging

### Walgreens
- Store Locator: `https://www.walgreens.com/locator/walgreens-*.html`
- Inventory: Limited Pokemon selection, mainly at pharmacy counters
- Difficulty: Low, basic HTML scraping

## Technical Details

### File Structure
```
src/
├── index.ts              # Main service entry point
├── store-locator.ts      # Geographic store finding
├── notifier.ts          # Alert system
└── retailers/
    └── bestbuy.ts       # Best Buy specific logic
```

### Key Classes

- **LocalMonitorService**: Main orchestrator
- **StoreLocator**: Finds stores by ZIP code and radius
- **BestBuyMonitor**: Checks Best Buy store inventory
- **Notifier**: Handles all alert types

### Mock Data
Currently uses realistic mock data for:
- Store locations in NJ area (ZIP 07748)
- Pokemon product names and prices
- Store hours and contact info
- Random stock simulation (30% chance of finding items)

## Contributing

1. Add new retailer monitors in `src/retailers/`
2. Implement the retailer interface with `checkStoreInventory()` method
3. Add retailer configuration to `local-config.json`
4. Update the main service to include the new retailer

## Security Considerations

- Use residential proxies for API calls
- Implement request delays to avoid rate limiting
- Rotate user agents and headers
- Consider legal implications of automated store checking
- Respect robots.txt and terms of service

## Performance

- Parallel store checking with controlled concurrency
- Configurable delays between requests
- Efficient mock data for testing
- Memory-efficient result processing

This service provides the foundation for local Pokemon card monitoring and can be extended to support additional retailers and notification methods as needed.
