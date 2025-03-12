import os
import matplotlib.pyplot as plt
from PIL import Image

def create_directory_structure():
    """Create the necessary directory structure for the project"""
    directories = [
        "data/initial_images",
        "data/new_images",
        "data/database",
        "models"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("Directory structure created successfully")

def display_similar_images(query_image, similar_images, figsize=(15, 10)):
    """Display the query image and its similar images"""
    n = len(similar_images) + 1  # +1 for query image
    fig, axes = plt.subplots(1, n, figsize=figsize)
    
    # Display query image
    axes[0].imshow(query_image)
    axes[0].set_title("Query Image")
    axes[0].axis('off')
    
    # Display similar images
    for i, (path, similarity) in enumerate(similar_images):
        img = Image.open(path)
        axes[i+1].imshow(img)
        axes[i+1].set_title(f"Similarity: {similarity:.4f}")
        axes[i+1].axis('off')
    
    plt.tight_layout()
    plt.show()

def load_model_weights(model, weights_path="models/fine_tuned_projection.pth"):
    """Load saved weights for the projection layer"""
    if os.path.exists(weights_path):
        model.projection.load_state_dict(torch.load(weights_path))
        print(f"Successfully loaded weights from {weights_path}")
    else:
        print(f"No weights found at {weights_path}")
    
    return model