from typing import Optional, List, Dict, Any
import json
import torch
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
from tqdm import tqdm
from huggingface_hub import login
from dotenv import load_dotenv
import gc

class NomicEmbeddingsProvider:
    def __init__(self, device: Optional[str] = None):
        # Load environment variables
        load_dotenv()
        
        # Check for Hugging Face token and login if available
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            print("Logging in to Hugging Face with token...")
            login(token=hf_token)
        else:
            print("Warning: No HUGGINGFACE_TOKEN found in environment variables.")
            print("You may need to authenticate to access the Nomic Embed Code model.")
            print("Visit https://huggingface.co/nomic-ai/nomic-embed-code to accept terms.")
        
        # Force CPU usage regardless of what's available to avoid MPS/CUDA memory issues
        print("Using CPU device for better memory management")
        self.device = torch.device("cpu")
        
        # Set environment variables for memory management
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        
        # Load model with explicit CPU device
        print("Loading model on CPU...")
        self.model = SentenceTransformer("nomic-ai/nomic-embed-code", device="cpu")
        self.model_name = "nomic-ai/nomic-embed-code"

    def embed_code(
        self, code: Optional[str] = None, docstring: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for code and/or docstring.
        For queries, use the prompt_name="query" parameter.
        """
        text = f"{docstring or ''} {code or ''}"
        
        # Use smaller batch size for embedding to reduce memory usage
        vector = self.model.encode(text, batch_size=1, show_progress_bar=False)
        
        # Force garbage collection
        gc.collect()
        
        return vector.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        """
        # Use smaller batch size for embedding to reduce memory usage
        vector = self.model.encode(query, prompt_name="query", batch_size=1, show_progress_bar=False)
        
        # Force garbage collection
        gc.collect()
        
        return vector.tolist()

def generate_embeddings_file(structures_file: str, output_file: str):
    """
    Generate embeddings for code structures and save them to a JSON file.
    
    Args:
        structures_file: Path to the JSON file containing code structures
        output_file: Path to save the embeddings JSON file
    """
    # Load the code structures
    with open(structures_file, 'r') as f:
        structures = json.load(f)
    
    # Initialize the embedding provider
    provider = NomicEmbeddingsProvider()
    
    # Dictionary to store the embeddings
    embeddings = {}
    
    # Check if structures is a list or dictionary and process accordingly
    if isinstance(structures, list):
        # Process list format
        print(f"Processing {len(structures)} code structures (list format)...")
        
        for structure in tqdm(structures, desc="Generating embeddings"):
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
            
            # Force garbage collection after each embedding to free memory
            gc.collect()
    else:
        # Process dictionary format
        print(f"Processing {len(structures)} code files (dictionary format)...")
        
        # Generate embeddings for each structure
        for file_path, file_info in tqdm(structures.items(), desc="Generating embeddings"):
            file_embeddings = {}
            
            # Generate embeddings for each function in the file
            for func_info in file_info["functions"]:
                func_id = func_info["id"]
                code = func_info["code"]
                docstring = func_info.get("docstring", "")
                
                # Generate embedding
                embedding = provider.embed_code(code=code, docstring=docstring)
                
                # Store the embedding
                file_embeddings[func_id] = embedding
                
                # Force garbage collection after each embedding to free memory
                gc.collect()
            
            # Store the file's embeddings
            embeddings[file_path] = file_embeddings
    
    # Save the embeddings to a file
    with open(output_file, 'w') as f:
        json.dump(embeddings, f)
    
    print(f"Embeddings saved to {output_file}")

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).resolve().parents[2]
    
    # Define paths
    structures_file = os.path.join(project_root, "data", "structures.json")
    output_file = os.path.join(project_root, "data", "embeddings.json")
    
    # Generate embeddings
    generate_embeddings_file(structures_file, output_file) 