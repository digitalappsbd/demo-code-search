from typing import Optional, List, Dict, Any, Union
import json
import torch
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
from tqdm import tqdm
from huggingface_hub import login
from dotenv import load_dotenv
import gc
import numpy as np

class QodoEmbeddingsProvider:
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
            print("You may need to authenticate to access the Qodo Embed model.")
            print("Visit https://huggingface.co/Qodo/Qodo-Embed-1-1.5B to accept terms.")
        
        # Determine device
        if device is None:
            device = os.environ.get("EMBEDDING_DEVICE", "cpu")
        
        # Map device string to torch device
        if device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif device == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        
        self.model = None
        self.model_name = "Qodo/Qodo-Embed-1-1.5B"
        
        try:
            # Load model with explicit device
            print(f"Loading model on {self.device}...")
            self.model = SentenceTransformer("Qodo/Qodo-Embed-1-1.5B", device=self.device.type)
            
            # Warm up the model with a simple embedding
            print("Warming up the model...")
            _ = self.model.encode("Test code", batch_size=1, show_progress_bar=False)
            print(f"Model {self.model_name} loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Will use fallback embedding method instead.")
            self.model = None
            self.model_name = "fallback_simple_embed"
        
        # Set environment variables for memory management
        if self.device.type == "mps":
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

    def embed_code(
        self, code: Optional[str] = None, docstring: Optional[str] = None, batch_size: int = 1
    ) -> List[float]:
        """
        Generate embedding for code and/or docstring.
        """
        text = f"{docstring or ''} {code or ''}"
        
        if self.model is None:
            # Fallback to simple embedding if model failed to load
            from code_search.local_search import simple_encode
            return simple_encode(text)
        
        # Use configurable batch size for embedding
        vector = self.model.encode(text, batch_size=batch_size, show_progress_bar=False)
        
        # Force garbage collection if on CPU to reduce memory pressure
        if self.device.type == "cpu":
            gc.collect()
        
        return vector.tolist()
    
    def embed_batch(
        self, 
        texts: List[Dict[str, str]], 
        batch_size: int = 8
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of code snippets.
        
        Args:
            texts: List of dicts, each with "code" and optional "docstring" keys
            batch_size: Batch size for more efficient processing
            
        Returns:
            List of embeddings (as lists of floats)
        """
        # Prepare the texts
        formatted_texts = [
            f"{item.get('docstring', '')} {item.get('code', '')}" 
            for item in texts
        ]
        
        if self.model is None:
            # Fallback to simple embedding if model failed to load
            from code_search.local_search import simple_encode
            return [simple_encode(text) for text in formatted_texts]
        
        # Generate embeddings in a single batch
        vectors = self.model.encode(
            formatted_texts, 
            batch_size=batch_size, 
            show_progress_bar=len(formatted_texts) > 10
        )
        
        # Force garbage collection if on CPU
        if self.device.type == "cpu":
            gc.collect()
        
        # Convert numpy arrays to lists
        return [vec.tolist() for vec in vectors]
    
    def embed_query(self, query: str, batch_size: int = 1) -> List[float]:
        """
        Generate embedding for a search query.
        """
        if self.model is None:
            # Fallback to simple embedding if model failed to load
            from code_search.local_search import simple_encode
            return simple_encode(query)
            
        # Use configurable batch size for embedding
        vector = self.model.encode(query, batch_size=batch_size, show_progress_bar=False)
        
        # Force garbage collection if on CPU
        if self.device.type == "cpu":
            gc.collect()
        
        return vector.tolist()

def generate_embeddings_file(structures_file: str, output_file: str, device: str = "cpu", batch_size: int = 8):
    """
    Generate embeddings for code structures and save them to a JSON file.
    
    Args:
        structures_file: Path to the JSON file containing code structures
        output_file: Path to save the embeddings JSON file
        device: Device to use for embedding generation ("cpu", "cuda", or "mps")
        batch_size: Batch size for more efficient processing
    """
    # Load the code structures
    with open(structures_file, 'r') as f:
        structures = json.load(f)
    
    # Initialize the embedding provider
    provider = QodoEmbeddingsProvider(device=device)
    
    # Dictionary to store the embeddings
    embeddings = {}
    
    # Check if structures is a list or dictionary and process accordingly
    if isinstance(structures, list):
        # Process list format
        print(f"Processing {len(structures)} code structures (list format)...")
        
        # Process in batches for efficiency
        batch_size = min(batch_size, len(structures))
        batches = [structures[i:i + batch_size] for i in range(0, len(structures), batch_size)]
        
        # Process each batch with progress bar
        for batch in tqdm(batches, desc="Generating embeddings", unit="batch"):
            # Prepare batch data
            batch_texts = []
            batch_metadata = []
            
            for structure in batch:
                file_path = structure["file_path"]
                struct_id = f"{file_path}_{structure['line_from']}_{structure['line_to']}"
                
                batch_texts.append({
                    "code": structure.get("snippet", ""),
                    "docstring": structure.get("docstring", "")
                })
                
                batch_metadata.append({
                    "file_path": file_path,
                    "struct_id": struct_id
                })
            
            # Generate embeddings for the batch
            batch_embeddings = provider.embed_batch(batch_texts, batch_size=batch_size)
            
            # Store the embeddings
            for i, (metadata, embedding) in enumerate(zip(batch_metadata, batch_embeddings)):
                file_path = metadata["file_path"]
                struct_id = metadata["struct_id"]
                
                if file_path not in embeddings:
                    embeddings[file_path] = {}
                
                embeddings[file_path][struct_id] = embedding
            
            # Force garbage collection after each batch to free memory
            gc.collect()
    else:
        # Process dictionary format
        print(f"Processing {len(structures)} code files (dictionary format)...")
        
        # Generate embeddings for each structure
        for file_path, file_info in tqdm(structures.items(), desc="Generating embeddings"):
            file_embeddings = {}
            
            # Prepare batch data
            functions = file_info["functions"]
            batch_size = min(batch_size, len(functions))
            
            # Process in batches
            for i in range(0, len(functions), batch_size):
                batch = functions[i:i + batch_size]
                
                # Prepare batch data
                batch_texts = []
                batch_ids = []
                
                for func_info in batch:
                    func_id = func_info["id"]
                    code = func_info["code"]
                    docstring = func_info.get("docstring", "")
                    
                    batch_texts.append({
                        "code": code,
                        "docstring": docstring
                    })
                    batch_ids.append(func_id)
                
                # Generate embeddings for the batch
                batch_embeddings = provider.embed_batch(batch_texts, batch_size=batch_size)
                
                # Store the embeddings
                for func_id, embedding in zip(batch_ids, batch_embeddings):
                    file_embeddings[func_id] = embedding
                
                # Force garbage collection after each batch
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