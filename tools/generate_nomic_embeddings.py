#!/usr/bin/env python3
"""
Script to generate embeddings using the nomic-ai/nomic-embed-code model.
"""
import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from code_search.model.nomic_embed import generate_embeddings_file

def main():
    # Define paths
    structures_file = os.path.join(project_root, "data", "structures.json")
    output_file = os.path.join(project_root, "data", "embeddings.json")
    
    # Check if structures.json exists
    if not os.path.exists(structures_file):
        print(f"Error: {structures_file} not found. Please make sure the file exists.")
        sys.exit(1)
    
    # Generate embeddings
    print(f"Generating embeddings using nomic-ai/nomic-embed-code model...")
    generate_embeddings_file(structures_file, output_file)
    print(f"Embeddings successfully saved to {output_file}")

if __name__ == "__main__":
    main() 