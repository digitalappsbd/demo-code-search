import os
import json
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyperclip

from code_search.config import ROOT_DIR
from code_search.local_searcher import LocalSearcher
from code_search.model.nomic_embed import NomicEmbeddingsProvider

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the searcher with Nomic embeddings provider
searcher = LocalSearcher(embeddings_provider=NomicEmbeddingsProvider())

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/search")
def search(query: str = Query(None, min_length=1), limit: int = Query(5, ge=1, le=20)):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    result = searcher.search(query, limit=limit)
    
    return {"result": result}


@app.get("/copy")
def copy_to_clipboard(file: str = Query(None), start_line: int = Query(None, ge=1), end_line: int = Query(None, ge=1)):
    if not file or not start_line or not end_line:
        raise HTTPException(status_code=400, detail="file, start_line, and end_line parameters are required")
    
    try:
        with open(file, 'r') as f:
            lines = f.readlines()
        
        # Lines are 1-indexed in the UI but 0-indexed in the file
        text = "".join(lines[start_line - 1:end_line])
        pyperclip.copy(text)
        
        return {"success": True, "message": f"Copied {end_line - start_line + 1} lines to clipboard"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error copying to clipboard: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Load the embeddings
    embeddings_path = os.path.join(ROOT_DIR, "data", "embeddings.json")
    if not os.path.exists(embeddings_path):
        logging.error(f"Embeddings file not found at {embeddings_path}")
        print(f"Error: Embeddings file not found at {embeddings_path}")
        print("Please run the generate_nomic_embeddings.py script first.")
        exit(1)
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000) 