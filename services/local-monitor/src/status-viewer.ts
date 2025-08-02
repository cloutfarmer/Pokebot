#!/usr/bin/env ts-node

import * as fs from 'fs';
import * as path from 'path';


class StatusViewer {
  private dataDir: string;
  private logsDir: string;

  constructor() {
    this.dataDir = path.join(__dirname, '../data');
    this.logsDir = path.join(__dirname, '../logs');
  }

  public showStatus(): void {
    console.clear();
    console.log('🤖 POKEMON LOCAL MONITOR STATUS 🤖\n');
    
    const status = this.readStatusFile();
    if (status) {
      console.log(`Status: ${status.isRunning ? '🟢 RUNNING' : '🔴 STOPPED'}`);
      console.log(`Last Check: ${status.lastCheck ? new Date(status.lastCheck).toLocaleString() : 'Never'}`);
      console.log(`Monitoring: ${status.config.zipCodes.join(', ')} (${status.config.radiusMiles} miles)`);
      console.log(`Check Interval: ${status.config.checkIntervalMinutes} minutes`);
      console.log(`Retailers: ${status.config.enabledRetailers.join(', ')}`);
      console.log(`Uptime: ${Math.floor(status.uptime / 60)}m ${Math.floor(status.uptime % 60)}s\n`);
    } else {
      console.log('❌ No status data available\n');
    }

    const stores = this.readStoresFile();
    console.log(`📍 STORES FOUND: ${stores.length}`);
    stores.forEach(store => {
      const lastChecked = store.lastChecked 
        ? new Date(store.lastChecked).toLocaleTimeString()
        : 'Never';
      const successRate = store.totalChecks > 0 
        ? Math.round((store.successfulChecks / store.totalChecks) * 100)
        : 0;
      
      console.log(`  ${store.retailer.toUpperCase()} - ${store.name}`);
      console.log(`    Distance: ${store.distance} miles | Last: ${lastChecked} | Success: ${successRate}%`);
    });

    const products = this.readProductsFile();
    console.log(`\n🎮 RECENT POKEMON PRODUCTS: ${products.length}`);
    products.slice(0, 5).forEach((product, index) => {
      const time = new Date(product.timestamp).toLocaleString();
      console.log(`  ${index + 1}. ${product.product.name}`);
      console.log(`     Store: ${product.store.name} (${product.store.retailer})`);
      console.log(`     Price: ${product.product.price || 'N/A'} | ${time}`);
    });

    console.log('\n📊 QUICK COMMANDS:');
    console.log('  npm run logs    - Follow live logs');
    console.log('  npm run dev     - Start monitoring');
    console.log('  cat data/summary.txt - Full summary');
  }

  public showLogs(lines: number = 20): void {
    const logFile = path.join(this.logsDir, 'monitor.log');
    if (fs.existsSync(logFile)) {
      const content = fs.readFileSync(logFile, 'utf8');
      const logLines = content.trim().split('\n');
      console.log(`📋 LAST ${Math.min(lines, logLines.length)} LOG ENTRIES:\n`);
      logLines.slice(-lines).forEach(line => console.log(line));
    } else {
      console.log('❌ No log file found');
    }
  }

  public followLogs(): void {
    const logFile = path.join(this.logsDir, 'monitor.log');
    console.log('📋 Following logs (Ctrl+C to stop)...\n');
    
    if (fs.existsSync(logFile)) {
      // Show last few lines first
      this.showLogs(5);
      console.log('\n--- LIVE LOGS ---');
    }

    // Watch for file changes
    if (fs.existsSync(this.logsDir)) {
      fs.watchFile(logFile, (curr, prev) => {
        if (curr.mtime > prev.mtime) {
          const content = fs.readFileSync(logFile, 'utf8');
          const lines = content.trim().split('\n');
          console.log(lines[lines.length - 1]);
        }
      });
    }
  }

  public watch(): void {
    console.log('👀 Watching status (Ctrl+C to stop)...\n');
    
    const refresh = () => {
      this.showStatus();
      console.log(`\n🔄 Last updated: ${new Date().toLocaleTimeString()}`);
    };

    refresh();
    setInterval(refresh, 5000); // Update every 5 seconds
  }

  private readStatusFile(): any {
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

  private readStoresFile(): any[] {
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

  private readProductsFile(): any[] {
    const productsFile = path.join(this.dataDir, 'products-found.json');
    if (fs.existsSync(productsFile)) {
      try {
        const data = fs.readFileSync(productsFile, 'utf8');
        return JSON.parse(data);
      } catch (error) {
        return [];
      }
    }
    return [];
  }
}

// CLI interface
function main() {
  const viewer = new StatusViewer();
  const args = process.argv.slice(2);
  const command = args[0] || 'status';

  switch (command) {
    case 'status':
    case 's':
      viewer.showStatus();
      break;
    
    case 'logs':
    case 'l':
      const lines = parseInt(args[1] || '20') || 20;
      viewer.showLogs(lines);
      break;
    
    case 'follow':
    case 'f':
      viewer.followLogs();
      break;
    
    case 'watch':
    case 'w':
      viewer.watch();
      break;
    
    default:
      console.log('Pokemon Monitor Status Viewer');
      console.log('');
      console.log('Usage:');
      console.log('  ts-node status-viewer.ts [command]');
      console.log('');
      console.log('Commands:');
      console.log('  status, s          Show current status (default)');
      console.log('  logs, l [lines]    Show recent logs (default: 20 lines)');
      console.log('  follow, f          Follow logs in real-time');
      console.log('  watch, w           Watch status updates');
      break;
  }
}

if (require.main === module) {
  main();
}