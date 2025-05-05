#!/usr/bin/env python3

import os
import json
import sys
from pathlib import Path
import glob
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

# Add the code_search module to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_search.index.textifier import textify
from code_search.config import QDRANT_NLU_COLLECTION_NAME, ENCODER_SIZE, QDRANT_CODE_COLLECTION_NAME

# Set up paths
QURAN_CODEBASE_PATH = "/Users/devsufi/Documents/GitHub/Quran-Majeed/lib"
DATA_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data"
DATA_PATH.mkdir(exist_ok=True)
STRUCTURES_JSON_PATH = DATA_PATH / "structures.json"

# Set up Qdrant client
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

print(f"Connecting to Qdrant at: {QDRANT_URL}")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)

# Define collection names and sizes
COLLECTION_NAME_ALL_MINILM = QDRANT_NLU_COLLECTION_NAME
VECTOR_SIZE_ALL_MINILM = ENCODER_SIZE
COLLECTION_NAME_UNIXCODER = QDRANT_CODE_COLLECTION_NAME
VECTOR_SIZE_UNIXCODER = 768  # UniXcoder dimension size

# Create collections
def setup_collections():
    print("Setting up collections...")
    
    # Helper function to create a collection if it doesn't exist
    def create_collection_if_not_exists(collection_name, vector_size):
        try:
            if not client.collection_exists(collection_name):
                print(f"Creating collection: {collection_name}")
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
            else:
                print(f"Collection {collection_name} already exists, truncating...")
                client.delete(collection_name=collection_name, points_selector=models.Filter())
        except Exception as e:
            print(f"Error with collection {collection_name}: {e}")
            # Create it anyway
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
            except Exception as inner_e:
                print(f"Failed to create collection {collection_name}: {inner_e}")
    
    # Create both collections
    create_collection_if_not_exists(COLLECTION_NAME_ALL_MINILM, VECTOR_SIZE_ALL_MINILM)
    create_collection_if_not_exists(COLLECTION_NAME_UNIXCODER, VECTOR_SIZE_UNIXCODER)

# Process and index Flutter files
def process_flutter_files():
    print("Processing Flutter files...")
    
    # Load Sentence Transformer models
    model_all_minilm = SentenceTransformer("all-MiniLM-L6-v2")
    model_unixcoder = SentenceTransformer("microsoft/unixcoder-base")
    
    # Get all Dart files
    dart_files = glob.glob(f"{QURAN_CODEBASE_PATH}/**/*.dart", recursive=True)
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
                        
                        # Adapt the structure to match what textify expects
                        signature = lines[start_line].strip()
                        code_type = "Class" if "class " in lines[start_line] else "Function"
                        name = signature.split("class ")[1].split("{")[0].strip() if "class " in signature else signature.split("(")[0].split(" ")[-1].strip()
                        
                        structure = {
                            "code_type": code_type,
                            "name": name,
                            "signature": signature,
                            "docstring": docstring,
                            "module": module,
                            "line": start_line + 1,
                            "line_from": start_line + 1,
                            "line_to": end_line + 1,
                            "context": {
                                "module": module,
                                "file_path": relative_path,
                                "file_name": file_name,
                                "struct_name": None,
                                "snippet": code_segment
                            }
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
    index_structures(code_structures, model_all_minilm, model_unixcoder)

# Index structures to Qdrant
def index_structures(structures, model_all_minilm, model_unixcoder):
    print("Indexing structures...")
    
    all_minilm_points = []
    unixcoder_points = []
    
    for i, structure in enumerate(tqdm(structures)):
        try:
            # Create text for all-MiniLM-L6-v2
            text = textify(structure)
            
            # Create embeddings
            all_minilm_vector = model_all_minilm.encode(text).tolist()
            unixcoder_vector = model_unixcoder.encode(structure["context"]["snippet"]).tolist()
            
            # Create Qdrant points
            all_minilm_points.append(
                models.PointStruct(
                    id=i,
                    vector=all_minilm_vector,
                    payload=structure
                )
            )
            
            unixcoder_points.append(
                models.PointStruct(
                    id=i,
                    vector=unixcoder_vector,
                    payload=structure
                )
            )
        except Exception as e:
            print(f"Error encoding structure {i}: {e}")
    
    # Upload points in batches
    batch_size = 100
    
    print(f"Uploading {len(all_minilm_points)} points to {COLLECTION_NAME_ALL_MINILM}")
    for i in range(0, len(all_minilm_points), batch_size):
        batch = all_minilm_points[i:i+batch_size]
        try:
            client.upsert(
                collection_name=COLLECTION_NAME_ALL_MINILM,
                points=batch
            )
        except Exception as e:
            print(f"Error uploading batch {i//batch_size} to {COLLECTION_NAME_ALL_MINILM}: {e}")
        
    print(f"Uploading {len(unixcoder_points)} points to {COLLECTION_NAME_UNIXCODER}")
    for i in range(0, len(unixcoder_points), batch_size):
        batch = unixcoder_points[i:i+batch_size]
        try:
            client.upsert(
                collection_name=COLLECTION_NAME_UNIXCODER,
                points=batch
            )
        except Exception as e:
            print(f"Error uploading batch {i//batch_size} to {COLLECTION_NAME_UNIXCODER}: {e}")

if __name__ == "__main__":
    # Set up collections
    setup_collections()
    
    # Process and index files
    process_flutter_files() 