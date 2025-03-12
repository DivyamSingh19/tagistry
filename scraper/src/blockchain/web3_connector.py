import os
import json
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import ipfshttpclient

class Web3Connector:
    """Connect to blockchain networks and interact with smart contracts"""
    
    def __init__(self, logger, network="ethereum"):
        self.logger = logger
        load_dotenv()
        
        # Set up provider based on network
        if network == "ethereum":
            self.provider_url = os.environ.get('ETH_PROVIDER_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
        elif network == "polygon":
            self.provider_url = os.environ.get('POLYGON_PROVIDER_URL', 'https://polygon-rpc.com')
        elif network == "bsc":
            self.provider_url = os.environ.get('BSC_PROVIDER_URL', 'https://bsc-dataseed.binance.org/')
        else:
            self.provider_url = os.environ.get('ETH_PROVIDER_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.provider_url))
        self.logger.info(f"Connected to {network}: {self.w3.is_connected()}")
        
        # Set account from private key (if available)
        self.private_key = os.environ.get('ETH_PRIVATE_KEY')
        self.account = None
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            self.address = self.account.address
            self.logger.info(f"Account set up: {self.address}")
        
        # IPFS client for decentralized storage
        try:
            self.ipfs_client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
            self.logger.info("Connected to local IPFS node")
        except:
            self.ipfs_client = None
            self.logger.warning("No local IPFS node found, using gateway instead")
    
    def get_contract(self, address, abi_path):
        """Load a smart contract instance"""
        try:
            with open(abi_path, 'r') as f:
                contract_abi = json.load(f)
            
            contract = self.w3.eth.contract(address=address, abi=contract_abi)
            return contract
        except Exception as e:
            self.logger.error(f"Error loading contract: {e}")
            return None
    
    def register_content_hash(self, contract_address, abi_path, content_hash, metadata=None):
        """Register a content hash on the blockchain"""
        try:
            # Load the contract
            contract = self.get_contract(contract_address, abi_path)
            if not contract:
                return None
                
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.address)
            
            # Estimate gas for the transaction
            gas_estimate = contract.functions.registerContentHash(
                content_hash,
                json.dumps(metadata) if metadata else ""
            ).estimate_gas({'from': self.address})
            
            # Build transaction
            txn = contract.functions.registerContentHash(
                content_hash,
                json.dumps(metadata) if metadata else ""
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.logger.info(f"Content hash registered on blockchain. Tx hash: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            self.logger.error(f"Error registering content hash: {e}")
            return None
    
    def verify_content_hash(self, contract_address, abi_path, content_hash):
        """Verify if a content hash exists on the blockchain"""
        try:
            # Load the contract
            contract = self.get_contract(contract_address, abi_path)
            if not contract:
                return False
                
            # Call the verification method
            is_registered = contract.functions.verifyContentHash(content_hash).call()
            
            return is_registered
            
        except Exception as e:
            self.logger.error(f"Error verifying content hash: {e}")
            return False
    
    def upload_to_ipfs(self, file_path=None, content=None):
        """Upload content or file to IPFS"""
        try:
            if not self.ipfs_client:
                self.logger.error("No IPFS client available")
                return None
                
            if file_path and os.path.exists(file_path):
                # Upload file
                result = self.ipfs_client.add(file_path)
                ipfs_hash = result['Hash']
                self.logger.info(f"File uploaded to IPFS: {ipfs_hash}")
                return ipfs_hash
            elif content:
                # Upload content
                result = self.ipfs_client.add_str(content)
                self.logger.info(f"Content uploaded to IPFS: {result}")
                return result
            else:
                self.logger.error("No file or content provided for IPFS upload")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading to IPFS: {e}")
            return None