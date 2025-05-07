import os
import tempfile
import logging
import subprocess
import time
from typing import List, Optional

from fastapi import FastAPI, BackgroundTasks
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

# Initialize global services only once at module load time
logger.info("Initializing search services...")
searcher = CombinedSearcher()
get_file = FileGet()
logger.info("Search services initialized successfully")

# Track embedding generation process
embedding_process = {
    "status": "idle",  # idle, running, completed, failed
    "progress": 0,
    "message": "",
    "start_time": None,
    "end_time": None
}

# Track structure generation process
structure_process = {
    "status": "idle",  # idle, running, completed, failed
    "progress": 0,
    "message": "",
    "start_time": None,
    "end_time": None
}

@app.get("/api/search")
async def search(query: str):
    logger.info(f"Received search request: {query}")
    results = searcher.search(query, limit=100)
    logger.info(f"Returning {len(results)} results")
    return {
        "result": results
    }

@app.get("/api/file")
async def file(path: str, codebase_path: Optional[str] = None):
    # If codebase_path is provided, create a new FileGet instance with the custom path
    # Otherwise, use the global instance with the default path
    if codebase_path:
        logger.info(f"Using custom codebase path: {codebase_path}")
        file_getter = FileGet(codebase_path=codebase_path)
        return {
            "result": file_getter.get(path)
        }
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

class EmbeddingRequest(BaseModel):
    model: str = "qodo"
    force: bool = False
    use_gpu: bool = False

def run_embedding_generation(model: str, force: bool, use_gpu: bool):
    global embedding_process
    
    try:
        embedding_process["status"] = "running"
        embedding_process["start_time"] = time.time()
        embedding_process["message"] = f"Starting embedding generation with {model} model..."
        
        # Build the command
        cmd = [
            "python3", 
            os.path.join(ROOT_DIR, "tools", "generate_embeddings_with_model.py"),
            f"--model={model}"
        ]
        
        if force:
            cmd.append("--force")
        
        if use_gpu:
            cmd.append("--gpu")
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Monitor progress
        for line in iter(process.stdout.readline, ''):
            logger.info(line.strip())
            
            # Extract total structures to process
            if "Processing" in line and "code structures" in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "out" and i > 0 and i+2 < len(parts):
                            current = int(parts[i-1])
                            total = int(parts[i+2])
                            embedding_process["total"] = total
                            embedding_process["progress"] = int((current / total) * 100)
                            break
                except Exception as e:
                    logger.error(f"Error parsing progress info: {e}")
            
            # Parse tqdm progress bar format
            elif "|" in line and "%" in line:
                try:
                    # Example: "45%|█████████▉         | 1351/3000 [00:20<00:24, 67.55it/s]"
                    percent_part = line.split("|")[0].strip()
                    if "%" in percent_part:
                        percent = int(float(percent_part.replace("%", "").strip()))
                        embedding_process["progress"] = percent
                except Exception as e:
                    logger.error(f"Error parsing tqdm output: {e}")
            
            embedding_process["message"] = line.strip()
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            embedding_process["status"] = "completed"
            embedding_process["progress"] = 100
            embedding_process["message"] = "Embedding generation completed successfully."
        else:
            stderr_output = process.stderr.read()
            logger.error(f"Embedding generation failed: {stderr_output}")
            embedding_process["status"] = "failed"
            embedding_process["message"] = f"Failed: {stderr_output}"
            
    except Exception as e:
        logger.exception("Error in embedding generation")
        embedding_process["status"] = "failed"
        embedding_process["message"] = str(e)
    finally:
        embedding_process["end_time"] = time.time()
        # Reset the searcher to load the new embeddings
        global searcher
        searcher = CombinedSearcher()

@app.post("/api/generate-embeddings")
async def generate_embeddings(request: EmbeddingRequest, background_tasks: BackgroundTasks):
    global embedding_process
    
    # Check if already running
    if embedding_process["status"] == "running":
        return {
            "status": "error",
            "message": "Embedding generation already in progress"
        }
    
    # Reset status
    embedding_process = {
        "status": "idle",
        "progress": 0,
        "message": "Initializing...",
        "start_time": None,
        "end_time": None
    }
    
    # Start embedding generation in background
    background_tasks.add_task(
        run_embedding_generation, 
        model=request.model, 
        force=request.force, 
        use_gpu=request.use_gpu
    )
    
    return {
        "status": "started",
        "message": f"Started embedding generation with {request.model} model"
    }

@app.get("/api/embedding-status")
async def get_embedding_status():
    global embedding_process
    return embedding_process

class StructureRequest(BaseModel):
    target_dir: str = ""
    pattern: str = "**/*.py"
    max_lines: int = 500
    force: bool = False

def run_structure_generation(target_dir: str, pattern: str, max_lines: int, force: bool):
    global structure_process
    
    try:
        structure_process["status"] = "running"
        structure_process["start_time"] = time.time()
        structure_process["message"] = "Starting code structure generation..."
        
        # Use a default target dir if not provided
        if not target_dir:
            # Use the parent directory or a specific code directory
            target_dir = os.path.dirname(ROOT_DIR)
        
        # Build the command
        cmd = [
            "python3", 
            os.path.join(ROOT_DIR, "tools", "index_quran_simple.py"),
            "--target-dir", target_dir,
            "--pattern", pattern,
            "--max-lines", str(max_lines)
        ]
        
        if force:
            cmd.append("--force")
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Monitor progress
        total_files = 0
        processed_files = 0
        
        for line in iter(process.stdout.readline, ''):
            logger.info(line.strip())
            
            # Extract total files to process
            if "Found" in line and "files to process" in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "Found" and i+1 < len(parts):
                            total_files = int(parts[i+1])
                            structure_process["total"] = total_files
                            break
                except Exception as e:
                    logger.error(f"Error parsing file count: {e}")
            
            # Parse file processing updates
            elif "Processing file" in line:
                processed_files += 1
                if total_files > 0:
                    structure_process["progress"] = int((processed_files / total_files) * 100)
                    structure_process["processed"] = processed_files
            
            # Parse tqdm progress bar format
            elif "|" in line and "%" in line:
                try:
                    # Example: "45%|█████████▉         | 1351/3000 [00:20<00:24, 67.55it/s]"
                    percent_part = line.split("|")[0].strip()
                    if "%" in percent_part:
                        percent = int(float(percent_part.replace("%", "").strip()))
                        structure_process["progress"] = percent
                except Exception as e:
                    logger.error(f"Error parsing tqdm output: {e}")
            
            structure_process["message"] = line.strip()
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            structure_process["status"] = "completed"
            structure_process["progress"] = 100
            structure_process["message"] = "Structure generation completed successfully."
        else:
            stderr_output = process.stderr.read()
            logger.error(f"Structure generation failed: {stderr_output}")
            structure_process["status"] = "failed"
            structure_process["message"] = f"Failed: {stderr_output}"
            
    except Exception as e:
        logger.exception("Error in structure generation")
        structure_process["status"] = "failed"
        structure_process["message"] = str(e)
    finally:
        structure_process["end_time"] = time.time()

@app.post("/api/generate-structures")
async def generate_structures(request: StructureRequest, background_tasks: BackgroundTasks):
    global structure_process
    
    # Check if already running
    if structure_process["status"] == "running":
        return {
            "status": "error",
            "message": "Structure generation already in progress"
        }
    
    # Reset status
    structure_process = {
        "status": "idle",
        "progress": 0,
        "message": "Initializing...",
        "start_time": None,
        "end_time": None
    }
    
    # Start structure generation in background
    background_tasks.add_task(
        run_structure_generation, 
        target_dir=request.target_dir,
        pattern=request.pattern,
        max_lines=request.max_lines,
        force=request.force
    )
    
    return {
        "status": "started",
        "message": "Started code structure generation"
    }

@app.get("/api/structure-status")
async def get_structure_status():
    global structure_process
    return structure_process

# Check if frontend is built
frontend_dir = os.path.join(ROOT_DIR, 'frontend', 'dist')
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 