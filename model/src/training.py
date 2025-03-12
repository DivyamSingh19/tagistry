import torch
import os
from torch.utils.data import DataLoader
from PIL import Image
from .dataset import SimilarImagePairsDataset

def train_model(model, image_folder, num_epochs=5, batch_size=8, learning_rate=0.0001):
    """Train the model to better recognize similar images"""
    
    # First, add all images to the database without computing embeddings
    image_paths = []
    for root, _, files in os.walk(image_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(root, file)
                model.add_image(image_path, compute_embedding=False)
                image_paths.append(image_path)
    
    # Now compute all embeddings at once (more efficient)
    for path in image_paths:
        try:
            image = Image.open(path)
            embedding = model.get_image_embedding(image)
            model.image_database["embeddings"][path] = embedding
        except Exception as e:
            print(f"Error processing {path}: {e}")
    
    model.save_database()
    
    # Create dataset and dataloader
    dataset = SimilarImagePairsDataset(model, image_paths)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Set up optimizer
    optimizer = torch.optim.Adam(model.projection.parameters(), lr=learning_rate)
    criterion = torch.nn.BCEWithLogitsLoss()
    
    # Training loop
    model.projection.train()
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        for batch_idx, (inputs1, inputs2, labels) in enumerate(dataloader):
            optimizer.zero_grad()
            
            # Forward pass
            with torch.no_grad():
                features1 = model.model.get_image_features(**inputs1)
                features2 = model.model.get_image_features(**inputs2)
            
            # Apply projection layer
            proj_features1 = model.projection(features1)
            proj_features2 = model.projection(features2)
            
            # Normalize
            proj_features1 = proj_features1 / proj_features1.norm(dim=-1, keepdim=True)
            proj_features2 = proj_features2 / proj_features2.norm(dim=-1, keepdim=True)
            
            # Compute similarity
            similarity = torch.sum(proj_features1 * proj_features2, dim=1)
            
            # Compute loss
            loss = criterion(similarity, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"Epoch {epoch+1}/{num_epochs}, Batch {batch_idx}, Loss: {loss.item():.4f}")
        
        print(f"Epoch {epoch+1}/{num_epochs}, Average Loss: {epoch_loss/len(dataloader):.4f}")
    
    # After training, update all embeddings in the database
    model.projection.eval()
    for path in image_paths:
        try:
            image = Image.open(path)
            embedding = model.get_image_embedding(image)
            model.image_database["embeddings"][path] = embedding
        except:
            print(f"Error processing {path}")
    
    model.save_database()
    
    # Save the fine-tuned projection layer
    os.makedirs('models', exist_ok=True)
    torch.save(model.projection.state_dict(), "models/fine_tuned_projection.pth")
    
    return model

def add_new_images_and_retrain(model, new_image_folder, num_epochs=2):
    """Add new images to the database and retrain the model"""
    
    # Add new images to database
    new_image_paths = []
    for root, _, files in os.walk(new_image_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(root, file)
                if model.add_image(image_path):
                    new_image_paths.append(image_path)
    
    print(f"Added {len(new_image_paths)} new images to the database")
    
    # If we have new images, retrain
    if new_image_paths:
        # Combine with existing images
        all_paths = model.image_database["paths"]
        
        # Create dataset with all images
        dataset = SimilarImagePairsDataset(model, all_paths)
        dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
        
        # Set up optimizer
        optimizer = torch.optim.Adam(model.projection.parameters(), lr=0.0001)
        criterion = torch.nn.BCEWithLogitsLoss()
        
        # Training loop
        model.projection.train()
        for epoch in range(num_epochs):
            epoch_loss = 0.0
            for batch_idx, (inputs1, inputs2, labels) in enumerate(dataloader):
                optimizer.zero_grad()
                
                # Forward pass
                with torch.no_grad():
                    features1 = model.model.get_image_features(**inputs1)
                    features2 = model.model.get_image_features(**inputs2)
                
                # Apply projection layer
                proj_features1 = model.projection(features1)
                proj_features2 = model.projection(features2)
                
                # Normalize
                proj_features1 = proj_features1 / proj_features1.norm(dim=-1, keepdim=True)
                proj_features2 = proj_features2 / proj_features2.norm(dim=-1, keepdim=True)
                
                # Compute similarity
                similarity = torch.sum(proj_features1 * proj_features2, dim=1)
                
                # Compute loss
                loss = criterion(similarity, labels)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            print(f"Epoch {epoch+1}/{num_epochs}, Average Loss: {epoch_loss/len(dataloader):.4f}")
        
        # Update embeddings after fine-tuning
        model.projection.eval()
        for path in all_paths:
            try:
                image = Image.open(path)
                embedding = model.get_image_embedding(image)
                model.image_database["embeddings"][path] = embedding
            except:
                print(f"Error processing {path}")
        
        model.save_database()
    
    return model