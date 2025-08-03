# Alert Infrastructure Task

## Overview
Build a real-time alert system that delivers instant notifications across multiple channels (WebSocket, Discord, SMS, Mobile Push) with sub-second latency from detection to notification.

## Alert Architecture

### System Components
```
Detection Engine
     │
     ▼
Alert Service (WebSocket Server)
     │
     ├─── Priority Queue
     │      (High/Medium/Low)
     │
     ├─── Alert Router
     │      │
     │      ├── Discord Webhook
     │      ├── SMS (Twilio)
     │      ├── Push (Firebase)
     │      ├── Email (SendGrid)
     │      └── WebSocket Clients
     │
     └─── Alert History
           (Airtable/Redis)
```

## Implementation Tasks

### 1. WebSocket Alert Server (`src/core/alert_service.py`)
```python
class AlertService:
    def __init__(self):
        self.websocket_server = WebSocketServer(port=8765)
        self.alert_queue = PriorityQueue()
        self.channels = {
            'discord': DiscordChannel(),
            'sms': TwilioChannel(),
            'push': FirebaseChannel(),
            'email': SendGridChannel()
        }
```

- [ ] Implement WebSocket server with Socket.io
- [ ] Create priority queue for alerts
- [ ] Add channel subscription management
- [ ] Implement retry logic for failed alerts
- [ ] Add rate limiting per channel

### 2. Alert Types & Priority
```python
class AlertType(Enum):
    IN_STOCK = "in_stock"          # Highest priority
    PRICE_DROP = "price_drop"       # High priority
    RESTOCK_SOON = "restock_soon"   # Medium priority
    BACK_ORDER = "back_order"       # Low priority

class Alert:
    id: str
    type: AlertType
    priority: int  # 1-10
    sku: str
    product_name: str
    retailer: str
    price: float
    url: str
    timestamp: datetime
    metadata: dict
```

### 3. Discord Integration
- [ ] Rich embed messages with product images
- [ ] Retailer-specific webhooks
- [ ] @everyone mentions for high-priority
- [ ] Stock status color coding
- [ ] Direct purchase links

```python
async def send_discord_alert(alert: Alert):
    embed = discord.Embed(
        title=f"🚨 {alert.product_name} IN STOCK!",
        color=0x00ff00,
        url=alert.url
    )
    embed.add_field("Price", f"${alert.price}")
    embed.add_field("Retailer", alert.retailer)
    embed.set_thumbnail(url=alert.metadata.get('image_url'))
    embed.set_footer(text=f"Detected at {alert.timestamp}")
```

### 4. SMS Alerts (Twilio)
- [ ] Configure Twilio API
- [ ] Implement phone number verification
- [ ] Create SMS templates
- [ ] Add opt-in/opt-out system
- [ ] Track delivery status

```python
class TwilioChannel:
    async def send_alert(self, alert: Alert, recipients: List[str]):
        message = f"🚨 {alert.product_name} available at {alert.retailer}! ${alert.price} - {alert.url}"
        # Send to verified numbers only
        # Track delivery status
        # Handle failures
```

### 5. Mobile Push Notifications (Firebase)
- [ ] Set up Firebase Cloud Messaging
- [ ] Implement device registration
- [ ] Create notification templates
- [ ] Add deep linking to retailer apps
- [ ] Implement notification grouping

### 6. Real-time Dashboard
```html
<!-- WebSocket Client Dashboard -->
<div id="alert-dashboard">
    <div class="active-monitors">
        <!-- Show all monitored SKUs -->
    </div>
    <div class="recent-alerts">
        <!-- Live alert feed -->
    </div>
    <div class="statistics">
        <!-- Success rate, response time -->
    </div>
</div>
```

### 7. Alert Configuration
```json
{
  "alerts": {
    "channels": {
      "discord": {
        "enabled": true,
        "webhooks": {
          "high_priority": "${DISCORD_WEBHOOK_HIGH}",
          "general": "${DISCORD_WEBHOOK_GENERAL}"
        },
        "rate_limit": 10
      },
      "sms": {
        "enabled": true,
        "twilio_sid": "${TWILIO_SID}",
        "twilio_auth": "${TWILIO_AUTH}",
        "from_number": "+1234567890",
        "max_recipients": 5
      },
      "push": {
        "enabled": false,
        "firebase_config": "firebase.json"
      }
    },
    "filters": {
      "min_price_drop_percent": 10,
      "excluded_retailers": [],
      "priority_skus": ["6634940", "6632394"]
    }
  }
}
```

### 8. Alert Deduplication
```python
class AlertDeduplicator:
    def __init__(self):
        self.sent_alerts = TTLCache(maxsize=1000, ttl=3600)
    
    def should_send(self, alert: Alert) -> bool:
        # Check if similar alert sent recently
        # Consider: SKU, retailer, price
        # Allow re-alerts after cooldown
```

### 9. Performance Requirements
- **Latency**: < 1 second from detection to notification
- **Throughput**: Handle 100+ alerts per second
- **Reliability**: 99.9% delivery rate
- **Scalability**: Support 1000+ WebSocket connections

### 10. Alert Analytics
- [ ] Track alert-to-purchase conversion
- [ ] Monitor channel performance
- [ ] Analyze response times
- [ ] Report failed deliveries
- [ ] Calculate ROI per channel

## Testing Strategy

### Load Testing
1. Simulate 100 simultaneous stock alerts
2. Verify all channels receive alerts
3. Measure end-to-end latency
4. Test deduplication logic
5. Verify priority ordering

### Channel Testing
- Discord: Test webhooks, rate limits
- SMS: Verify delivery, costs
- Push: Test on iOS/Android
- WebSocket: Test reconnection

### Failure Scenarios
1. Channel unavailable
2. Rate limit exceeded
3. Network interruption
4. Queue overflow
5. Invalid configuration

## Integration Points

### From Monitor Service
```python
# When stock detected
await alert_service.send_alert(
    type=AlertType.IN_STOCK,
    sku=sku,
    retailer="bestbuy",
    price=49.99,
    priority=9
)
```

### To Airtable
```python
# Log all alerts for analytics
await airtable.log_alert(
    alert_id=alert.id,
    sent_channels=["discord", "sms"],
    delivery_status="success"
)
```

## Success Metrics
- Alert latency: < 1 second
- Delivery rate: > 99%
- Zero duplicate alerts
- Channel uptime: > 99.9%
- User satisfaction: > 90%

## Future Enhancements
- Voice calls for ultra-high priority
- Telegram bot integration
- Slack workspace alerts
- IFTTT/Zapier webhooks
- Custom alert sounds