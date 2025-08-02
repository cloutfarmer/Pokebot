import { AdvancedHttpClient } from './advanced-http-client';

export interface Store {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  phone?: string;
  distance?: number;
  hours?: string;
  retailer: string;
}

export class StoreLocator {
  private httpClient: AdvancedHttpClient;

  constructor(_userAgent: string) {
    this.httpClient = new AdvancedHttpClient({
      rotateUserAgents: true,
      delayBetweenRequests: 3000,
      maxRetries: 3
    });
    console.log(`StoreLocator initialized with advanced HTTP client`);
  }

  async findBestBuyStores(zipCode: string, radiusMiles: number): Promise<Store[]> {
    try {
      console.log(`Finding Best Buy stores near ${zipCode} within ${radiusMiles} miles`);
      
      // Initialize session first
      await this.httpClient.initializeSession('bestbuy.com');
      
      // Try multiple Best Buy endpoints
      const endpoints = [
        // Modern API endpoint
        `https://www.bestbuy.com/api/tcfb/model.json?paths=[["shop","magellan","v2","page","region","US","zipCode","${zipCode}"]]&method=get`,
        // Store locator endpoint with different params
        `https://www.bestbuy.com/site/misc/store-locator?requesttype=locatorStoreSearch&zip=${zipCode}&radius=${radiusMiles}&format=json`,
        // Alternative store search
        `https://www.bestbuy.com/api/3.0/stores?zip=${zipCode}&radius=${radiusMiles}`,
        // Search page that might have store data
        `https://www.bestbuy.com/site/store-locator/search?zip=${zipCode}`
      ];

      let response = null;
      let workingEndpoint = null;

      for (const endpoint of endpoints) {
        try {
          console.log(`Trying Best Buy endpoint: ${endpoint}`);
          response = await this.httpClient.get(endpoint, {
            headers: {
              'Accept': 'application/json, text/plain, */*',
              'Referer': 'https://www.bestbuy.com/site/store-locator'
            }
          });
          
          if (response.status === 200 && response.data) {
            workingEndpoint = endpoint;
            console.log(`Best Buy endpoint success: ${endpoint}`);
            break;
          }
        } catch (endpointError: any) {
          console.log(`Best Buy endpoint failed: ${endpoint} - ${endpointError.response?.status || endpointError.code}`);
          continue;
        }
      }

      if (!response || !workingEndpoint) {
        throw new Error('All Best Buy endpoints failed');
      }

      const stores: Store[] = [];
      
      // Parse response based on endpoint type
      if (workingEndpoint.includes('tcfb/model.json')) {
        // Parse modern API response
        this.parseBestBuyTcfbResponse(response.data, stores, radiusMiles);
      } else if (response.data && Array.isArray(response.data)) {
        // Direct store array
        this.parseBestBuyStoreArray(response.data, stores);
      } else if (response.data && response.data.stores) {
        // Standard response with stores property
        this.parseBestBuyStoreArray(response.data.stores, stores);
      } else if (typeof response.data === 'string') {
        // HTML response - extract JSON
        this.parseBestBuyHtmlResponse(response.data, stores, radiusMiles);
      }

      console.log(`Found ${stores.length} Best Buy stores`);
      return stores;
    } catch (error: any) {
      console.error('Error finding Best Buy stores:', error.message);
      return [];
    }
  }

  private parseBestBuyStoreArray(storeArray: any[], stores: Store[]): void {
    for (const storeData of storeArray) {
      stores.push({
        id: storeData.storeNumber || storeData.id || storeData.storeId,
        name: storeData.name || storeData.longName || storeData.storeName,
        address: storeData.address || storeData.address1,
        city: storeData.city,
        state: storeData.state || storeData.stateCode,
        zip: storeData.postalCode || storeData.zip || storeData.zipCode,
        phone: storeData.phone || storeData.phoneNumber,
        distance: storeData.distance || storeData.distanceInMiles,
        hours: storeData.hours || storeData.storeHours || 'Call for hours',
        retailer: 'bestbuy'
      });
    }
  }

  private parseBestBuyTcfbResponse(data: any, stores: Store[], _radiusMiles: number): void {
    try {
      // Navigate complex JSON structure from modern API
      const jsonData = data?.jsonGraph || data?.json || data;
      
      // Look for store data in various possible locations
      const paths = [
        'shop.magellan.v2.page.region.US',
        'shop.stores',
        'stores',
        'locations'
      ];

      for (const path of paths) {
        const storeData = this.getNestedProperty(jsonData, path);
        if (storeData && Array.isArray(storeData)) {
          this.parseBestBuyStoreArray(storeData, stores);
          break;
        }
      }
    } catch (error) {
      console.log('Error parsing Best Buy TCFB response:', error);
    }
  }

  private parseBestBuyHtmlResponse(html: string, stores: Store[], _radiusMiles: number): void {
    try {
      // Look for JSON data in script tags
      const patterns = [
        /"stores":\s*(\[.*?\])/s,
        /window\.__INITIAL_STATE__\s*=\s*({.*?});/s,
        /window\.stores\s*=\s*(\[.*?\]);/s
      ];

      for (const pattern of patterns) {
        const match = html.match(pattern);
        if (match) {
          try {
            const storeData = JSON.parse(match[1]!);
            if (Array.isArray(storeData)) {
              this.parseBestBuyStoreArray(storeData, stores);
            } else if (storeData.stores) {
              this.parseBestBuyStoreArray(storeData.stores, stores);
            }
            break;
          } catch (parseError) {
            continue;
          }
        }
      }
    } catch (error) {
      console.log('Error parsing Best Buy HTML response:', error);
    }
  }

  private getNestedProperty(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  async findTargetStores(zipCode: string, radiusMiles: number): Promise<Store[]> {
    try {
      console.log(`Finding Target stores near ${zipCode} within ${radiusMiles} miles`);
      
      // Initialize session first
      await this.httpClient.initializeSession('target.com');
      
      // Try multiple Target endpoints
      const endpoints = [
        // Main store locator API (may need auth)
        `https://api.target.com/location_search/v1/stores?within=${radiusMiles}&units=mile&place=${zipCode}`,
        // Alternative store API
        `https://redsky.target.com/redsky_aggregations/v1/web/store_locator_v1?zip=${zipCode}&radius=${radiusMiles}&limit=50`,
        // Legacy API
        `https://api.target.com/store_locator/v2/search?zip=${zipCode}&radius=${radiusMiles}`,
        // Web page that might have store data
        `https://www.target.com/store-locator/find-stores?searchTerm=${zipCode}`,
        // Store directory page
        `https://www.target.com/sl/store-directory`
      ];

      let response = null;
      let workingEndpoint = null;

      for (const endpoint of endpoints) {
        try {
          console.log(`Trying Target endpoint: ${endpoint}`);
          response = await this.httpClient.get(endpoint, {
            headers: {
              'Accept': 'application/json, text/html, */*',
              'Referer': 'https://www.target.com/store-locator'
            }
          });
          
          if (response.status === 200 && response.data) {
            workingEndpoint = endpoint;
            console.log(`Target endpoint success: ${endpoint}`);
            break;
          }
        } catch (endpointError: any) {
          console.log(`Target endpoint failed: ${endpoint} - ${endpointError.response?.status || endpointError.code}`);
          continue;
        }
      }

      if (!response || !workingEndpoint) {
        throw new Error('All Target endpoints failed');
      }

      const stores: Store[] = [];
      
      // Parse response based on endpoint type and structure
      if (response.data?.data?.stores) {
        // Redsky API response
        this.parseTargetStoreArray(response.data.data.stores, stores);
      } else if (response.data?.stores) {
        // Direct stores array
        this.parseTargetStoreArray(response.data.stores, stores);
      } else if (Array.isArray(response.data)) {
        // Direct array response
        this.parseTargetStoreArray(response.data, stores);
      } else if (typeof response.data === 'string') {
        // HTML response - extract JSON
        this.parseTargetHtmlResponse(response.data, stores, radiusMiles);
      } else if (response.data?.locations) {
        // Alternative API structure
        this.parseTargetStoreArray(response.data.locations, stores);
      }

      console.log(`Found ${stores.length} Target stores`);
      return stores;
    } catch (error: any) {
      console.error('Error finding Target stores:', error.message);
      return [];
    }
  }

  private parseTargetStoreArray(storeArray: any[], stores: Store[]): void {
    for (const storeData of storeArray) {
      stores.push({
        id: storeData.location_id?.toString() || storeData.store_id?.toString() || storeData.id?.toString(),
        name: storeData.location_names?.[0]?.name || storeData.name || storeData.storeName,
        address: storeData.address?.address_line1 || storeData.address1 || storeData.address,
        city: storeData.address?.city || storeData.city,
        state: storeData.address?.state || storeData.state,
        zip: storeData.address?.postal_code || storeData.zip || storeData.postalCode,
        phone: storeData.phone || storeData.phoneNumber,
        distance: storeData.distance_in_miles || storeData.distance,
        hours: this.formatTargetHours(storeData.hours) || 'Call for hours',
        retailer: 'target'
      });
    }
  }

  private parseTargetHtmlResponse(html: string, stores: Store[], _radiusMiles: number): void {
    try {
      // Look for JSON data in script tags
      const patterns = [
        /__PRELOADED_QUERIES__\s*=\s*({.*?});/s,
        /window\.__INITIAL_STATE__\s*=\s*({.*?});/s,
        /"stores":\s*(\[.*?\])/s,
        /window\.stores\s*=\s*(\[.*?\]);/s
      ];

      for (const pattern of patterns) {
        const match = html.match(pattern);
        if (match) {
          try {
            const data = JSON.parse(match[1]!);
            
            // Navigate different JSON structures
            if (Array.isArray(data)) {
              this.parseTargetStoreArray(data, stores);
            } else if (data.stores) {
              this.parseTargetStoreArray(data.stores, stores);
            } else if (data.data?.stores) {
              this.parseTargetStoreArray(data.data.stores, stores);
            } else {
              // Look for stores in nested queries
              for (const key in data) {
                const queryData = data[key];
                if (queryData?.data?.stores) {
                  this.parseTargetStoreArray(queryData.data.stores, stores);
                  break;
                }
              }
            }
            
            if (stores.length > 0) break;
          } catch (parseError) {
            continue;
          }
        }
      }
    } catch (error) {
      console.log('Error parsing Target HTML response:', error);
    }
  }

  private formatTargetHours(hours: any): string {
    try {
      if (hours?.regular_hours) {
        const today = new Date().getDay(); // 0 = Sunday, 1 = Monday, etc.
        const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
        const todayHours = hours.regular_hours[dayNames[today]!];
        
        if (todayHours) {
          return `${todayHours.open} - ${todayHours.close}`;
        }
      }
      
      return 'Hours available online';
    } catch (error) {
      return 'Hours available online';
    }
  }

  async findWalgreensStores(zipCode: string, radiusMiles: number): Promise<Store[]> {
    console.log(`Finding Walgreens stores near ${zipCode} within ${radiusMiles} miles`);
    // TODO: Implement Walgreens store locator API
    return [];
  }

  async findAllStores(zipCode: string, radiusMiles: number): Promise<Store[]> {
    const allStores: Store[] = [];
    
    try {
      const [bestBuyStores, targetStores, walgreensStores] = await Promise.all([
        this.findBestBuyStores(zipCode, radiusMiles),
        this.findTargetStores(zipCode, radiusMiles),
        this.findWalgreensStores(zipCode, radiusMiles)
      ]);

      allStores.push(...bestBuyStores, ...targetStores, ...walgreensStores);
      
      // Sort by distance
      allStores.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      
      return allStores;
    } catch (error) {
      console.error('Error finding stores:', error);
      return allStores;
    }
  }
}
