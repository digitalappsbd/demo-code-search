import os
import tempfile
import logging
from typing import List

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from code_search.config import ROOT_DIR
from code_search.hybrid_searcher import CombinedSearcher
from code_search.local_file_get import FileGet
from code_search.merge_codes import merge_search_results

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

searcher = CombinedSearcher()
get_file = FileGet()

@app.get("/api/search")
async def search(query: str):
    return {
        "result": searcher.search(query, limit=100)
    }

@app.get("/api/file")
async def file(path: str):
    return {
        "result": get_file.get(path)
    }

class MergeRequest(BaseModel):
    file_paths: List[str]

@app.post("/api/merge-codes")
async def merge_codes(request: MergeRequest):
    logger.info(f"Received merge request with {len(request.file_paths)} files")
    logger.info(f"File paths: {request.file_paths}")
    
    temp_file = os.path.join(tempfile.gettempdir(), "merged_code.txt")
    merged_content = merge_search_results(request.file_paths, temp_file)
    
    logger.info(f"Merged content length: {len(merged_content)}")
    # Log the first 100 characters of the content for debugging
    if merged_content:
        logger.info(f"Content preview: {merged_content[:100]}...")
    else:
        logger.warning("Merged content is empty")
    
    return {
        "result": merged_content
    }

# Check if frontend is built
frontend_dir = os.path.join(ROOT_DIR, 'frontend', 'dist')
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 