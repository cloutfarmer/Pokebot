import * as fs from 'fs';
import * as path from 'path';
import { StoreLocator } from './store-locator';
import { BestBuyMonitor } from './retailers/bestbuy';
import { TargetMonitor } from './retailers/target';
import { Notifier } from './notifier';

interface LocalConfig {
  zip_codes: string[];
  radius_miles: number;
  check_interval_minutes: number;
  retailers: {
    bestbuy: {
      enabled: boolean;
      categories: string[];
      search_terms: string[];
    };
    target: {
      enabled: boolean;
      search_terms: string[];
    };
    walgreens: {
      enabled: boolean;
      search_terms: string[];
    };
    gamestop: {
      enabled: boolean;
      search_terms: string[];
    };
  };
  notifications: {
    console: boolean;
    email: boolean;
    webhook: boolean;
  };
  user_agent: string;
}

export class LocalMonitorService {
  private config: LocalConfig;
  private storeLocator: StoreLocator;
  private bestBuyMonitor: BestBuyMonitor;
  private targetMonitor: TargetMonitor;
  private notifier: Notifier;
  private isRunning: boolean = false;
  private intervalId: NodeJS.Timeout | null = null;

  constructor() {
    this.config = this.loadConfig();
    this.storeLocator = new StoreLocator(this.config.user_agent);
    this.bestBuyMonitor = new BestBuyMonitor(this.config.user_agent);
    this.targetMonitor = new TargetMonitor(this.config.user_agent);
    this.notifier = new Notifier(this.config.notifications);
  }

  private loadConfig(): LocalConfig {
    const configPath = path.join(__dirname, '../config/local-config.json');
    
    if (!fs.existsSync(configPath)) {
      throw new Error(`Config file not found: ${configPath}`);
    }

    const configData = fs.readFileSync(configPath, 'utf8');
    return JSON.parse(configData);
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      this.notifier.sendError('Local monitor is already running');
      return;
    }

    this.isRunning = true;
    this.notifier.updateMonitorStatus(this.config, true);
    this.notifier.sendStatusUpdate('🚀 Starting Local Pokemon Monitor...');
    
    // Initial check
    await this.performCheck();
    
    // Set up interval
    const intervalMs = this.config.check_interval_minutes * 60 * 1000;
    this.intervalId = setInterval(async () => {
      await this.performCheck();
    }, intervalMs);

    this.notifier.sendStatusUpdate(
      `✅ Local monitor started! Checking every ${this.config.check_interval_minutes} minutes for Pokemon products within ${this.config.radius_miles} miles of ZIP codes: ${this.config.zip_codes.join(', ')}`
    );
    
    // Generate initial summary
    this.notifier.generateSummary();
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      this.notifier.sendError('Local monitor is not running');
      return;
    }

    this.isRunning = false;
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    this.notifier.updateMonitorStatus(this.config, false);
    this.notifier.sendStatusUpdate('🛑 Local monitor stopped');
    this.notifier.generateSummary();
  }

  private async performCheck(): Promise<void> {
    try {
      this.notifier.sendStatusUpdate('🔍 Checking local stores for Pokemon products...');
      
      const allResults = [];

      // Check each ZIP code
      for (const zipCode of this.config.zip_codes) {
        this.notifier.sendStatusUpdate(`📍 Checking stores near ${zipCode}...`);
        
        // Find stores
        const stores = await this.storeLocator.findAllStores(zipCode, this.config.radius_miles);
        this.notifier.sendStatusUpdate(`Found ${stores.length} stores within ${this.config.radius_miles} miles`);

        // Check Best Buy stores
        if (this.config.retailers.bestbuy.enabled) {
          const bestBuyStores = stores.filter(store => store.retailer === 'bestbuy');
          if (bestBuyStores.length > 0) {
            this.notifier.sendStatusUpdate(`🔍 Checking ${bestBuyStores.length} Best Buy stores...`);
            const bestBuyResults = await this.bestBuyMonitor.checkMultipleStores(
              bestBuyStores,
              this.config.retailers.bestbuy.search_terms
            );
            allResults.push(...bestBuyResults);
          }
        }

        // Check Target stores
        if (this.config.retailers.target.enabled) {
          const targetStores = stores.filter(store => store.retailer === 'target');
          if (targetStores.length > 0) {
            this.notifier.sendStatusUpdate(`🔍 Checking ${targetStores.length} Target stores...`);
            const targetResults = await this.targetMonitor.checkMultipleStores(
              targetStores,
              this.config.retailers.target.search_terms
            );
            allResults.push(...targetResults);
          }
        }

        // TODO: Add Walgreens, GameStop checks here
        // if (this.config.retailers.walgreens.enabled) { ... }
        // if (this.config.retailers.gamestop.enabled) { ... }
      }

      // Send notifications for any stock found
      await this.notifier.sendStockAlert(allResults);
      
      const stockCount = allResults.filter(r => r.hasStock).length;
      if (stockCount === 0) {
        this.notifier.sendStatusUpdate('😔 No Pokemon products found in local stores this check');
      } else {
        this.notifier.sendStatusUpdate(`🎉 Found Pokemon products at ${stockCount} local stores!`);
      }

      // Update status after each check
      this.notifier.updateMonitorStatus(this.config, this.isRunning);

    } catch (error) {
      this.notifier.sendError(`Error during check: ${error}`);
      this.notifier.updateMonitorStatus(this.config, this.isRunning);
    }
  }

  getStatus(): string {
    return `Local Monitor Status:
- Running: ${this.isRunning}
- ZIP Codes: ${this.config.zip_codes.join(', ')}
- Radius: ${this.config.radius_miles} miles
- Check Interval: ${this.config.check_interval_minutes} minutes
- Enabled Retailers: ${Object.entries(this.config.retailers)
  .filter(([_, config]) => config.enabled)
  .map(([name]) => name)
  .join(', ')}`;
  }
}

// CLI interface
async function main() {
  const monitor = new LocalMonitorService();
  
  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down local monitor...');
    await monitor.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log('\n🛑 Shutting down local monitor...');
    await monitor.stop();
    process.exit(0);
  });

  // Start the monitor
  try {
    await monitor.start();
    
    // Keep the process alive
    process.stdin.resume();
  } catch (error) {
    console.error('Failed to start local monitor:', error);
    process.exit(1);
  }
}

// Run if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}

export default LocalMonitorService;
