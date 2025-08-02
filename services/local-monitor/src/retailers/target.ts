import axios from 'axios';
import { Store } from '../store-locator';

export interface ProductMatch {
  name: string;
  price?: string | undefined;
  availability: string;
  url?: string | undefined;
  sku?: string | undefined;
}

export interface StockResult {
  store: Store;
  products: ProductMatch[];
  hasStock: boolean;
  lastChecked: Date;
}

export class TargetMonitor {
  private userAgent: string;

  constructor(userAgent: string) {
    this.userAgent = userAgent;
    console.log(`TargetMonitor initialized with user agent: ${this.userAgent.substring(0, 50)}...`);
  }

  async checkStoreInventory(store: Store, searchTerms: string[]): Promise<StockResult> {
    const result: StockResult = {
      store,
      products: [],
      hasStock: false,
      lastChecked: new Date()
    };

    try {
      console.log(`Checking inventory at Target ${store.name} (Store #${store.id})`);
      
      // Search for Pokemon products using Target's API
      for (const searchTerm of searchTerms) {
        const products = await this.searchProducts(searchTerm, store.id);
        result.products.push(...products);
      }

      // Remove duplicates based on SKU
      result.products = result.products.filter((product, index, self) => 
        index === self.findIndex(p => p.sku === product.sku)
      );

      result.hasStock = result.products.some(p => 
        p.availability.toLowerCase().includes('available') || 
        p.availability.toLowerCase().includes('in stock')
      );

      console.log(`Found ${result.products.length} Pokemon products at ${store.name}`);
      return result;
    } catch (error) {
      console.error(`Error checking Target store ${store.name}:`, error);
      return result;
    }
  }

  private async searchProducts(searchTerm: string, storeId: string): Promise<ProductMatch[]> {
    try {
      // Target's product search API
      const response = await axios.get('https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2', {
        headers: {
          'User-Agent': this.userAgent,
          'Accept': 'application/json',
          'Referer': 'https://www.target.com'
        },
        params: {
          'keyword': searchTerm,
          'store_id': storeId,
          'pricing_store_id': storeId,
          'include_sponsored': false,
          'limit': 50,
          'offset': 0,
          'default_purchasability_filter': false,
          'include_dpa': false
        },
        timeout: 15000
      });

      const products: ProductMatch[] = [];
      
      if (response.data?.data?.search?.products) {
        for (const product of response.data.data.search.products) {
          // Filter for Pokemon TCG products
          const title = product.item?.product_description?.title?.toLowerCase() || '';
          if (title.includes('pokemon') || title.includes('pokémon') || title.includes('tcg')) {
            const availability = this.determineAvailability(product);
            const price = this.extractPrice(product);
            
            products.push({
              name: product.item?.product_description?.title || 'Unknown Product',
              price: price,
              availability,
              url: `https://www.target.com/p/-/A-${product.tcin}`,
              sku: product.tcin
            });
          }
        }
      }

      console.log(`Target API found ${products.length} Pokemon products for "${searchTerm}"`);
      return products;
    } catch (error: any) {
      console.error(`Error searching Target for "${searchTerm}":`, error.message);
      return [];
    }
  }

  private determineAvailability(product: any): string {
    try {
      const fulfillment = product.fulfillment_v2;
      
      // Check store pickup availability
      if (fulfillment?.store_pick_up?.availability_status === 'AVAILABLE') {
        return 'Available for store pickup';
      }
      
      if (fulfillment?.store_pick_up?.availability_status === 'LIMITED_STOCK') {
        return 'Limited stock - store pickup';
      }
      
      // Check ship to store
      if (fulfillment?.ship_to_store?.availability_status === 'AVAILABLE') {
        return 'Available - ship to store';
      }
      
      // Check standard shipping
      if (fulfillment?.shipping?.availability_status === 'AVAILABLE') {
        return 'Available for shipping';
      }
      
      return 'Out of stock';
    } catch (error) {
      return 'Unknown availability';
    }
  }

  private extractPrice(product: any): string | undefined {
    try {
      const price = product.price?.current_retail;
      if (price) {
        return `$${price}`;
      }
      
      const listPrice = product.price?.list_price;
      if (listPrice) {
        return `$${listPrice}`;
      }
      
      return undefined;
    } catch (error) {
      return undefined;
    }
  }



  async checkMultipleStores(stores: Store[], searchTerms: string[]): Promise<StockResult[]> {
    const results: StockResult[] = [];
    
    // Check stores with delay to avoid rate limiting
    for (let i = 0; i < stores.length; i++) {
      const store = stores[i];
      
      if (!store) continue;
      
      try {
        const result = await this.checkStoreInventory(store, searchTerms);
        results.push(result);
        
        // Add delay between requests
        if (i < stores.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 2000));
        }
      } catch (error) {
        console.error(`Failed to check Target store ${store.name}:`, error);
        results.push({
          store,
          products: [],
          hasStock: false,
          lastChecked: new Date()
        });
      }
    }
    
    return results;
  }

  formatStockAlert(result: StockResult): string {
    if (!result.hasStock) {
      return '';
    }

    const store = result.store;
    let alert = `🚨 POKEMON STOCK FOUND AT TARGET!\n`;
    alert += `📍 ${store.name} (${store.distance} miles away)\n`;
    alert += `📞 ${store.phone}\n`;
    alert += `🕒 ${store.hours}\n`;
    alert += `🗺️  ${store.address}, ${store.city}, ${store.state} ${store.zip}\n\n`;
    
    alert += `🎮 Products Available:\n`;
    result.products.forEach(product => {
      alert += `   • ${product.name}\n`;
      if (product.price) alert += `     💰 ${product.price}\n`;
      alert += `     📦 ${product.availability}\n`;
      if (product.url) alert += `     🔗 ${product.url}\n`;
      alert += `\n`;
    });

    return alert;
  }
}