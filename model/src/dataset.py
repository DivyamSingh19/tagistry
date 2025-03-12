from torch.utils.data import Dataset
from PIL import Image

class SimilarImagePairsDataset(Dataset):
    def __init__(self, model, image_paths, transform=None):
        self.model = model
        self.image_paths = image_paths
        self.transform = transform
        self.pairs = self._generate_pairs()
        
    def _generate_pairs(self):
        """Generate pairs of similar and dissimilar images"""
        pairs = []
        # For each image, find its nearest neighbors and furthest neighbors
        for i, path in enumerate(self.image_paths):
            if path not in self.model.image_database["embeddings"]:
                continue
                
            emb_i = self.model.image_database["embeddings"][path]
            
            # Find similar and dissimilar pairs
            similarities = []
            for j, other_path in enumerate(self.image_paths):
                if i == j or other_path not in self.model.image_database["embeddings"]:
                    continue
                    
                emb_j = self.model.image_database["embeddings"][other_path]
                sim = torch.matmul(emb_i, emb_j.T).item()
                similarities.append((other_path, sim))
                
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Add positive pairs (similar images)
            for similar_path, _ in similarities[:3]:  # Top 3 most similar
                pairs.append((path, similar_path, 1))  # 1 for similar
                
            # Add negative pairs (dissimilar images)
            for dissimilar_path, _ in similarities[-3:]:  # 3 least similar
                pairs.append((path, dissimilar_path, 0))  # 0 for dissimilar
                
        return pairs
    
    def __len__(self):
        return len(self.pairs)
        
    def __getitem__(self, idx):
        path1, path2, label = self.pairs[idx]
        img1 = Image.open(path1)
        img2 = Image.open(path2)
        
        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)
            
        # Process through CLIP processor
        inputs1 = self.model.processor(images=img1, return_tensors="pt", padding=True)
        inputs2 = self.model.processor(images=img2, return_tensors="pt", padding=True)
        
        return inputs1, inputs2, torch.tensor(label, dtype=torch.float)