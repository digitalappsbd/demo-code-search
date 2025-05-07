#!/usr/bin/env python3

import os
import json
import sys
import glob
import hashlib
import numpy as np
import argparse
from pathlib import Path
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Parse arguments
parser = argparse.ArgumentParser(description='Index Quran codebase structures')
parser.add_argument('--target-dir', type=str, default="/Users/devsufi/Documents/GitHub/Quran-Majeed/lib",
                    help='Target directory to process')
parser.add_argument('--pattern', type=str, default="**/*.dart",
                    help='File pattern to process')
parser.add_argument('--max-lines', type=int, default=500,
                    help='Maximum lines per code block')
parser.add_argument('--force', action='store_true',
                    help='Force regeneration even if structures exist')
args = parser.parse_args()

# Set up paths
QURAN_CODEBASE_PATH = args.target_dir
DATA_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data"
DATA_PATH.mkdir(exist_ok=True)
STRUCTURES_JSON_PATH = DATA_PATH / "structures.json"

print(f"Using codebase path: {QURAN_CODEBASE_PATH}")

# Set up Qdrant client
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

print(f"Connecting to Qdrant at: {QDRANT_URL}")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)

# Define collection names and sizes
COLLECTION_NAME = "quran-majeed-code"
VECTOR_SIZE = 768  # A fixed size that we'll create with our custom encoding

# Create collections
def setup_collections():
    print("Setting up collections...")
    
    # Create a single collection for all code snippets
    try:
        if client.collection_exists(COLLECTION_NAME):
            print(f"Collection {COLLECTION_NAME} already exists, truncating...")
            client.delete(collection_name=COLLECTION_NAME, points_selector=models.Filter())
        else:
            print(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
    except Exception as e:
        print(f"Error with collection {COLLECTION_NAME}: {e}")
        try:
            print(f"Trying to create collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception as inner_e:
            print(f"Failed to create collection {COLLECTION_NAME}: {inner_e}")

# Simple encoding function using hash of text
def simple_encode(text, size=VECTOR_SIZE):
    """Create a simple vector encoding from text using hashing."""
    # Use a hash function to convert the text to a fixed-length byte array
    text_hash = hashlib.sha256(text.encode('utf-8')).digest()
    
    # Convert the byte array to a numpy array of floats normalized to [-1, 1]
    array = np.array([float(b) / 127.0 - 1.0 for b in text_hash])
    
    # Repeat or truncate to get the desired vector size
    if len(array) < size:
        repeats = size // len(array) + 1
        array = np.tile(array, repeats)[:size]
    else:
        array = array[:size]
    
    # Apply a simple transformation to make the vector more meaningful
    # (this is a very naive approach but helps spread the vectors in the embedding space)
    positions = np.arange(size)
    array = array * np.sin(positions / 10.0)
    
    # Normalize to unit length for cosine similarity
    array = array / np.linalg.norm(array)
    
    return array.tolist()

# Process and index Flutter files
def process_flutter_files():
    print("Processing Flutter files...")
    
    # Get all files matching the pattern
    file_pattern = args.pattern if args.pattern.startswith('**') else f"**/{args.pattern}"
    dart_files = glob.glob(f"{QURAN_CODEBASE_PATH}/{file_pattern}", recursive=True)
    print(f"Found {len(dart_files)} files to process")
    code_structures = []
    
    for file_path in tqdm(dart_files):
        try:
            relative_path = os.path.relpath(file_path, start=QURAN_CODEBASE_PATH)
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Extract file parts
            file_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            module = os.path.basename(dir_path) if dir_path else ""
            
            # Process code line by line
            lines = code.split('\n')
            line_index = 0
            
            while line_index < len(lines):
                # Look for class or function definitions
                if line_index < len(lines) and ('class ' in lines[line_index] or 
                                              'void ' in lines[line_index] or 
                                              'Future<' in lines[line_index] or
                                              'Stream<' in lines[line_index] or
                                              'Widget ' in lines[line_index]):
                    start_line = line_index
                    # Look for opening brace
                    brace_count = 0
                    end_line = start_line
                    
                    # Collect docstring if any (usually before the definition)
                    docstring = ""
                    if start_line > 0 and "///" in lines[start_line - 1]:
                        comment_lines = []
                        i = start_line - 1
                        while i >= 0 and "///" in lines[i]:
                            comment_lines.insert(0, lines[i].strip("/ "))
                            i -= 1
                        docstring = "\n".join(comment_lines)
                    
                    # Find the end of the definition
                    while end_line < len(lines):
                        line = lines[end_line]
                        brace_count += line.count('{') - line.count('}')
                        if brace_count <= 0 and '{' in line:
                            break
                        end_line += 1
                    
                    # Check if we found a complete definition
                    if end_line < len(lines) and '{' in lines[end_line]:
                        # Find matching closing brace
                        brace_count = 1  # We've found an opening brace
                        end_line += 1
                        
                        while end_line < len(lines) and brace_count > 0:
                            line = lines[end_line]
                            brace_count += line.count('{') - line.count('}')
                            end_line += 1
                        
                        # Adjust for over-counting
                        if brace_count <= 0:
                            end_line -= 1
                        
                        # Extract the code segment
                        code_segment = "\n".join(lines[start_line:end_line+1])
                        
                        # Skip if code segment is too long
                        if len(lines[start_line:end_line+1]) > args.max_lines:
                            line_index = end_line
                            continue
                        
                        # Create structure
                        structure_type = "class" if "class " in lines[start_line] else "function"
                        name = lines[start_line].split("class ")[1].split("{")[0].strip() if "class " in lines[start_line] else lines[start_line].split("(")[0].split(" ")[-1].strip()
                        
                        structure = {
                            "structure_type": structure_type,
                            "name": name,
                            "docstring": docstring,
                            "module": module,
                            "file_path": relative_path,
                            "file_name": file_name,
                            "line": start_line + 1,
                            "line_from": start_line + 1,
                            "line_to": end_line + 1,
                            "snippet": code_segment
                        }
                        
                        code_structures.append(structure)
                        line_index = end_line
                
                line_index += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Save structures to file
    with open(STRUCTURES_JSON_PATH, 'w') as f:
        json.dump(code_structures, f)
    
    print(f"Found {len(code_structures)} code structures")
    
    # Index the structures
    index_structures(code_structures)

# Index structures to Qdrant
def index_structures(structures):
    print("Indexing structures...")
    
    points = []
    
    for i, structure in enumerate(tqdm(structures)):
        try:
            # Create searchable text representation
            searchable_text = f"{structure['structure_type']} {structure['name']} {structure['docstring']} {structure['module']} {structure['file_path']}"
            
            # Create simple vector encoding
            vector = simple_encode(searchable_text + " " + structure['snippet'])
            
            # Create Qdrant point
            points.append(
                models.PointStruct(
                    id=i,
                    vector=vector,
                    payload=structure
                )
            )
        except Exception as e:
            print(f"Error encoding structure {i}: {e}")
    
    # Upload points in batches
    batch_size = 100
    
    print(f"Uploading {len(points)} points to {COLLECTION_NAME}")
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1) // batch_size}")
        except Exception as e:
            print(f"Error uploading batch {i//batch_size} to {COLLECTION_NAME}: {e}")

if __name__ == "__main__":
    # Check if we should skip generation if structure exists
    if not args.force and os.path.exists(STRUCTURES_JSON_PATH):
        print(f"Structure file {STRUCTURES_JSON_PATH} already exists. Use --force to regenerate.")
        sys.exit(0)
        
    # Set up collections
    setup_collections()
    
    # Process and index files
    process_flutter_files() 