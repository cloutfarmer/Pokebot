import axios from 'axios';
import { Store } from '../store-locator';
import { AdvancedHttpClient } from '../advanced-http-client';

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

export class BestBuyMonitor {
  private userAgent: string;
  private httpClient: AdvancedHttpClient;

  constructor(userAgent: string) {
    this.userAgent = userAgent;
    this.httpClient = new AdvancedHttpClient({
      rotateUserAgents: true,
      delayBetweenRequests: 2000,
      maxRetries: 3
    });
    console.log(`BestBuyMonitor initialized with advanced HTTP client`);
  }

  async checkStoreInventory(store: Store, searchTerms: string[]): Promise<StockResult> {
    const result: StockResult = {
      store,
      products: [],
      hasStock: false,
      lastChecked: new Date()
    };

    try {
      console.log(`Checking inventory at Best Buy ${store.name} (Store #${store.id})`);
      
      // Search for Pokemon products using Best Buy's search API
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
        p.availability.toLowerCase().includes('pickup')
      );

      console.log(`Found ${result.products.length} Pokemon products at ${store.name}`);
      return result;
    } catch (error) {
      console.error(`Error checking Best Buy store ${store.name}:`, error);
      return result;
    }
  }

  private async searchProducts(searchTerm: string, storeId: string): Promise<ProductMatch[]> {
    try {
      console.log(`Searching Best Buy for "${searchTerm}" at store ${storeId}`);
      
      // Initialize session
      await this.httpClient.initializeSession('bestbuy.com');
      
      // Try multiple Best Buy product search endpoints
      const endpoints = [
        // Modern search API
        `https://www.bestbuy.com/api/tcfb/model.json?paths=[["search","products","${encodeURIComponent(searchTerm)}","storeId",${storeId}]]&method=get`,
        // Legacy product API
        `https://www.bestbuy.com/api/3.0/products?q=${encodeURIComponent(searchTerm)}&storeId=${storeId}&format=json`,
        // Alternative API
        `https://www.bestbuy.com/api/3.0/priceBlocks?apikey=mmz8y2rqxzpmzu2pktmem8rw&query=${encodeURIComponent(searchTerm)}&storeId=${storeId}&format=json`,
        // Search page that might have product data
        `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(searchTerm)}&storeId=${storeId}`
      ];

      let response = null;
      
      for (const endpoint of endpoints) {
        try {
          console.log(`Trying Best Buy product endpoint: ${endpoint}`);
          response = await this.httpClient.get(endpoint, {
            headers: {
              'Accept': 'application/json, text/html, */*',
              'Referer': 'https://www.bestbuy.com/'
            }
          });
          
          if (response.status === 200 && response.data) {
            console.log(`Best Buy product endpoint success: ${endpoint}`);
            break;
          }
        } catch (endpointError: any) {
          console.log(`Best Buy product endpoint failed: ${endpoint} - ${endpointError.response?.status || endpointError.code}`);
          continue;
        }
      }

      if (!response) {
        throw new Error('All Best Buy product endpoints failed');
      }

      const products: ProductMatch[] = [];
      
      if (response.data && response.data.products) {
        for (const product of response.data.products) {
          // Filter for Pokemon TCG products
          const name = product.name.toLowerCase();
          if (name.includes('pokemon') || name.includes('pokémon')) {
            const availability = this.determineAvailability(product, storeId);
            products.push({
              name: product.name,
              price: product.salePrice ? `$${product.salePrice}` : undefined,
              availability,
              url: `https://www.bestbuy.com/site/${product.sku}.p`,
              sku: product.sku
            });
          }
        }
      }

      // Fallback: web scraping search results
      if (products.length === 0) {
        return await this.scrapeSearchResults(searchTerm, storeId);
      }

      return products;
    } catch (error: any) {
      console.error(`Error searching for "${searchTerm}":`, error.message);
      return [];
    }
  }

  private determineAvailability(product: any, storeId: string): string {
    if (product.inStoreAvailability && product.inStoreAvailability[storeId]) {
      const storeAvailability = product.inStoreAvailability[storeId];
      if (storeAvailability.status === 'Available') {
        return 'Available for pickup today';
      } else if (storeAvailability.status === 'LimitedStock') {
        return 'Limited stock available';
      }
    }
    
    if (product.onlineAvailability) {
      if (product.onlineAvailability.status === 'Available') {
        return 'Available online';
      }
    }
    
    return 'Out of stock';
  }

  private async scrapeSearchResults(searchTerm: string, storeId: string): Promise<ProductMatch[]> {
    try {
      const searchUrl = `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(searchTerm)}&storeId=${storeId}`;
      
      const response = await axios.get(searchUrl, {
        headers: {
          'User-Agent': this.userAgent
        },
        timeout: 15000
      });

      const products: ProductMatch[] = [];
      const html = response.data;

      // Look for product data in JSON within script tags
      const productDataRegex = /"products":\s*(\[.*?\])/s;
      const match = html.match(productDataRegex);
      
      if (match) {
        try {
          const productData = JSON.parse(match[1]);
          for (const product of productData) {
            const name = product.name?.toLowerCase() || '';
            if (name.includes('pokemon') || name.includes('pokémon')) {
              products.push({
                name: product.name,
                price: product.price ? `$${product.price}` : undefined,
                availability: product.availability || 'Unknown',
                url: product.url || `https://www.bestbuy.com/site/${product.sku}.p`,
                sku: product.sku
              });
            }
          }
        } catch (parseError) {
          console.error('Error parsing product data from search results:', parseError);
        }
      }

      console.log(`Web scraping found ${products.length} Pokemon products for "${searchTerm}"`);
      return products;
    } catch (error: any) {
      console.error(`Error scraping search results for "${searchTerm}":`, error.message);
      return [];
    }
  }



  async checkMultipleStores(stores: Store[], searchTerms: string[]): Promise<StockResult[]> {
    const results: StockResult[] = [];
    
    // Check stores in parallel but with some delay to avoid rate limiting
    for (let i = 0; i < stores.length; i++) {
      const store = stores[i];
      
      if (!store) continue;
      
      try {
        const result = await this.checkStoreInventory(store, searchTerms);
        results.push(result);
        
        // Add delay between requests
        if (i < stores.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
        }
      } catch (error) {
        console.error(`Failed to check store ${store.name}:`, error);
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
    let alert = `🚨 POKEMON STOCK FOUND AT BEST BUY!\n`;
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
