import os
import tempfile
from typing import List

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel

from code_search.config import ROOT_DIR
from code_search.searcher import CombinedSearcher
from code_search.get_file import FileGet
from code_search.merge_codes import merge_search_results

app = FastAPI()

searcher = CombinedSearcher()
get_file = FileGet()


@app.get("/api/search")
async def search(query: str):
    return {
        "result": searcher.search(query, limit=5)
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
    temp_file = os.path.join(tempfile.gettempdir(), "merged_code.txt")
    merged_content = merge_search_results(request.file_paths, temp_file)
    return {
        "result": merged_content
    }


app.mount("/", StaticFiles(directory=os.path.join(ROOT_DIR, 'frontend', 'dist'), html=True))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
