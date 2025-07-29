import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';
import * as chokidar from 'chokidar';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

interface SKUItem {
  sku: string;
  name: string;
  url: string;
  price_limit: number;
}

interface SKUConfig {
  [retailer: string]: SKUItem[];
}

class Scout {
  private skuConfig: SKUConfig = {};
  private skuFilePath: string;
  private isRunning = false;
  private intervals: Map<string, NodeJS.Timeout> = new Map();

  constructor(skuFilePath: string = '../../../skus.json') {
    this.skuFilePath = path.resolve(__dirname, skuFilePath);
    this.loadSKUs();
    this.watchSKUFile();
  }

  private loadSKUs(): void {
    try {
      const data = fs.readFileSync(this.skuFilePath, 'utf8');
      this.skuConfig = JSON.parse(data);
      console.log('📋 Loaded SKUs:', Object.keys(this.skuConfig).map(retailer => 
        `${retailer}: ${this.skuConfig[retailer].length} items`
      ).join(', '));
    } catch (error) {
      console.error('❌ Error loading SKU file:', error);
      this.skuConfig = {};
    }
  }

  private watchSKUFile(): void {
    const watcher = chokidar.watch(this.skuFilePath);
    watcher.on('change', () => {
      console.log('📝 SKU file changed, reloading...');
      this.loadSKUs();
      this.restartMonitoring();
    });
  }

  private async checkWalmartStock(item: SKUItem): Promise<boolean> {
    try {
      // Simple HTML scraping approach for now
      const response = await axios.get(item.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        },
        timeout: 10000
      });

      // Look for common out-of-stock indicators
      const html = response.data.toLowerCase();
      const outOfStockIndicators = [
        'out of stock',
        'currently unavailable',
        'not available',
        'sold out'
      ];

      const isOutOfStock = outOfStockIndicators.some(indicator => 
        html.includes(indicator)
      );

      return !isOutOfStock;
    } catch (error) {
      console.error(`❌ Error checking Walmart stock for ${item.name}:`, error.message);
      return false;
    }
  }

  private async checkBestBuyStock(item: SKUItem): Promise<boolean> {
    try {
      const response = await axios.get(item.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        },
        timeout: 10000
      });

      const html = response.data.toLowerCase();
      const outOfStockIndicators = [
        'sold out',
        'currently unavailable',
        'not available online',
        'coming soon'
      ];

      const isOutOfStock = outOfStockIndicators.some(indicator => 
        html.includes(indicator)
      );

      return !isOutOfStock;
    } catch (error) {
      console.error(`❌ Error checking Best Buy stock for ${item.name}:`, error.message);
      return false;
    }
  }

  private async checkStock(retailer: string, item: SKUItem): Promise<void> {
    let inStock = false;

    switch (retailer.toLowerCase()) {
      case 'walmart':
        inStock = await this.checkWalmartStock(item);
        break;
      case 'bestbuy':
        inStock = await this.checkBestBuyStock(item);
        break;
      default:
        console.warn(`⚠️ Unknown retailer: ${retailer}`);
        return;
    }

    if (inStock) {
      console.log(`🚨 STOCK ALERT: ${item.name} is IN STOCK at ${retailer}!`);
      console.log(`   URL: ${item.url}`);
      console.log(`   Price Limit: $${item.price_limit}`);
      
      // Here we would normally emit to a queue for purchasing agents
      // For now, just log the alert
    } else {
      console.log(`📊 ${retailer} - ${item.name}: Out of stock`);
    }
  }

  private startMonitoring(): void {
    if (this.isRunning) return;

    console.log('🚀 Starting stock monitoring...');
    this.isRunning = true;

    for (const [retailer, items] of Object.entries(this.skuConfig)) {
      for (const item of items) {
        const key = `${retailer}-${item.sku}`;
        
        // Check immediately
        this.checkStock(retailer, item);
        
        // Then check every 30 seconds with some jitter
        const interval = setInterval(() => {
          const jitter = Math.random() * 10000; // 0-10 second jitter
          setTimeout(() => this.checkStock(retailer, item), jitter);
        }, 30000);
        
        this.intervals.set(key, interval);
      }
    }
  }

  private stopMonitoring(): void {
    console.log('⏹️ Stopping stock monitoring...');
    this.isRunning = false;
    
    for (const interval of this.intervals.values()) {
      clearInterval(interval);
    }
    this.intervals.clear();
  }

  private restartMonitoring(): void {
    this.stopMonitoring();
    setTimeout(() => this.startMonitoring(), 1000);
  }

  public start(): void {
    console.log('🤖 Pokebot Scout starting up...');
    this.startMonitoring();

    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log('\n👋 Shutting down scout...');
      this.stopMonitoring();
      process.exit(0);
    });
  }
}

// Start the scout
const scout = new Scout();
scout.start();
