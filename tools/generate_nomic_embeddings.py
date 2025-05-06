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

from code_search.model.nomic_embed import NomicEmbeddingsProvider
import json

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
    
    # Initialize the embedding provider
    provider = NomicEmbeddingsProvider()
    
    # Dictionary to store the embeddings
    embeddings = {}
    
    # Load the code structures (as a list)
    with open(structures_file, 'r') as f:
        structures_list = json.load(f)
    
    # Process each structure in the list
    print(f"Processing {len(structures_list)} code structures...")
    
    for structure in structures_list:
        file_path = structure["file_path"]
        struct_id = f"{file_path}_{structure['line_from']}_{structure['line_to']}"
        
        # Get code and docstring
        code = structure.get("snippet", "")
        docstring = structure.get("docstring", "")
        
        # Generate embedding
        embedding = provider.embed_code(code=code, docstring=docstring)
        
        # Store the embedding by file path
        if file_path not in embeddings:
            embeddings[file_path] = {}
        
        embeddings[file_path][struct_id] = embedding
    
    # Save the embeddings to a file
    with open(output_file, 'w') as f:
        json.dump(embeddings, f)
    
    print(f"Embeddings successfully saved to {output_file}")

if __name__ == "__main__":
    main() 