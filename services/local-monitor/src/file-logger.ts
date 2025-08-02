import * as fs from 'fs';
import * as path from 'path';

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  data?: any;
}

export interface MonitorStatus {
  isRunning: boolean;
  lastCheck: string | null;
  config: {
    zipCodes: string[];
    radiusMiles: number;
    checkIntervalMinutes: number;
    enabledRetailers: string[];
  };
  uptime: number;
}

export interface StoreInfo {
  id: string;
  name: string;
  retailer: string;
  distance: number;
  address: string;
  city: string;
  state: string;
  zip: string;
  phone?: string | undefined;
  hours?: string | undefined;
  lastChecked: string | null;
  totalChecks: number;
  successfulChecks: number;
}

export interface ProductFind {
  timestamp: string;
  product: {
    name: string;
    price?: string | undefined;
    availability: string;
    url?: string | undefined;
    sku?: string | undefined;
  };
  store: {
    id: string;
    name: string;
    retailer: string;
    distance: number;
    address: string;
  };
}

export class FileLogger {
  private logsDir: string;
  private dataDir: string;

  constructor(baseDir: string = './') {
    this.logsDir = path.join(baseDir, 'logs');
    this.dataDir = path.join(baseDir, 'data');
    
    // Create directories if they don't exist
    this.ensureDirectories();
  }

  private ensureDirectories(): void {
    if (!fs.existsSync(this.logsDir)) {
      fs.mkdirSync(this.logsDir, { recursive: true });
    }
    if (!fs.existsSync(this.dataDir)) {
      fs.mkdirSync(this.dataDir, { recursive: true });
    }
  }

  public log(level: LogEntry['level'], message: string, data?: any): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };

    // Write to main log file
    const logFile = path.join(this.logsDir, 'monitor.log');
    const logLine = `[${entry.timestamp}] ${entry.level.toUpperCase()}: ${entry.message}\n`;
    fs.appendFileSync(logFile, logLine);

    // Also write JSON log for easier parsing
    const jsonLogFile = path.join(this.logsDir, 'monitor.json');
    fs.appendFileSync(jsonLogFile, JSON.stringify(entry) + '\n');

    // Console output with colors
    this.logToConsole(entry);
  }

  private logToConsole(entry: LogEntry): void {
    const colors = {
      info: '\x1b[36m',    // cyan
      warning: '\x1b[33m', // yellow
      error: '\x1b[31m',   // red
      success: '\x1b[32m'  // green
    };
    const reset = '\x1b[0m';
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    
    console.log(`${colors[entry.level]}[${timestamp}] ${entry.level.toUpperCase()}: ${entry.message}${reset}`);
  }

  public updateStatus(status: MonitorStatus): void {
    const statusFile = path.join(this.dataDir, 'status.json');
    fs.writeFileSync(statusFile, JSON.stringify(status, null, 2));
  }

  public updateStores(stores: StoreInfo[]): void {
    const storesFile = path.join(this.dataDir, 'stores.json');
    fs.writeFileSync(storesFile, JSON.stringify(stores, null, 2));
  }

  public recordProductFind(productFind: ProductFind): void {
    // Add to finds file
    const findsFile = path.join(this.dataDir, 'products-found.json');
    let finds: ProductFind[] = [];
    
    if (fs.existsSync(findsFile)) {
      try {
        const data = fs.readFileSync(findsFile, 'utf8');
        finds = JSON.parse(data);
      } catch (error) {
        finds = [];
      }
    }
    
    finds.unshift(productFind); // Add to beginning
    finds = finds.slice(0, 100); // Keep only last 100 finds
    
    fs.writeFileSync(findsFile, JSON.stringify(finds, null, 2));

    // Also create a daily summary file
    const today = new Date().toISOString().split('T')[0];
    const dailyFile = path.join(this.dataDir, `products-${today}.json`);
    
    let dailyFinds: ProductFind[] = [];
    if (fs.existsSync(dailyFile)) {
      try {
        const data = fs.readFileSync(dailyFile, 'utf8');
        dailyFinds = JSON.parse(data);
      } catch (error) {
        dailyFinds = [];
      }
    }
    
    dailyFinds.push(productFind);
    fs.writeFileSync(dailyFile, JSON.stringify(dailyFinds, null, 2));
  }

  public getStatus(): MonitorStatus | null {
    const statusFile = path.join(this.dataDir, 'status.json');
    if (fs.existsSync(statusFile)) {
      try {
        const data = fs.readFileSync(statusFile, 'utf8');
        return JSON.parse(data);
      } catch (error) {
        return null;
      }
    }
    return null;
  }

  public getStores(): StoreInfo[] {
    const storesFile = path.join(this.dataDir, 'stores.json');
    if (fs.existsSync(storesFile)) {
      try {
        const data = fs.readFileSync(storesFile, 'utf8');
        return JSON.parse(data);
      } catch (error) {
        return [];
      }
    }
    return [];
  }

  public getRecentFinds(limit: number = 20): ProductFind[] {
    const findsFile = path.join(this.dataDir, 'products-found.json');
    if (fs.existsSync(findsFile)) {
      try {
        const data = fs.readFileSync(findsFile, 'utf8');
        const finds: ProductFind[] = JSON.parse(data);
        return finds.slice(0, limit);
      } catch (error) {
        return [];
      }
    }
    return [];
  }

  public generateSummary(): string {
    const status = this.getStatus();
    const stores = this.getStores();
    const recentFinds = this.getRecentFinds(10);
    
    let summary = '\n=== POKEMON MONITOR SUMMARY ===\n';
    
    if (status) {
      summary += `Status: ${status.isRunning ? 'RUNNING' : 'STOPPED'}\n`;
      summary += `Last Check: ${status.lastCheck || 'Never'}\n`;
      summary += `Monitoring: ${status.config.zipCodes.join(', ')} (${status.config.radiusMiles} miles)\n`;
      summary += `Check Interval: ${status.config.checkIntervalMinutes} minutes\n`;
      summary += `Retailers: ${status.config.enabledRetailers.join(', ')}\n`;
    }
    
    summary += `\nStores Found: ${stores.length}\n`;
    if (stores.length > 0) {
      const storesByRetailer = stores.reduce((acc, store) => {
        acc[store.retailer] = (acc[store.retailer] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      
      for (const [retailer, count] of Object.entries(storesByRetailer)) {
        summary += `  ${retailer}: ${count} stores\n`;
      }
    }
    
    summary += `\nRecent Pokemon Products Found: ${recentFinds.length}\n`;
    if (recentFinds.length > 0) {
      recentFinds.slice(0, 5).forEach((find, index) => {
        summary += `  ${index + 1}. ${find.product.name} at ${find.store.name} (${find.store.retailer})\n`;
        if (find.product.price) summary += `     Price: ${find.product.price}\n`;
        summary += `     Found: ${new Date(find.timestamp).toLocaleString()}\n`;
      });
    }
    
    summary += '\n=== END SUMMARY ===\n';
    return summary;
  }

  public writeSummaryToFile(): void {
    const summary = this.generateSummary();
    const summaryFile = path.join(this.dataDir, 'summary.txt');
    fs.writeFileSync(summaryFile, summary);
    
    // Also log to console
    console.log(summary);
  }
}