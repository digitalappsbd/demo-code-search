from typing import List
import json

from code_search.local_search import search

class LocalSearcher:
    def __init__(self):
        pass
        
    def search(self, query, limit=5) -> List[dict]:
        """
        Search for code structures that match the query and format them
        in a way the frontend expects.
        """
        results = search(query, limit=limit)
        formatted_results = []
        
        for item in results:
            structure = item["payload"]
            # Format as expected by frontend
            formatted_result = {
                "file_path": structure.get("file_path", ""),
                "file_name": structure.get("file_name", ""),
                "name": structure.get("name", ""),
                "structure_type": structure.get("structure_type", ""),
                "module": structure.get("module", ""),
                "docstring": structure.get("docstring", ""),
                "snippet": structure.get("snippet", ""),
                "line": structure.get("line", 0),
                "line_from": structure.get("line_from", 0),
                "line_to": structure.get("line_to", 0),
                # Add a context section as expected by frontend
                "context": {
                    "module": structure.get("module", ""),
                    "file_path": structure.get("file_path", ""),
                    "file_name": structure.get("file_name", ""),
                    "struct_name": None,
                    "snippet": structure.get("snippet", "")
                }
            }
            formatted_results.append(formatted_result)
            
        return formatted_results
        
class CombinedSearcher:
    def __init__(self):
        self.searcher = LocalSearcher()
        
    def search(self, query, limit=5) -> List[dict]:
        results = self.searcher.search(query, limit=limit)
        return results
        
if __name__ == '__main__':
    query = "read file from assets"
    searcher = CombinedSearcher()
    res = searcher.search(query)
    for hit in res:
        print(json.dumps(hit)) 