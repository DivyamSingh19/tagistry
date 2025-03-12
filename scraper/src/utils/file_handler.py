import os
import json
import shutil

class FileHandler:
    """Handles file operations for scraper data"""
    
    def __init__(self, logger):
        self.logger = logger
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            "data/raw",
            "data/processed",
            "data/hashes"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_json(self, data, filepath):
        """Save data as JSON to the specified file path"""
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Data saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {filepath}: {str(e)}")
            return False
    
    def load_json(self, filepath):
        """Load JSON data from the specified file path"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading data from {filepath}: {str(e)}")
            return None