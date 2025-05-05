import os
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Set up paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "embeddings.json")
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
    return []

def load_embeddings():
    """Load embeddings from file."""
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def search(query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Search for code structures matching the query."""
    # Load structures and embeddings
    structures = load_structures()
    embeddings = load_embeddings()
    
    if not structures or not embeddings:
        return []
    
    # Create query vector
    query_vector = simple_encode(query)
    
    # Calculate similarity scores
    results = []
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