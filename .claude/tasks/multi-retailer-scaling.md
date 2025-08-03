# Multi-Retailer Scaling Task

## Overview
Scale the monitoring system to handle 5+ major retailers simultaneously, each with different anti-bot protections and monitoring requirements.

## Retailer Difficulty Levels

### Tier 1 - Easy (Basic Protection)
- **Best Buy** ✅ (Currently implemented)
- **GameStop** (Minimal protection)

### Tier 2 - Moderate (Standard Protection)
- **Target** (Shape Security)
- **Walmart** (PerimeterX basic)

### Tier 3 - Hard (Advanced Protection)
- **Pokemon Center** (DataDome + Incapsula + hCaptcha)
- **Costco** (Membership + PerimeterX)

### Tier 4 - Expert (Multiple Layers)
- **Amazon** (AWS WAF + Custom)
- **Apple** (Device verification)

## Architecture

### Multi-Retailer System Design
```
┌─────────────────────────────────┐
│    Orchestration Engine         │
│  (Manages all retailer agents)  │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼───────┐ ┌──────▼──────┐
│ Retailer  │ │  Retailer   │
│ Registry  │ │  Scheduler  │
└───────────┘ └─────────────┘
        │
┌───────┴──────────────────┐
│                          │
▼                          ▼
Retailer Agents         Browser Pool
├── BestBuyAgent          (30 instances)
├── TargetAgent              │
├── WalmartAgent       ◄─────┘
├── PokemonCenterAgent
└── CostcoAgent
```

## Implementation Tasks

### 1. Base Retailer Agent (`src/agents/base_agent.py`)
```python
class BaseRetailerAgent(ABC):
    @abstractmethod
    async def check_availability(self, sku: str) -> AvailabilityResult
    
    @abstractmethod
    async def add_to_cart(self, sku: str) -> bool
    
    @abstractmethod
    async def handle_queue(self) -> bool
    
    @abstractmethod
    async def handle_captcha(self) -> bool
    
    @abstractmethod
    def get_required_proxy_tier(self) -> ProxyTier
```

### 2. Target Implementation (`src/agents/target_agent.py`)
- [ ] Handle Shape Security protection
- [ ] Implement Circle membership detection
- [ ] Parse Target's React-based product data
- [ ] Handle "Notify Me" vs "Add to Cart"
- [ ] Implement store pickup options

**Target-Specific Challenges:**
- Shape Security bot detection
- Dynamic API endpoints
- Store inventory API
- Circle member pricing

### 3. Walmart Implementation (`src/agents/walmart_agent.py`)
- [ ] Bypass PerimeterX protection
- [ ] Handle Walmart+ membership
- [ ] Parse product API responses
- [ ] Implement affiliate bypass
- [ ] Handle IP-based store selection

**Walmart-Specific Challenges:**
- PerimeterX with sensor data
- Captcha on suspicious activity
- Regional inventory
- Spark delivery integration

### 4. Pokemon Center (`src/agents/pokemoncenter_agent.py`)
- [ ] Bypass DataDome protection
- [ ] Handle Incapsula challenges
- [ ] Solve hCaptcha when required
- [ ] Manage queue system
- [ ] Handle member-exclusive releases

**Pokemon Center Challenges:**
- Triple-layer protection
- Member-only products
- Extreme rate limiting
- Queue randomization

### 5. Costco Implementation (`src/agents/costco_agent.py`)
- [ ] Handle membership verification
- [ ] Bypass basic PerimeterX
- [ ] Parse warehouse availability
- [ ] Implement guest checkout
- [ ] Handle business vs personal accounts

### 6. Retailer Configuration Schema
```json
{
  "retailers": {
    "target": {
      "enabled": true,
      "base_url": "https://www.target.com",
      "api_endpoints": {
        "product": "/redsky/v3/pdp/tcin/{sku}",
        "availability": "/fulfillment_aggregator/v1/fiats/{sku}"
      },
      "protections": ["shape_security"],
      "proxy_tier": "residential",
      "check_interval": 15,
      "priority_skus": []
    },
    "walmart": {
      "enabled": true,
      "protections": ["perimeterx", "captcha"],
      "proxy_tier": "residential_premium",
      "requires_account": false
    },
    "pokemoncenter": {
      "enabled": false,
      "protections": ["datadome", "incapsula", "hcaptcha"],
      "proxy_tier": "mobile",
      "requires_account": true,
      "member_only": true
    }
  }
}
```

### 7. Orchestration Engine
```python
class RetailerOrchestrator:
    def __init__(self):
        self.agents = {}
        self.scheduler = RetailerScheduler()
        self.browser_pool = BrowserPool()
        self.proxy_manager = ProxyManager()
    
    async def monitor_all_retailers(self):
        # Distribute SKUs across retailers
        # Assign browsers from pool
        # Manage check intervals
        # Handle failures and retries
```

### 8. Cross-Retailer Features
- [ ] Unified SKU format handling
- [ ] Price comparison across retailers
- [ ] Availability aggregation
- [ ] Intelligent failover (if one fails, try another)
- [ ] Bundle detection (multi-item sets)

## Testing Strategy

### Per-Retailer Testing
1. **Proxy Requirements**: Test minimum proxy tier needed
2. **Rate Limits**: Find optimal check frequency
3. **Detection**: Monitor for blocks/captchas
4. **Accuracy**: Verify availability detection
5. **Speed**: Measure response times

### Integration Testing
1. Run all 5 retailers simultaneously
2. Monitor resource usage (CPU, memory, bandwidth)
3. Test failover between retailers
4. Verify no cross-contamination
5. Check alert deduplication

## Scalability Considerations

### Resource Allocation
```
Best Buy:     4 browsers, basic proxies
Target:       6 browsers, residential proxies  
Walmart:      6 browsers, premium proxies
Pokemon Ctr:  8 browsers, mobile proxies
Costco:       6 browsers, residential proxies
─────────────────────────────────────────
Total:       30 browsers, mixed proxies
```

### Performance Targets
- Monitor 50+ SKUs across all retailers
- < 10 second detection latency
- 95%+ uptime per retailer
- < 1% false positive rate
- Automatic failure recovery

## Rollout Plan

### Phase 1: Target (Week 1)
- Implement Shape Security bypass
- Test with 5 high-demand SKUs
- Optimize check frequency

### Phase 2: Walmart (Week 1-2)
- Implement PerimeterX bypass
- Add captcha handling
- Test regional availability

### Phase 3: Pokemon Center (Week 2-3)
- Research protection layers
- Implement member authentication
- Test with exclusive releases

### Phase 4: Integration (Week 3)
- Combine all retailers
- Implement orchestration
- Deploy monitoring dashboard

## Success Metrics
- All 5 retailers operational
- < 5% detection rate per retailer
- Instant cross-retailer alerts
- Unified monitoring interface
- Cost < $0.01 per check