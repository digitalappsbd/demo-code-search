import os
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Set up paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "qodo_embeddings.json")
STRUCTURES_FILE = os.path.join(DATA_DIR, "structures.json")

# Vector size for encoding
VECTOR_SIZE = 768

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
    positions = np.arange(size)
    array = array * np.sin(positions / 10.0)
    
    # Normalize to unit length for cosine similarity
    array = array / np.linalg.norm(array)
    
    return array.tolist()

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_structures():
    """Load code structures from file."""
    if os.path.exists(STRUCTURES_FILE):
        with open(STRUCTURES_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_embeddings():
    """Load embeddings from file."""
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def search(query: str, limit: int = 100, embeddings_provider=None) -> List[Dict[str, Any]]:
    """Search for code structures matching the query."""
    # Load structures and embeddings
    structures = load_structures()
    
    if not structures:
        return []
    
    # Create query vector - either using the provided embeddings_provider or fallback to simple_encode
    if embeddings_provider:
        print(f"Using embeddings provider: {embeddings_provider.model_name}")
        query_vector = embeddings_provider.embed_query(query)
        # Load our pre-calculated embeddings for structures
        embeddings = load_embeddings()
    else:
        print("Using fallback simple embedding")
        query_vector = simple_encode(query)
        # Convert structure dict to list for compatibility with the old code
        structure_list = []
        for file_path, file_info in structures.items():
            for func_info in file_info.get("functions", []):
                structure_list.append({
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "name": func_info.get("name", ""),
                    "structure_type": "function",
                    "module": os.path.dirname(file_path),
                    "docstring": func_info.get("docstring", ""),
                    "snippet": func_info.get("code", ""),
                    "line": func_info.get("line", 0),
                    "line_from": func_info.get("line_from", 0),
                    "line_to": func_info.get("line_to", 0),
                })
        structures = structure_list
        
        # Create simple embeddings for each structure
        embeddings = {}
        for idx, structure in enumerate(structures):
            structure_text = f"{structure.get('name', '')} {structure.get('docstring', '')} {structure.get('snippet', '')}"
            embeddings[str(idx)] = simple_encode(structure_text)
    
    # Calculate similarity scores
    results = []
    
    if embeddings_provider:
        # Use the newer data format where structures is a dict of file paths
        for file_path, file_info in structures.items():
            file_embeddings = embeddings.get(file_path, {})
            
            for func_info in file_info.get("functions", []):
                func_id = func_info.get("id")
                
                if func_id in file_embeddings:
                    similarity = cosine_similarity(query_vector, file_embeddings[func_id])
                    
                    if similarity > 0.5:  # Higher threshold for better results
                        # Create a structure object for the frontend
                        structure = {
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "name": func_info.get("name", ""),
                            "structure_type": "function",
                            "module": os.path.dirname(file_path),
                            "docstring": func_info.get("docstring", ""),
                            "snippet": func_info.get("code", ""),
                            "line": func_info.get("line", 0),
                            "line_from": func_info.get("line_from", 0),
                            "line_to": func_info.get("line_to", 0),
                        }
                        
                        results.append((similarity, structure))
    else:
        # Use the older format where structures is a list
        for idx, structure in enumerate(structures):
            structure_id = str(idx)
            if structure_id in embeddings:
                similarity = cosine_similarity(query_vector, embeddings[structure_id])
                if similarity > 0.0 and similarity < 0.5:
                    results.append((similarity, structure))
    
    # Sort by similarity (descending)
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Return top matches
    return [
        {
            "similarity": float(score),
            "payload": structure
        }
        for score, structure in results[:limit]
    ] 