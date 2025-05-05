from typing import List, Dict, Any
import re
from code_search.local_search import search as semantic_search, load_structures

def hybrid_search(query: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Perform a hybrid search combining semantic search with text-based search for
    filename, filepath, and function name.
    
    Args:
        query: The search query string
        limit: Maximum number of results to return
        
    Returns:
        A list of search results with similarity scores and payloads
    """
    # Get semantic search results
    semantic_results = semantic_search(query, limit=limit)
    
    # Get all structures for text-based search
    structures = load_structures()
    
    # Create a dictionary to store results with their scores
    results_dict = {}
    
    # Add semantic search results to the dictionary
    for item in semantic_results:
        structure_id = str(item["payload"].get("file_path", "") + item["payload"].get("name", ""))
        results_dict[structure_id] = item
    
    # Perform text-based search
    if len(structures) > 0:
        # Normalize query for comparison
        normalized_query = query.lower()
        query_terms = normalized_query.split()
        
        for idx, structure in enumerate(structures):
            structure_id = str(structure.get("file_path", "") + structure.get("name", ""))
            
            # Skip if already added by semantic search
            if structure_id in results_dict:
                continue
            
            # Get relevant fields for matching
            file_path = structure.get("file_path", "").lower()
            file_name = structure.get("file_name", "").lower()
            function_name = structure.get("name", "").lower()
            
            # Calculate match score based on exact and partial matches in fields
            score = 0.0
            
            # Check for exact matches (highest priority)
            if normalized_query == file_name:
                score = 0.95  # High score for exact filename match
            elif normalized_query == function_name:
                score = 0.9   # High score for exact function name match
            elif file_path.endswith("/" + normalized_query):
                score = 0.85  # High score for path ending with exact query
                
            # Check for partial matches if no exact match found
            if score == 0.0:
                # Check if all query terms are present in any of the fields
                all_terms_present = all(term in file_path or term in file_name or term in function_name for term in query_terms)
                
                if all_terms_present:
                    # Calculate a score based on field relevance and match positions
                    filename_score = _calculate_match_score(file_name, normalized_query, query_terms)
                    function_score = _calculate_match_score(function_name, normalized_query, query_terms)
                    path_score = _calculate_match_score(file_path, normalized_query, query_terms)
                    
                    # Weight the scores, emphasizing filename and function name matches
                    score = max(
                        filename_score * 0.9,      # Filename is important
                        function_score * 0.85,     # Function name is important
                        path_score * 0.7           # Path is less important
                    )
            
            # Only include matches with a minimum score
            if score > 0.4:
                results_dict[structure_id] = {
                    "similarity": float(score),
                    "payload": structure,
                    "match_type": "text"  # Add this to indicate it was a text match
                }
    
    # Convert dictionary to list and sort by similarity score
    results = list(results_dict.values())
    results.sort(reverse=True, key=lambda x: x["similarity"])
    
    # Return top matches
    return results[:limit]

def _calculate_match_score(text: str, query: str, query_terms: List[str]) -> float:
    """
    Calculate a match score based on how well the text matches the query.
    
    Args:
        text: The text to check
        query: The original query string
        query_terms: The query broken down into terms
        
    Returns:
        A score between 0 and 1
    """
    if not text:
        return 0.0
    
    # Check for exact match
    if query in text:
        # Score higher for exact match at beginning or as a whole word
        if text.startswith(query):
            return 0.85
        
        # Check if the query is a whole word within the text
        query_pattern = r"\b{}\b".format(re.escape(query))
        if re.search(query_pattern, text):
            return 0.75
        
        # It's in the string but not a whole word
        return 0.65
    
    # Calculate score based on how many terms match and their positions
    matches = 0
    for term in query_terms:
        if term in text:
            matches += 1
            # Give higher score if term appears at the beginning
            if text.startswith(term):
                matches += 0.5
    
    # Return a score proportional to how many terms matched
    return 0.5 * matches / max(len(query_terms), 1) 