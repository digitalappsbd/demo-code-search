#!/usr/bin/env python3
"""
Script to generate embeddings using multiple model options.
This script provides a unified interface to generate embeddings
using one of the supported embedding models:
- nomic-ai/nomic-embed-code
- Qodo/Qodo-Embed-1-1.5B

Features:
- Progress tracking
- Checkpoint logic
- Optional GPU acceleration
- Resume capability for interrupted jobs
- Model selection
"""
import os
import sys
import argparse
import json
import time
from pathlib import Path
from tqdm import tqdm

# Add the project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Import model providers
from code_search.model.nomic_embed import NomicEmbeddingsProvider
from code_search.model.qodo_embed import QodoEmbeddingsProvider

# Available models
AVAILABLE_MODELS = {
    "nomic": {
        "name": "nomic-ai/nomic-embed-code",
        "provider_class": NomicEmbeddingsProvider,
        "default_output": "embeddings.json"
    },
    "qodo": {
        "name": "Qodo/Qodo-Embed-1-1.5B",
        "provider_class": QodoEmbeddingsProvider,
        "default_output": "qodo_embeddings.json"
    }
}

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate embeddings using various embedding models")
    parser.add_argument("--model", type=str, choices=list(AVAILABLE_MODELS.keys()), default="nomic",
                      help=f"Embedding model to use (default: nomic)")
    parser.add_argument("--force", action="store_true", help="Force regeneration of all embeddings")
    parser.add_argument("--gpu", action="store_true", help="Use GPU for embedding generation if available")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for embedding generation")
    parser.add_argument("--checkpoint-interval", type=int, default=10, help="Save checkpoints after processing this many items")
    parser.add_argument("--output", type=str, help="Output filename (defaults to model-specific name)")
    args = parser.parse_args()
    
    # Select model config
    model_config = AVAILABLE_MODELS[args.model]
    model_name = model_config["name"]
    provider_class = model_config["provider_class"]
    
    # Set default output filename if not specified
    if not args.output:
        args.output = model_config["default_output"]
    
    # Define paths
    structures_file = os.path.join(project_root, "data", "structures.json")
    output_file = os.path.join(project_root, "data", args.output)
    checkpoint_file = os.path.join(project_root, "data", f"{args.output}_checkpoint.json")
    
    # Check if structures.json exists
    if not os.path.exists(structures_file):
        print(f"Error: {structures_file} not found. Please make sure the file exists.")
        sys.exit(1)
    
    # Load existing embeddings if they exist (for resuming)
    embeddings = {}
    processed_ids = set()
    
    if os.path.exists(output_file) and not args.force:
        try:
            with open(output_file, 'r') as f:
                embeddings = json.load(f)
                
            # Build a set of already processed IDs
            for file_path, file_embeddings in embeddings.items():
                # Check if file_embeddings is a dictionary
                if isinstance(file_embeddings, dict):
                    for struct_id in file_embeddings.keys():
                        processed_ids.add(struct_id)
                # Handle the case where file_embeddings might be a list
                elif isinstance(file_embeddings, list):
                    for embedding in file_embeddings:
                        if isinstance(embedding, dict) and 'id' in embedding:
                            processed_ids.add(embedding['id'])
                            
            print(f"Loaded {len(processed_ids)} existing embeddings from {output_file}")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing embeddings file. Starting fresh.")
            embeddings = {}
    
    # Check for checkpoint file
    if os.path.exists(checkpoint_file) and not args.force:
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                
            # Merge checkpoint data with existing embeddings
            for file_path, file_embeddings in checkpoint_data.items():
                if file_path not in embeddings:
                    embeddings[file_path] = {}
                
                # Check if file_embeddings is a dictionary
                if isinstance(file_embeddings, dict):
                    for struct_id, embedding in file_embeddings.items():
                        embeddings[file_path][struct_id] = embedding
                        processed_ids.add(struct_id)
                # Handle the case where file_embeddings might be a list
                elif isinstance(file_embeddings, list):
                    if not isinstance(embeddings[file_path], list):
                        embeddings[file_path] = []
                    for embedding in file_embeddings:
                        embeddings[file_path].append(embedding)
                        if isinstance(embedding, dict) and 'id' in embedding:
                            processed_ids.add(embedding['id'])
                            
            print(f"Loaded checkpoint with {len(processed_ids)} processed entries")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse checkpoint file. Ignoring it.")
    
    # Generate embeddings
    print(f"Generating embeddings using {model_name} model...")
    
    # Initialize the embedding provider
    device = "cuda" if args.gpu else "cpu"
    provider = provider_class(device=device)
    
    # Load the code structures (as a list)
    with open(structures_file, 'r') as f:
        structures_list = json.load(f)
    
    # Filter out structures that have already been processed
    to_process = []
    for structure in structures_list:
        file_path = structure["file_path"]
        struct_id = f"{file_path}_{structure['line_from']}_{structure['line_to']}"
        
        if args.force or struct_id not in processed_ids:
            structure["struct_id"] = struct_id
            to_process.append(structure)
    
    # Process each structure in the list with progress bar
    print(f"Processing {len(to_process)} out of {len(structures_list)} code structures...")
    
    # Create a progress bar with more information
    pbar = tqdm(
        total=len(to_process), 
        desc="Generating embeddings",
        bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    )
    
    # Process in batches for checkpointing
    checkpoint_counter = 0
    start_time = time.time()
    
    # Track and report progress periodically
    processed_count = 0
    total_count = len(to_process)
    
    for structure in to_process:
        file_path = structure["file_path"]
        struct_id = structure["struct_id"]
        
        # Get code and docstring
        code = structure.get("snippet", "")
        docstring = structure.get("docstring", "")
        
        # Generate embedding
        embedding = provider.embed_code(code=code, docstring=docstring)
        
        # Store the embedding by file path
        if file_path not in embeddings:
            embeddings[file_path] = {}
        
        # Ensure embeddings[file_path] is a dictionary
        if not isinstance(embeddings[file_path], dict):
            embeddings[file_path] = {}
            
        embeddings[file_path][struct_id] = embedding
        
        # Update progress bar
        pbar.update(1)
        processed_count += 1
        
        # Output progress percentage for backend to capture
        if processed_count % 5 == 0 or processed_count == total_count:
            progress_pct = (processed_count / total_count) * 100
            print(f"Progress: {progress_pct:.1f}% ({processed_count}/{total_count})")
        
        # Save checkpoint periodically
        checkpoint_counter += 1
        if checkpoint_counter >= args.checkpoint_interval:
            with open(checkpoint_file, 'w') as f:
                json.dump(embeddings, f)
            checkpoint_counter = 0
            
            # Display processing speed
            elapsed = time.time() - start_time
            items_per_second = pbar.n / elapsed if elapsed > 0 else 0
            pbar.set_postfix({"speed": f"{items_per_second:.2f} items/s"})
    
    # Close the progress bar
    pbar.close()
    
    # Save the embeddings to the output file
    with open(output_file, 'w') as f:
        json.dump(embeddings, f)
    
    # Remove checkpoint file if successful
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        
    print(f"Embeddings successfully saved to {output_file}")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main() 