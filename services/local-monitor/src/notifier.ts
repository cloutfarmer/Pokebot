import { StockResult } from './retailers/bestbuy';
import { FileLogger, MonitorStatus, StoreInfo, ProductFind } from './file-logger';

export interface NotificationConfig {
  console: boolean;
  email: boolean;
  webhook: boolean;
}

export class Notifier {
  private config: NotificationConfig;
  private fileLogger: FileLogger;
  private stores: Map<string, StoreInfo> = new Map();

  constructor(config: NotificationConfig) {
    this.config = config;
    this.fileLogger = new FileLogger();
  }

  async sendStockAlert(results: StockResult[]): Promise<void> {
    // Update store tracking for all results
    this.updateStoreTracking(results);
    
    const stockFound = results.filter(result => result.hasStock);
    
    if (stockFound.length > 0) {
      // Record all product finds
      this.recordProductFinds(stockFound);
      
      if (this.config.console) {
        this.sendConsoleAlert(stockFound);
      }

      if (this.config.email) {
        await this.sendEmailAlert(stockFound);
      }

      if (this.config.webhook) {
        await this.sendWebhookAlert(stockFound);
      }
    }
  }

  private sendConsoleAlert(results: StockResult[]): void {
    console.log('\n' + '='.repeat(60));
    console.log('🚨 LOCAL POKEMON STOCK ALERT! 🚨');
    console.log('='.repeat(60));
    
    results.forEach(result => {
      const store = result.store;
      console.log(`\n📍 ${store.retailer.toUpperCase()} - ${store.name}`);
      console.log(`   Distance: ${store.distance} miles`);
      console.log(`   Address: ${store.address}, ${store.city}, ${store.state} ${store.zip}`);
      console.log(`   Phone: ${store.phone}`);
      console.log(`   Hours: ${store.hours}`);
      
      console.log(`\n   🎮 Products Found:`);
      result.products.forEach(product => {
        console.log(`      • ${product.name}`);
        if (product.price) console.log(`        💰 ${product.price}`);
        console.log(`        📦 ${product.availability}`);
        if (product.url) console.log(`        🔗 ${product.url}`);
      });
      
      console.log(`   ⏰ Last checked: ${result.lastChecked.toLocaleTimeString()}`);
      console.log('-'.repeat(50));
    });
    
    console.log('\n🏃‍♂️ Better hurry - local stock moves fast!');
    console.log('='.repeat(60) + '\n');
  }

  private async sendEmailAlert(results: StockResult[]): Promise<void> {
    // TODO: Implement email notifications
    // Could use nodemailer or similar
    console.log(`📧 Email notifications not implemented yet (${results.length} results)`);
  }

  private async sendWebhookAlert(results: StockResult[]): Promise<void> {
    // TODO: Implement webhook notifications (Discord, Slack, etc.)
    console.log(`🔗 Webhook notifications not implemented yet (${results.length} results)`);
  }

  sendStatusUpdate(message: string): void {
    this.fileLogger.log('info', message);
  }

  sendError(error: string): void {
    this.fileLogger.log('error', error);
  }

  private updateStoreTracking(results: StockResult[]): void {
    for (const result of results) {
      const store = result.store;
      const storeKey = `${store.retailer}-${store.id}`;
      
      if (this.stores.has(storeKey)) {
        const storeInfo = this.stores.get(storeKey)!;
        storeInfo.lastChecked = new Date().toISOString();
        storeInfo.totalChecks += 1;
        if (result.hasStock || result.products.length > 0) {
          storeInfo.successfulChecks += 1;
        }
        this.stores.set(storeKey, storeInfo);
      } else {
        const storeInfo: StoreInfo = {
          id: store.id,
          name: store.name,
          retailer: store.retailer,
          distance: store.distance || 0,
          address: store.address || '',
          city: store.city || '',
          state: store.state || '',
          zip: store.zip || '',
          phone: store.phone,
          hours: store.hours,
          lastChecked: new Date().toISOString(),
          totalChecks: 1,
          successfulChecks: result.hasStock ? 1 : 0
        };
        this.stores.set(storeKey, storeInfo);
      }
    }
    
    // Update stores file
    this.fileLogger.updateStores(Array.from(this.stores.values()));
  }

  private recordProductFinds(stockResults: StockResult[]): void {
    for (const result of stockResults) {
      for (const product of result.products) {
        const productFind: ProductFind = {
          timestamp: new Date().toISOString(),
          product: {
            name: product.name,
            price: product.price,
            availability: product.availability,
            url: product.url,
            sku: product.sku
          },
          store: {
            id: result.store.id,
            name: result.store.name,
            retailer: result.store.retailer,
            distance: result.store.distance || 0,
            address: result.store.address || ''
          }
        };
        
        this.fileLogger.recordProductFind(productFind);
        this.fileLogger.log('success', `Pokemon product found: ${product.name} at ${result.store.name}`, productFind);
      }
    }
  }

  public updateMonitorStatus(config: any, isRunning: boolean): void {
    const status: MonitorStatus = {
      isRunning,
      lastCheck: new Date().toISOString(),
      config: {
        zipCodes: config.zip_codes || [],
        radiusMiles: config.radius_miles || 0,
        checkIntervalMinutes: config.check_interval_minutes || 0,
        enabledRetailers: Object.keys(config.retailers || {}).filter(retailer => 
          config.retailers[retailer]?.enabled
        )
      },
      uptime: process.uptime()
    };
    
    this.fileLogger.updateStatus(status);
  }

  public generateSummary(): void {
    this.fileLogger.writeSummaryToFile();
  }
}
