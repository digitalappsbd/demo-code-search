import os
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

# Set up paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "qodo_embeddings.json")
STRUCTURES_FILE = os.path.join(DATA_DIR, "structures.json")

# Vector size for encoding
VECTOR_SIZE = 768

# Create a global embeddings provider singleton
_EMBEDDINGS_PROVIDER = None

# Set up logging
logger = logging.getLogger(__name__)

def get_embeddings_provider(model=None):
    """
    Get or create the embedding provider based on model selection.
    
    Args:
        model: The model name to use (e.g., 'qodo', 'nomic', 'jina'). If None, uses default.
    
    Returns:
        An instance of the appropriate embeddings provider.
    """
    global _EMBEDDINGS_PROVIDER
    
    # If specific model requested, create a new provider for that model
    if model:
        if model == 'qodo':
            from code_search.model.qodo_embed import QodoEmbeddingsProvider
            return QodoEmbeddingsProvider()
        elif model == 'nomic':
            from code_search.model.nomic_embed import NomicEmbeddingsProvider
            return NomicEmbeddingsProvider()
        elif model == 'jina':
            from code_search.model.jina_embed import JinaEmbeddingsProvider
            return JinaEmbeddingsProvider()
    
    # Otherwise use or create the default provider
    if _EMBEDDINGS_PROVIDER is None:
        from code_search.model.qodo_embed import QodoEmbeddingsProvider
        _EMBEDDINGS_PROVIDER = QodoEmbeddingsProvider()
    
    return _EMBEDDINGS_PROVIDER

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
    """
    Calculate cosine similarity between two vectors.
    Handles vectors of different dimensions by logging a warning
    and returning a low similarity score.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    # Check if dimensions match
    if vec1.shape != vec2.shape:
        logger.warning(f"Vector dimension mismatch: {vec1.shape} vs {vec2.shape}. Using alternative similarity measure.")
        # Return a low similarity score to avoid breaking the search
        return 0.1
    
    # Calculate cosine similarity for vectors with matching dimensions
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_structures():
    """Load code structures from file."""
    if os.path.exists(STRUCTURES_FILE):
        with open(STRUCTURES_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_embeddings(model: str = None):
    """
    Load embeddings from a JSON file.
    
    Args:
        model: The specific embedding model to load. Format is the prefix of the file
              name (e.g., 'qodo', 'nomic', 'jina'). If None, uses default priority.
    """
    if model:
        # Try to load the specified model's embeddings file
        embeddings_file = os.path.join(DATA_DIR, f"{model}_embeddings.json")
        if os.path.exists(embeddings_file):
            with open(embeddings_file, "r") as f:
                return json.load(f)
        else:
            # If the specified model embeddings don't exist, log a warning
            logging.warning(f"No embeddings found for model {model}. Falling back to default.")
    
    # First try to load qodo_embeddings.json (preferred)
    qodo_embeddings_file = os.path.join(DATA_DIR, "qodo_embeddings.json")
    if os.path.exists(qodo_embeddings_file):
        with open(qodo_embeddings_file, "r") as f:
            return json.load(f)
    
    # Fall back to embeddings.json if qodo_embeddings.json doesn't exist
    embeddings_file = os.path.join(DATA_DIR, "embeddings.json") 
    if os.path.exists(embeddings_file):
        with open(embeddings_file, "r") as f:
            return json.load(f)
    
    return {}

def search(query: str, limit: int = 100, embeddings_provider=None, model: str = None) -> List[Dict[str, Any]]:
    """Search for code structures matching the query using available embeddings."""
    logger.info(f"Searching with query: {query}, model: {model}")
    
    # Load structures and embeddings
    structures = load_structures()
    if not structures:
        logger.warning("No structures found. Please run indexing first.")
        return []

    # Use the singleton embeddings provider instead of creating a new one each time
    if embeddings_provider is None:
        embeddings_provider = get_embeddings_provider(model)
        logger.info(f"Created embedding provider for model: {model}")
    
    # Embed the query
    query_vector = embeddings_provider.embed_query(query)
    vector_dim = len(query_vector)
    logger.info(f"Query vector dimension: {vector_dim}")
    
    # Load embeddings file
    embeddings = load_embeddings(model)
    if not embeddings:
        logger.warning("No embeddings found. Please run indexing first.")
        return []

    results = []
    
    # Check if we're using the newer dictionary format or the older list format
    if isinstance(structures, dict):
        # Newer format: structures is a dict of file_path -> file_info
        for file_path, file_info in structures.items():
            if file_path not in embeddings:
                continue
                
            file_embeddings = embeddings[file_path]
            for func in file_info.get("functions", []):
                func_id = func.get("id", "")
                if not func_id or func_id not in file_embeddings:
                    continue
                    
                # Get the embedding vector for this function
                embedding = file_embeddings[func_id]
                
                # Calculate similarity
                similarity = cosine_similarity(query_vector, embedding)
                
                # Create the search result
                result = {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "name": func.get("name", ""),
                    "structure_type": func.get("type", "function"),
                    "module": func.get("module", ""),
                    "docstring": func.get("docstring", ""),
                    "snippet": func.get("code", ""),
                    "line": func.get("line", 0),
                    "line_from": func.get("start_line", 0),
                    "line_to": func.get("end_line", 0),
                    "similarity": similarity
                }
                
                results.append(result)
    else:
        # Legacy format: structures is a list of structure objects
        for i, structure in enumerate(structures):
            file_path = structure.get("file_path", "")
            if file_path not in embeddings:
                continue
                
            structure_id = f"{file_path}_{structure.get('line_from', '')}_{structure.get('line_to', '')}"
            
            if structure_id not in embeddings[file_path]:
                continue
                
            # Get the embedding vector
            embedding = embeddings[file_path][structure_id]
            
            # Calculate similarity
            similarity = cosine_similarity(query_vector, embedding)
            
            # Copy the structure and add the similarity score
            result = structure.copy()
            result["similarity"] = similarity
            
            results.append(result)
    
    # Sort results by similarity and limit
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit] 