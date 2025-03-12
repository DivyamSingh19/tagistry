import hashlib
import json
import os
from datetime import datetime
from PIL import Image
import io
import requests

class HashGenerator:
    """Generates hashes for Pinterest content"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def generate_content_hash(self, content):
        """Generate a SHA-256 hash for content"""
        try:
            # Convert to JSON string for consistent hashing
            if isinstance(content, dict) or isinstance(content, list):
                content = json.dumps(content, sort_keys=True)
            elif not isinstance(content, str):
                content = str(content)
                
            # Generate hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            return content_hash
            
        except Exception as e:
            self.logger.error(f"Error generating content hash: {str(e)}")
            return None
    
    def generate_image_hash(self, image_path=None, image_url=None):
        """
        Generate hash for image data using either a local path or remote URL
        This function can use perceptual hashing for better image comparisons
        """
        try:
            img = None
            
            # Load image from local path
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                
            # Or download image from URL
            elif image_url:
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                else:
                    self.logger.warning(f"Failed to download image: HTTP {response.status_code}")
                    return None
            else:
                self.logger.error("No image path or URL provided")
                return None
                
            # Generate hash from image data
            if img:
                # Convert to RGB if necessary to ensure consistent processing
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to small dimensions for faster hashing
                img = img.resize((32, 32), Image.LANCZOS)
                
                # Convert to bytes and hash
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_hash = hashlib.sha256(img_bytes.getvalue()).hexdigest()
                
                return img_hash
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating image hash: {str(e)}")
            return None
    
    def create_pin_hash_record(self, pin_data):
        """Create a comprehensive hash record for a Pinterest pin"""
        try:
            # Generate hash for pin metadata
            pin_metadata = {
                "pin_id": pin_data.get("pin_id", ""),
                "description": pin_data.get("description", ""),
                "title": pin_data.get("title", ""),
                "creator": pin_data.get("creator", ""),
                "pin_url": pin_data.get("pin_url", ""),
            }
            metadata_hash = self.generate_content_hash(pin_metadata)
            
            # Generate hash for pin image
            image_hash = None
            if "local_path" in pin_data and pin_data["local_path"]:
                image_hash = self.generate_image_hash(image_path=pin_data["local_path"])
            elif "image_url" in pin_data and pin_data["image_url"]:
                image_hash = self.generate_image_hash(image_url=pin_data["image_url"])
            
            # Create complete hash record
            hash_record = {
                "pin_id": pin_data.get("pin_id", ""),
                "timestamp": datetime.now().isoformat(),
                "metadata_hash": metadata_hash,
                "image_hash": image_hash,
                "combined_hash": self.generate_content_hash(f"{metadata_hash}:{image_hash}") if image_hash else metadata_hash,
                "source": pin_data.get("pin_url", "")
            }
            
            return hash_record
            
        except Exception as e:
            self.logger.error(f"Error creating pin hash record: {str(e)}")
            return None