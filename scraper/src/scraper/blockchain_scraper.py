import time
import json
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BlockchainExplorerScraper:
    """Scrape data from blockchain explorers like Etherscan"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.explorers = {
            "ethereum": "https://etherscan.io",
            "polygon": "https://polygonscan.com",
            "bsc": "https://bscscan.com"
        }
        self.api_endpoints = {
            "ethereum": "https://api.etherscan.io/api",
            "polygon": "https://api.polygonscan.com/api",
            "bsc": "https://api.bscscan.com/api"
        }
        self.api_keys = {}
    
    def set_api_key(self, network, api_key):
        """Set API key for a specific explorer"""
        self.api_keys[network] = api_key
    
    def get_contract_details(self, network, contract_address):
        """Get details of a smart contract"""
        self.logger.info(f"Getting details for contract {contract_address} on {network}")
        
        # Try API first
        if network in self.api_keys:
            try:
                url = f"{self.api_endpoints[network]}"
                params = {
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": contract_address,
                    "apikey": self.api_keys[network]
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "1":
                        contract_data = data["result"][0]
                        return {
                            "name": contract_data.get("ContractName"),
                            "source_code": contract_data.get("SourceCode"),
                            "abi": contract_data.get("ABI"),
                            "compiler_version": contract_data.get("CompilerVersion"),
                            "optimization_used": contract_data.get("OptimizationUsed"),
                            "runs": contract_data.get("Runs"),
                            "constructor_arguments": contract_data.get("ConstructorArguments"),
                            "implementation": contract_data.get("Implementation"),
                            "proxy": contract_data.get("Proxy") == "1"
                        }
            except Exception as e:
                self.logger.warning(f"API error: {e}. Falling back to browser scraping")
        
        # Fallback to browser scraping
        try:
            explorer_url = f"{self.explorers[network]}/address/{contract_address}"
            self.driver.get(explorer_url)
            time.sleep(3)
            
            contract_data = {
                "address": contract_address,
                "explorer_url": explorer_url
            }
            
            # Get contract name
            try:
                contract_data["name"] = self.driver.find_element(By.CSS_SELECTOR, ".text-break").text
            except:
                pass
                
            # Check if it's a contract
            try:
                # Look for "Contract" badge
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'Contract')]")
                contract_data["is_contract"] = True
            except:
                contract_data["is_contract"] = False
                
            # Get balance
            try:
                balance_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'card-body')]//span[contains(@data-toggle, 'tooltip')]")
                contract_data["balance"] = balance_element.text
            except:
                pass
                
            # Get transactions count
            try:
                txn_count_element = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Transactions')]//parent::div//span")
                contract_data["transaction_count"] = txn_count_element.text
            except:
                pass
            
            return contract_data
            
        except Exception as e:
            self.logger.error(f"Error getting contract details: {e}")
            return None
    
    def get_contract_transactions(self, network, contract_address, limit=100):
        """Get recent transactions for a contract"""
        self.logger.info(f"Getting transactions for contract {contract_address} on {network}")
        
        # Try API first
        if network in self.api_keys:
            try:
                url = f"{self.api_endpoints[network]}"
                params = {
                    "module": "account",
                    "action": "txlist",
                    "address": contract_address,
                    "startblock": 0,
                    "endblock": 99999999,
                    "page": 1,
                    "offset": limit,
                    "sort": "desc",
                    "apikey": self.api_keys[network]
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "1":
                        return data["result"]
            except Exception as e:
                self.logger.warning(f"API error: {e}. Falling back to browser scraping")
        
        # Fallback to browser scraping
        try:
            explorer_url = f"{self.explorers[network]}/txs?a={contract_address}"
            self.driver.get(explorer_url)
            time.sleep(3)
            
            transactions = []
            
            # Find transaction table
            txn_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            for row in txn_rows[:limit]:
                try:
                    columns = row.find_elements(By.TAG_NAME, "td")
                    if len(columns) >= 7:
                        txn = {
                            "hash": columns[1].text,
                            "method": columns[2].text,
                            "block": columns[3].text,
                            "age": columns[4].text,
                            "from": columns[5].text,
                            "to": columns[6].text,
                            "value": columns[7].text if len(columns) > 7 else "0"
                        }
                        transactions.append(txn)
                except:
                    continue
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting contract transactions: {e}")
            return []
    
    def get_nft_transfers(self, network, contract_address, token_id=None, limit=100):
        """Get NFT transfer events for a contract or specific token"""
        self.logger.info(f"Getting NFT transfers for contract {contract_address} on {network}")
        
        # Try API first
        if network in self.api_keys:
            try:
                url = f"{self.api_endpoints[network]}"
                params = {
                    "module": "account",
                    "action": "tokennfttx",
                    "contractaddress": contract_address,
                    "page": 1,
                    "offset": limit,
                    "sort": "desc",
                    "apikey": self.api_keys[network]
                }
                
                if token_id:
                    params["tokenid"] = token_id
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "1":
                        return data["result"]
            except Exception as e:
                self.logger.warning(f"API error: {e}. Falling back to browser scraping")
        
        # Fallback to browser scraping
        try:
            explorer_url = f"{self.explorers[network]}/token/{contract_address}"
            if token_id:
                explorer_url += f"?a={token_id}"
            
            self.driver.get(explorer_url)
            time.sleep(3)
            
            # Click on the "Transfers" tab if it exists
            try:
                transfers_tab = self.driver.find_element(By.XPATH, "//a[contains(text(), 'NFT Transfers')]")
                transfers_tab.click()
                time.sleep(2)
            except:
                pass
            
            transfers = []
            
            # Find transfers table
            transfer_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            for row in transfer_rows[:limit]:
                try:
                    columns = row.find_elements(By.TAG_NAME, "td")
                    if len(columns) >= 6:
                        transfer = {
                            "hash": columns[0].text,
                            "token_id": columns[1].text,
                            "age": columns[2].text,
                            "from": columns[3].text,
                            "to": columns[4].text,
                            "quantity": columns[5].text
                        }
                        transfers.append(transfer)
                except:
                    continue
            
            return transfers
            
        except Exception as e:
            self.logger.error(f"Error getting NFT transfers: {e}")
            return []