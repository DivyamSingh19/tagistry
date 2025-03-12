import time
import json
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class NFTMarketplaceScraper:
    """Scraper for NFT marketplaces like OpenSea and Rarible"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.marketplace_apis = {
            "opensea": "https://api.opensea.io/api/v1",
            "rarible": "https://api.rarible.org/v0.1"
        }
        self.headers = {
            "Accept": "application/json",
            "X-API-KEY": ""  # API key would come from env or config
        }
    
    def set_api_key(self, marketplace, api_key):
        """Set API key for a specific marketplace"""
        if marketplace in self.marketplace_apis:
            self.headers["X-API-KEY"] = api_key
    
    def navigate_to_collection(self, marketplace, collection_slug):
        """Navigate to an NFT collection"""
        if marketplace == "opensea":
            url = f"https://opensea.io/collection/{collection_slug}"
        elif marketplace == "rarible":
            url = f"https://rarible.com/collection/{collection_slug}"
        else:
            self.logger.error(f"Unsupported marketplace: {marketplace}")
            return False
            
        try:
            self.logger.info(f"Navigating to {url}")
            self.driver.get(url)
            time.sleep(3)
            return True
        except Exception as e:
            self.logger.error(f"Error navigating to collection: {e}")
            return False
    
    def scrape_nfts_from_collection(self, marketplace, collection_slug, limit=50):
        """Scrape NFTs from a collection using API when possible, fallback to browser"""
        self.logger.info(f"Scraping NFTs from {marketplace} collection: {collection_slug}")
        
        nfts = []
        
        # Try API first if we have an API key
        if self.headers["X-API-KEY"] and marketplace in self.marketplace_apis:
            try:
                if marketplace == "opensea":
                    url = f"{self.marketplace_apis[marketplace]}/assets?collection={collection_slug}&limit={limit}"
                    response = requests.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        for asset in data.get("assets", []):
                            nft = {
                                "id": asset.get("token_id"),
                                "name": asset.get("name"),
                                "description": asset.get("description"),
                                "image_url": asset.get("image_url"),
                                "permalink": asset.get("permalink"),
                                "contract_address": asset.get("asset_contract", {}).get("address"),
                                "creator": asset.get("creator", {}).get("user", {}).get("username"),
                                "traits": [trait for trait in asset.get("traits", [])]
                            }
                            nfts.append(nft)
                        
                        self.logger.info(f"Scraped {len(nfts)} NFTs via API")
                        return nfts
            except Exception as e:
                self.logger.warning(f"API error: {e}. Falling back to browser scraping")
        
        # Fallback to browser scraping
        if not self.navigate_to_collection(marketplace, collection_slug):
            return []
            
        try:
            # Wait for NFT cards to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Asset--anchor"))
            )
            
            # Scroll to load more NFTs
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            # Extract NFT data
            if marketplace == "opensea":
                nft_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Asset--anchor")
                for i, elem in enumerate(nft_elements):
                    if i >= limit:
                        break
                        
                    try:
                        # Extract available data
                        nft = {
                            "name": elem.find_element(By.CSS_SELECTOR, ".AssetCardFooter--name").text,
                            "permalink": elem.get_attribute("href"),
                            "image_url": elem.find_element(By.CSS_SELECTOR, "img").get_attribute("src"),
                        }
                        nfts.append(nft)
                    except:
                        continue
            
            self.logger.info(f"Scraped {len(nfts)} NFTs via browser")
            return nfts
            
        except Exception as e:
            self.logger.error(f"Error scraping NFTs: {e}")
            return []
    
    def scrape_nft_details(self, marketplace, contract_address, token_id):
        """Scrape detailed information about a specific NFT"""
        self.logger.info(f"Scraping NFT details: {contract_address}/{token_id}")
        
        # Try API first
        if self.headers["X-API-KEY"] and marketplace in self.marketplace_apis:
            try:
                if marketplace == "opensea":
                    url = f"{self.marketplace_apis[marketplace]}/asset/{contract_address}/{token_id}"
                    response = requests.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        asset = response.json()
                        nft = {
                            "id": asset.get("token_id"),
                            "name": asset.get("name"),
                            "description": asset.get("description"),
                            "image_url": asset.get("image_url"),
                            "image_original_url": asset.get("image_original_url"),
                            "animation_url": asset.get("animation_url"),
                            "permalink": asset.get("permalink"),
                            "contract_address": asset.get("asset_contract", {}).get("address"),
                            "creator": asset.get("creator", {}).get("user", {}).get("username"),
                            "owner": asset.get("owner", {}).get("user", {}).get("username"),
                            "traits": [trait for trait in asset.get("traits", [])],
                            "last_sale": asset.get("last_sale"),
                            "top_bid": asset.get("top_bid"),
                            "listing_date": asset.get("listing_date")
                        }
                        
                        # Get blockchain metadata
                        nft["token_metadata"] = asset.get("token_metadata")
                        
                        # Get IPFS data if available
                        ipfs_hash = None
                        if asset.get("image_original_url") and "ipfs://" in asset.get("image_original_url"):
                            ipfs_hash = asset.get("image_original_url").split("ipfs://")[1]
                            nft["ipfs_hash"] = ipfs_hash
                        
                        return nft
            except Exception as e:
                self.logger.warning(f"API error: {e}. Falling back to browser scraping")
        
        # Fallback to browser scraping
        try:
            if marketplace == "opensea":
                url = f"https://opensea.io/assets/{contract_address}/{token_id}"
            elif marketplace == "rarible":
                url = f"https://rarible.com/token/{contract_address}:{token_id}"
            else:
                self.logger.error(f"Unsupported marketplace: {marketplace}")
                return None
                
            self.driver.get(url)
            time.sleep(3)
            
            # Extract NFT details
            nft = {
                "contract_address": contract_address,
                "token_id": token_id,
                "url": url
            }
            
            if marketplace == "opensea":
                try:
                    nft["name"] = self.driver.find_element(By.CSS_SELECTOR, ".item--title").text
                except:
                    pass
                    
                try:
                    nft["description"] = self.driver.find_element(By.CSS_SELECTOR, ".item--description").text
                except:
                    pass
                    
                try:
                    nft["image_url"] = self.driver.find_element(By.CSS_SELECTOR, ".Image--image").get_attribute("src")
                except:
                    pass
            
            return nft
            
        except Exception as e:
            self.logger.error(f"Error scraping NFT details: {e}")
            return None