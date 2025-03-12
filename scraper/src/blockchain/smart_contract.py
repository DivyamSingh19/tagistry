import json
import os
from web3 import Web3

class ContentProtectionContract:
    """Interface for the content protection smart contract"""
    
    def __init__(self, web3_connector, contract_address, abi_path):
        self.w3 = web3_connector
        self.logger = web3_connector.logger
        self.contract_address = contract_address
        
        # Load contract
        self.contract = self.w3.get_contract(contract_address, abi_path)
        if not self.contract:
            self.logger.error(f"Failed to load content protection contract at {contract_address}")
    
    def register_content(self, content_hash, metadata):
        """Register content hash on the blockchain"""
        if not self.contract:
            return None
            
        try:
            tx_hash = self.w3.register_content_hash(
                self.contract_address, 
                self.contract_abi_path, 
                content_hash, 
                metadata
            )
            return tx_hash
        except Exception as e:
            self.logger.error(f"Error registering content: {e}")
            return None
    
    def verify_content(self, content_hash):
        """Check if content hash is registered"""
        if not self.contract:
            return False
            
        try:
            return self.w3.verify_content_hash(
                self.contract_address,
                self.contract_abi_path,
                content_hash
            )
        except Exception as e:
            self.logger.error(f"Error verifying content: {e}")
            return False
    
    def get_content_details(self, content_hash):
        """Get registered content details"""
        if not self.contract:
            return None
            
        try:
            # This is a read operation, so we can call it directly
            details = self.contract.functions.getContentDetails(content_hash).call()
            
            # Parse the result based on your contract structure
            # This is an example - adapt to your actual contract return structure
            return {
                "owner": details[0],
                "timestamp": details[1],
                "metadata": json.loads(details[2]) if details[2] else {},
                "status": details[3]
            }
        except Exception as e:
            self.logger.error(f"Error getting content details: {e}")
            return None
    
    def report_content_violation(self, content_hash, violation_url, violation_type):
        """Report unauthorized use of content"""
        if not self.contract:
            return None
            
        try:
            # Build transaction to report violation
            nonce = self.w3.w3.eth.get_transaction_count(self.w3.address)
            
            # Estimate gas for the transaction
            gas_estimate = self.contract.functions.reportViolation(
                content_hash,
                violation_url,
                violation_type
            ).estimate_gas({'from': self.w3.address})
            
            # Build transaction
            txn = self.contract.functions.reportViolation(
                content_hash,
                violation_url,
                violation_type
            ).build_transaction({
                'chainId': self.w3.w3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': self.w3.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = self.w3.w3.eth.account.sign_transaction(txn, private_key=self.w3.private_key)
            tx_hash = self.w3.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.w3.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.logger.info(f"Violation reported. Tx hash: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            self.logger.error(f"Error reporting violation: {e}")
            return None