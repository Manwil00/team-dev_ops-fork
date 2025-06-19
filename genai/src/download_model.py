#!/usr/bin/env python3
"""
Script to pre-download sentence transformer model for faster container startup.
"""

import os
import sys

def download_model():
    """Download the sentence transformer model with proper error handling."""
    try:
        print("Setting up model cache directories...")
        os.makedirs('/app/models', exist_ok=True)
        
        print("Downloading sentence transformer model: all-MiniLM-L6-v2")
        
        # Import and download model
        from sentence_transformers import SentenceTransformer
        
        # Download model to cache
        model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/models')
        
        print("✅ Model downloaded successfully!")
        print(f"Model cached at: {model._modules['0'].auto_model.config._name_or_path}")
        
        # Verify model works
        test_embedding = model.encode(["test sentence"])
        print(f"✅ Model verification successful! Embedding shape: {test_embedding.shape}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Required packages may not be installed correctly.")
        return False
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        print("Model will be downloaded on first API use.")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1) 