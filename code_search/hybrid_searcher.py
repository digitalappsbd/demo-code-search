from typing import List
import json
import logging

from code_search.hybrid_search import hybrid_search

# Set up logging
logger = logging.getLogger(__name__)

class HybridSearcher:
    def __init__(self):
        pass
        
    def search(self, query, limit=5, model=None) -> List[dict]:
        """
        Search for code structures that match the query using a hybrid search approach
        that combines semantic search with text-based matching for filenames,
        filepaths, and function names.
        
        Args:
            query: The search query string
            limit: Maximum number of results to return
            model: The model to use for the search
            
        Returns:
            A list of search results formatted for the frontend
        """
        logger.info(f"HybridSearcher executing search for query: {query}" + (f" with model: {model}" if model else ""))
        results = hybrid_search(query, limit=limit, model=model)
        logger.info(f"Received {len(results)} results from hybrid_search")
        
        formatted_results = []
        
        for item in results:
            structure = item["payload"]
            match_type = item.get("match_type", "semantic")
            matched_field = item.get("matched_field", "")
            
            logger.debug(f"Processing result: {match_type} match on {matched_field}, score: {item.get('similarity', 0.0)}")
            
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
                "similarity": item.get("similarity", 0.0),
                "match_type": match_type,
                "matched_field": matched_field,
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
            
        logger.info(f"Returning {len(formatted_results)} formatted results")
        
        # Log a summary of match types
        semantic_count = sum(1 for r in formatted_results if r["match_type"] == "semantic")
        text_count = sum(1 for r in formatted_results if r["match_type"] == "text")
        hybrid_count = sum(1 for r in formatted_results if r["match_type"] == "hybrid")
        logger.info(f"Result breakdown: {semantic_count} semantic, {text_count} text, {hybrid_count} hybrid")
        
        return formatted_results
        
class CombinedSearcher:
    def __init__(self):
        self.searcher = HybridSearcher()
        logger.info("CombinedSearcher initialized with HybridSearcher")
        
    def search(self, query, limit=5, model=None) -> List[dict]:
        logger.info(f"CombinedSearcher executing search for query: {query}" + (f" with model: {model}" if model else ""))
        results = self.searcher.search(query, limit=limit, model=model)
        logger.info(f"CombinedSearcher returning {len(results)} results")
        return results
        
if __name__ == '__main__':
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    query = "read file from assets"
    searcher = CombinedSearcher()
    res = searcher.search(query)
    for hit in res:
        print(json.dumps(hit)) 