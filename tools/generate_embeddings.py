import json
import os
import sys
import hashlib
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Set up paths
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = ROOT_DIR / "data"
EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"
STRUCTURES_FILE = DATA_DIR / "structures.json"

# Vector size for encoding
VECTOR_SIZE = 1024  # BGE-large-en produces 1024-dimension vectors

def load_structures():
    """Load code structures from file."""
    if os.path.exists(STRUCTURES_FILE):
        with open(STRUCTURES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_embeddings(embeddings):
    """Save embeddings to file."""
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f)

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

def create_model():
    """Create the embedding model."""
    try:
        print("Loading BAAI/bge-large-en model...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('BAAI/bge-large-en')
        return model, True
    except Exception as e:
        print(f"Error loading BGE model: {str(e)}")
        print("Falling back to simple hash-based encoding.")
        return None, False

def prepare_text_for_embedding(structure):
    """Prepare text from code structure for embedding."""
    # Combine relevant fields into a single text representation
    parts = []
    
    # Add name and type
    parts.append(f"Type: {structure.get('structure_type', '')}")
    parts.append(f"Name: {structure.get('name', '')}")
    
    # Add docstring if it exists
    docstring = structure.get('docstring', '')
    if docstring and len(docstring.strip()) > 0:
        parts.append(f"Docstring: {docstring}")
    
    # Add file path information
    parts.append(f"File: {structure.get('file_path', '')}")
    
    # Add code snippet (truncated if too long)
    snippet = structure.get('snippet', '')
    if snippet:
        # Limit snippet length to avoid model context limits
        if len(snippet) > 4000:
            snippet = snippet[:4000] + "..."
        parts.append(f"Code: {snippet}")
    
    # Join all parts with newlines
    text = "\n".join(parts)
    return text

def generate_embeddings():
    """Generate embeddings for all code structures."""
    structures = load_structures()
    if not structures:
        print("No structures found, please make sure structures.json exists and is not empty.")
        return

    model, use_model = create_model()
    embeddings = {}
    
    print(f"Generating embeddings for {len(structures)} code structures...")
    for idx, structure in enumerate(tqdm(structures)):
        structure_id = str(idx)
        text = prepare_text_for_embedding(structure)
        
        # Generate embedding
        if use_model:
            try:
                # The instruction prefix improves retrieval performance for BGE model
                instruction = "Represent this code for searching relevant passages: "
                embedding = model.encode(instruction + text, normalize_embeddings=True)
                embeddings[structure_id] = embedding.tolist()
            except Exception as e:
                print(f"Error encoding structure {idx}: {str(e)}")
                print("Falling back to simple encoding for this item")
                embeddings[structure_id] = simple_encode(text)
        else:
            # Use simple encoding if model isn't available
            embeddings[structure_id] = simple_encode(text)
    
    # Save to file
    save_embeddings(embeddings)
    print(f"Embeddings saved to {EMBEDDINGS_FILE}")

if __name__ == "__main__":
    generate_embeddings() 