import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { CookieJar } from 'tough-cookie';
import { wrapper } from 'axios-cookiejar-support';

export interface ProxyConfig {
  host: string;
  port: number;
  auth?: {
    username: string;
    password: string;
  };
}

export interface ClientConfig {
  proxy?: ProxyConfig;
  rotateUserAgents?: boolean;
  delayBetweenRequests?: number;
  maxRetries?: number;
}

export class AdvancedHttpClient {
  private clients: Map<string, AxiosInstance> = new Map();
  private cookieJars: Map<string, CookieJar> = new Map();
  private requestCount: number = 0;
  private lastRequestTime: number = 0;
  private config: ClientConfig;

  private userAgents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
  ];

  private commonHeaders = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
  };

  constructor(config: ClientConfig = {}) {
    this.config = {
      rotateUserAgents: true,
      delayBetweenRequests: 2000,
      maxRetries: 3,
      ...config
    };
  }

  private getOrCreateClient(domain: string): AxiosInstance {
    if (!this.clients.has(domain)) {
      const jar = new CookieJar();
      this.cookieJars.set(domain, jar);

      const client = wrapper(axios.create({
        jar,
        timeout: 15000,
        maxRedirects: 5,
        validateStatus: (status) => status < 500, // Don't throw on 4xx errors
        proxy: this.config.proxy ? {
          host: this.config.proxy.host,
          port: this.config.proxy.port,
          ...(this.config.proxy.auth && { auth: this.config.proxy.auth })
        } : false
      }));

      this.clients.set(domain, client);
    }

    return this.clients.get(domain)!;
  }

  private getRandomUserAgent(): string {
    return this.userAgents[Math.floor(Math.random() * this.userAgents.length)] || this.userAgents[0]!;
  }

  private async addDelay(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    const minDelay = this.config.delayBetweenRequests || 2000;

    if (timeSinceLastRequest < minDelay) {
      const delay = minDelay - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    this.lastRequestTime = Date.now();
  }

  private getDomainFromUrl(url: string): string {
    try {
      return new URL(url).hostname;
    } catch {
      return 'default';
    }
  }

  async get(url: string, config: AxiosRequestConfig = {}): Promise<AxiosResponse> {
    await this.addDelay();
    
    const domain = this.getDomainFromUrl(url);
    const client = this.getOrCreateClient(domain);
    
    const headers: Record<string, string> = {
      ...this.commonHeaders,
      'User-Agent': this.config.rotateUserAgents ? this.getRandomUserAgent() : (this.userAgents[0] || '')
    };
    
    // Add custom headers from config
    if (config.headers) {
      Object.entries(config.headers).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          headers[key] = String(value);
        }
      });
    }

    // Add domain-specific headers
    if (domain.includes('bestbuy.com')) {
      headers['Referer'] = 'https://www.bestbuy.com/';
      headers['Origin'] = 'https://www.bestbuy.com';
      headers['Sec-Fetch-Site'] = 'same-origin';
    } else if (domain.includes('target.com')) {
      headers['Referer'] = 'https://www.target.com/';
      headers['Origin'] = 'https://www.target.com';
      headers['Sec-Fetch-Site'] = 'same-origin';
    }

    let lastError: any;
    
    for (let attempt = 1; attempt <= (this.config.maxRetries || 3); attempt++) {
      try {
        console.log(`[${domain}] Attempt ${attempt}/${this.config.maxRetries} - ${url}`);
        
        const response = await client.get(url, {
          ...config,
          headers
        });

        this.requestCount++;
        console.log(`[${domain}] Success! Status: ${response.status}, Cookies: ${this.cookieJars.get(domain)?.getCookieStringSync(url) ? 'Yes' : 'No'}`);
        
        return response;
      } catch (error: any) {
        lastError = error;
        console.log(`[${domain}] Attempt ${attempt} failed: ${error.response?.status || error.code} - ${error.message}`);
        
        if (attempt < (this.config.maxRetries || 3)) {
          // Exponential backoff
          const delay = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
          console.log(`[${domain}] Retrying in ${Math.round(delay)}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError;
  }

  // Method to initialize session by visiting homepage first
  async initializeSession(domain: string): Promise<void> {
    console.log(`[${domain}] Initializing session...`);
    
    try {
      if (domain.includes('bestbuy')) {
        await this.get('https://www.bestbuy.com/', {
          headers: {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
          }
        });
        console.log(`[bestbuy.com] Session initialized`);
      } else if (domain.includes('target')) {
        await this.get('https://www.target.com/', {
          headers: {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
          }
        });
        console.log(`[target.com] Session initialized`);
      }
    } catch (error: any) {
      console.log(`[${domain}] Session initialization failed: ${error.message}`);
    }
  }

  // Get specific API endpoints that might work better
  async findWorkingEndpoints(domain: string): Promise<string[]> {
    const endpoints: string[] = [];
    
    if (domain.includes('bestbuy')) {
      const bestbuyEndpoints = [
        'https://www.bestbuy.com/api/tcfb/model.json?paths=[["shop","scds","v2","page","tenants","bbypres","realms","web","contexts","global","cachePolicy"]]&method=get',
        'https://www.bestbuy.com/api/csiservice/v2/key/localization',
        'https://www.bestbuy.com/api/tcfb/model.json?paths=[["shop","magellan","v2","page","region","US","zipCode","' + '07748' + '"]]&method=get',
        'https://www.bestbuy.com/site/searchpage.jsp?st=pokemon',
        'https://www.bestbuy.com/site/store-locator'
      ];
      
      for (const endpoint of bestbuyEndpoints) {
        try {
          const response = await this.get(endpoint);
          if (response.status === 200) {
            endpoints.push(endpoint);
            console.log(`[bestbuy.com] Working endpoint found: ${endpoint}`);
          }
        } catch (error) {
          console.log(`[bestbuy.com] Endpoint failed: ${endpoint}`);
        }
      }
    }

    if (domain.includes('target')) {
      const targetEndpoints = [
        'https://www.target.com/c/pokemon-trading-card-game-collectibles/-/N-xbvqf',
        'https://www.target.com/s?searchTerm=pokemon',
        'https://www.target.com/store-locator',
        'https://api.target.com/location_search/v1/stores?within=50&units=mile&place=' + '07748',
        'https://redsky.target.com/v2/pdp/tcin/placeholder'
      ];
      
      for (const endpoint of targetEndpoints) {
        try {
          const response = await this.get(endpoint);
          if (response.status === 200) {
            endpoints.push(endpoint);
            console.log(`[target.com] Working endpoint found: ${endpoint}`);
          }
        } catch (error) {
          console.log(`[target.com] Endpoint failed: ${endpoint}`);
        }
      }
    }

    return endpoints;
  }

  getStats(): { requestCount: number; domainsActive: number } {
    return {
      requestCount: this.requestCount,
      domainsActive: this.clients.size
    };
  }

  // Clear sessions for a fresh start
  clearSessions(): void {
    this.clients.clear();
    this.cookieJars.clear();
    this.requestCount = 0;
    console.log('All sessions cleared');
  }
}