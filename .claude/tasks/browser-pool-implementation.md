# Browser Pool Implementation Task

## Overview
Implement a sophisticated browser pool management system that maintains 20-30 browser instances for distributed monitoring, avoiding detection through intelligent rotation and behavioral diversity.

## Architecture

### Core Components
```
BrowserPool
├── Pool Manager (orchestrates all browsers)
├── Browser Instances (20-30 profiles)
├── Health Monitor (tracks browser performance)
├── Session Warmer (maintains activity)
└── Assignment Engine (distributes work)
```

## Implementation Tasks

### 1. Browser Pool Manager (`src/core/browser_pool.py`)
- [ ] Create `BrowserPool` class with configurable size (20-30 instances)
- [ ] Implement round-robin assignment algorithm
- [ ] Add health checking for each browser instance
- [ ] Create auto-restart mechanism for failed browsers
- [ ] Implement browser warmup on initialization

### 2. Browser Profile Generation
- [ ] Generate unique profiles with varied:
  - User agents (desktop Chrome/Firefox/Edge)
  - Screen resolutions (1920x1080, 1366x768, 1440x900)
  - Timezone settings (US timezones)
  - Language preferences
  - Canvas fingerprints
- [ ] Store profiles in `browser-profiles/pool/`
- [ ] Implement profile rotation every 24 hours

### 3. Session Persistence & Warming
- [ ] Keep browsers "warm" with periodic activity:
  - Browse Best Buy homepage every 10-15 minutes
  - Search for random electronics
  - View 2-3 random product pages
  - Add/remove items from saved lists
- [ ] Maintain cookies and session data
- [ ] Implement natural browsing patterns

### 4. Intelligent Work Distribution
```python
class BrowserAssignment:
    def get_browser(self, retailer: str, priority: str) -> Browser:
        # Factors to consider:
        # - Browser health score
        # - Recent activity on retailer
        # - Time since last check
        # - Current load
        # - Proxy assignment
```

### 5. Browser Instance Configuration
Each browser should have:
- Unique profile directory
- Persistent storage
- WebRTC leak prevention
- WebGL spoofing
- Audio context fingerprinting
- Font enumeration blocking

### 6. Performance Monitoring
- [ ] Track metrics per browser:
  - Success rate
  - Average response time
  - Detection/block count
  - Uptime
- [ ] Implement scoring system (0-100)
- [ ] Auto-retire low-performing browsers

## Configuration Schema
```json
{
  "browser_pool": {
    "min_size": 20,
    "max_size": 30,
    "warmup_interval_seconds": 600,
    "health_check_interval": 300,
    "profile_rotation_hours": 24,
    "browsers": {
      "chrome": 70,  // percentage
      "firefox": 20,
      "edge": 10
    }
  }
}
```

## Testing Requirements
1. Load test with 30 concurrent browsers
2. Verify memory usage stays under 16GB
3. Test failover when browsers crash
4. Validate unique fingerprints
5. Confirm session persistence

## Success Metrics
- Pool maintains 95%+ uptime
- < 2 second browser assignment time
- Zero duplicate fingerprints
- Successful warmup activities
- No memory leaks over 24 hours

## Integration Points
- Proxy Manager (assign proxies to browsers)
- Monitoring Service (receive work assignments)
- Alert Service (report availability)
- Airtable Logger (track performance)