import os

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from code_search.config import ROOT_DIR
from code_search.hybrid_searcher import CombinedSearcher
from code_search.local_file_get import FileGet

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Check if frontend is built
frontend_dir = os.path.join(ROOT_DIR, 'frontend', 'dist')
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 