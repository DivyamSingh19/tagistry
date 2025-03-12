import torch
from PIL import Image
import requests
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import hashlib
from io import BytesIO
import os
import pickle
import torch.nn as nn

class ImageSimilarityModel:
    def __init__(self, model_name="openai/clip-vit-base-patch32", database_path="data/database/image_database.pkl"):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.database_path = database_path
        self.image_database = self._load_database()
        
        
        self.projection = nn.Linear(512, 512)  # Assuming CLIP outputs 512-dim vectors
        
    def _load_database(self):
        if os.path.exists(self.database_path):
            with open(self.database_path, 'rb') as f:
                return pickle.load(f)
        return {"embeddings": {}, "hashes": {}, "paths": []}
        
    def save_database(self):
        
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        with open(self.database_path, 'wb') as f:
            pickle.dump(self.image_database, f)
            
    def get_image_embedding(self, image):
        inputs = self.processor(images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            
         
        image_features = self.projection(image_features)
        return image_features / image_features.norm(dim=-1, keepdim=True)
    
    def get_image_hash(self, image):
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return hashlib.sha256(img_byte_arr).hexdigest()
    
    def add_image(self, image_path, compute_embedding=True):
        """Add an image to the database"""
        try:
            image = Image.open(image_path)
            image_hash = self.get_image_hash(image)
            
             
            self.image_database["hashes"][image_path] = image_hash
            if image_path not in self.image_database["paths"]:
                self.image_database["paths"].append(image_path)
            
            
            if compute_embedding:
                embedding = self.get_image_embedding(image)
                self.image_database["embeddings"][image_path] = embedding
                
            self.save_database()
            return True
        except Exception as e:
            print(f"Error adding image {image_path}: {e}")
            return False
    
    def find_similar_images(self, query_image, top_k=5):
        """Find similar images to the query image"""
        query_embedding = self.get_image_embedding(query_image)
        query_hash = self.get_image_hash(query_image)
        
        
        exact_matches = []
        for path, hash_val in self.image_database["hashes"].items():
            if hash_val == query_hash:
                exact_matches.append((path, 1.0))
                
        
        if exact_matches:
            return exact_matches
            
         
        similarities = []
        for path, embedding in self.image_database["embeddings"].items():
            sim_score = torch.matmul(query_embedding, embedding.T).item()
            similarities.append((path, sim_score))
            
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]