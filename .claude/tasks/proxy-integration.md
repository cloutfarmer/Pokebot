# Proxy Integration Task

## Overview
Implement a comprehensive proxy management system supporting residential, mobile, and datacenter proxies with intelligent rotation, health monitoring, and geographic distribution.

## Proxy Architecture

### Proxy Hierarchy
```
ProxyManager
├── Proxy Providers
│   ├── PacketStream (Residential - Primary)
│   ├── Bright Data (Premium Residential)
│   ├── IPRoyal (Budget Residential)
│   ├── Soax (Mobile 4G/5G)
│   └── Private Datacenter (Backup)
├── Proxy Pool (100+ IPs)
├── Health Monitor
├── Geographic Rotator
└── Session Manager
```

### Browser-Proxy Assignment
```
30 Browser Instances:
├── 10 instances: Direct connection (home IP)
├── 8 instances: PacketStream residential
├── 5 instances: Bright Data premium
├── 4 instances: Mobile proxies
└── 3 instances: Datacenter backup
```

## Implementation Tasks

### 1. Proxy Manager Core (`src/core/proxy_manager.py`)
- [ ] Create `ProxyManager` class with provider abstraction
- [ ] Implement proxy pool with 100+ rotating IPs
- [ ] Add health checking (response time, success rate)
- [ ] Create automatic failover system
- [ ] Implement sticky sessions per browser

### 2. Provider Integrations
```python
class ProxyProvider(ABC):
    @abstractmethod
    async def get_proxy(self) -> Proxy
    
    @abstractmethod
    async def report_failure(self, proxy: Proxy)
    
    @abstractmethod
    async def refresh_pool(self)

# Implement for each provider:
- PacketStreamProvider
- BrightDataProvider  
- IPRoyalProvider
- SoaxMobileProvider
- DatacenterProvider
```

### 3. Proxy Configuration
```json
{
  "proxy_config": {
    "providers": {
      "packetstream": {
        "enabled": true,
        "api_key": "${PACKETSTREAM_API_KEY}",
        "bandwidth_gb": 100,
        "sticky_session_minutes": 30
      },
      "bright_data": {
        "enabled": true,
        "username": "${BRIGHTDATA_USER}",
        "password": "${BRIGHTDATA_PASS}",
        "zone": "residential_premium"
      },
      "iproyal": {
        "enabled": true,
        "api_key": "${IPROYAL_API_KEY}",
        "country": "US",
        "state_targeting": true
      },
      "soax": {
        "enabled": false,
        "package": "mobile_5g",
        "rotation_interval": 600
      }
    },
    "distribution": {
      "geographic_spread": true,
      "preferred_states": ["CA", "TX", "NY", "FL", "IL"],
      "avoid_datacenter_asn": true
    }
  }
}
```

### 4. Proxy Health Monitoring
- [ ] Track per-proxy metrics:
  - Response time
  - Success/failure rate
  - Ban detection
  - Geographic location
  - ASN type
- [ ] Implement scoring algorithm (0-100)
- [ ] Auto-blacklist failing proxies
- [ ] Alert on proxy pool depletion

### 5. Geographic Distribution
```python
class GeographicRotator:
    def assign_proxy(self, browser_id: str) -> Proxy:
        # Ensure browsers use different:
        # - States
        # - Cities  
        # - ISPs
        # - ASN types
        # Maintain mapping for consistency
```

### 6. Session Persistence
- [ ] Implement sticky proxy sessions (30 min minimum)
- [ ] Store proxy-browser mappings
- [ ] Handle proxy rotation on failure only
- [ ] Maintain session cookies per proxy

### 7. Cost Optimization
```python
class CostOptimizer:
    # Use proxies efficiently:
    # - PacketStream for general monitoring ($1/GB)
    # - Bright Data for difficult detections ($15/GB)
    # - Mobile for Pokemon Center ($30/GB)
    # - Direct connection when safe
    
    def select_proxy_tier(self, retailer: str, failure_count: int) -> ProxyTier
```

## Testing Strategy

### 1. Proxy Validation
- Test 100 proxies concurrently
- Verify geographic distribution
- Confirm unique IPs
- Check residential vs datacenter

### 2. Rotation Testing
- Simulate proxy failures
- Verify automatic failover
- Test session persistence
- Validate cost tracking

### 3. Performance Benchmarks
- Proxy assignment: < 100ms
- Health check cycle: < 60s
- Pool refresh: < 5 minutes
- Memory usage: < 1GB

## Integration Points

### With Browser Pool
```python
browser = browser_pool.get_browser()
proxy = proxy_manager.get_proxy_for_browser(browser.id)
await browser.set_proxy(proxy)
```

### With Monitoring Service
```python
# Escalate proxy tier on failures
if monitor.consecutive_failures > 3:
    proxy_manager.upgrade_proxy_tier(monitor.browser_id)
```

## Budget Management
- Set monthly limits per provider
- Track bandwidth usage in real-time
- Alert at 80% budget consumption
- Automatic fallback to cheaper tiers

## Security Considerations
- Store proxy credentials encrypted
- Rotate API keys monthly
- Use separate proxy pools per retailer
- Never log full proxy URLs
- Implement proxy authentication

## Success Metrics
- 99%+ proxy availability
- < 5% detection rate
- Geographic coverage: 20+ states
- Cost per check: < $0.001
- Zero proxy leaks