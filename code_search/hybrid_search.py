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
        # Slightly reduce semantic search scores to prioritize exact keyword matches
        results_dict[structure_id] = {
            "similarity": float(item["similarity"]) * 0.9,  # Reduce semantic scores to prioritize keyword matches
            "payload": item["payload"],
            "match_type": "semantic"
        }
    
    # Perform text-based search
    if len(structures) > 0:
        # Normalize query for comparison
        normalized_query = query.lower()
        query_terms = normalized_query.split()
        
        for idx, structure in enumerate(structures):
            structure_id = str(structure.get("file_path", "") + structure.get("name", ""))
            
            # Get relevant fields for matching
            file_path = structure.get("file_path", "").lower()
            file_name = structure.get("file_name", "").lower()
            function_name = structure.get("name", "").lower()
            
            # Calculate match score based on exact and partial matches in fields
            score = 0.0
            matched_field = ""
            
            # Check for exact matches (highest priority)
            if normalized_query == file_name:
                score = 0.99  # Highest score for exact filename match
                matched_field = "file_name"
            elif file_name and normalized_query in file_name:
                # Partial but strong match in filename
                score = 0.97
                matched_field = "file_name"
            elif normalized_query == function_name:
                score = 0.95  # High score for exact function name match
                matched_field = "function_name"
            elif file_path.endswith("/" + normalized_query):
                score = 0.93  # High score for path ending with exact query
                matched_field = "file_path"
                
            # Check for partial matches if no exact match found
            if score == 0.0:
                # Calculate individual field scores
                filename_score = _calculate_match_score(file_name, normalized_query, query_terms)
                function_score = _calculate_match_score(function_name, normalized_query, query_terms)
                path_score = _calculate_match_score(file_path, normalized_query, query_terms)
                
                # Weight the scores, heavily prioritizing filename matches
                if filename_score > 0:
                    score = filename_score * 0.95  # Filename is highest priority
                    matched_field = "file_name"
                elif function_score > 0:
                    score = function_score * 0.85  # Function name is high priority
                    matched_field = "function_name"
                elif path_score > 0:
                    score = path_score * 0.8   # Path is medium priority
                    matched_field = "file_path"
            
            # Only include matches with a minimum score
            if score > 0.3:
                # If this entry already exists from semantic search but our keyword match is better, update it
                if structure_id in results_dict and results_dict[structure_id]["similarity"] < score:
                    results_dict[structure_id] = {
                        "similarity": float(score),
                        "payload": structure,
                        "match_type": "text",
                        "matched_field": matched_field
                    }
                # If this entry doesn't exist in results yet, add it
                elif structure_id not in results_dict:
                    results_dict[structure_id] = {
                        "similarity": float(score),
                        "payload": structure,
                        "match_type": "text",
                        "matched_field": matched_field
                    }
    
    # Convert dictionary to list and sort by similarity score
    results = list(results_dict.values())
    
    # Custom sort: first by match_type (text before semantic), then by matched_field, then by similarity
    def custom_sort_key(item):
        # First tier: text matches before semantic matches
        match_type_value = 0 if item.get("match_type") == "text" else 1
        
        # Second tier: prioritize by matched field type
        matched_field = item.get("matched_field", "")
        field_priority = {
            "file_name": 0,      # Highest priority
            "function_name": 1,  # Second priority
            "file_path": 2,      # Third priority
            "": 3                # Lowest priority (for semantic matches)
        }
        field_value = field_priority.get(matched_field, 3)
        
        # Third tier: sort by similarity score
        similarity = -item.get("similarity", 0)  # Negative for descending order
        
        return (match_type_value, field_value, similarity)
    
    # Sort results using our custom sort key
    results.sort(key=custom_sort_key)
    
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
            return 0.9
        
        # Check if the query is a whole word within the text
        query_pattern = r"\b{}\b".format(re.escape(query))
        if re.search(query_pattern, text):
            return 0.8
        
        # It's in the string but not a whole word
        return 0.7
    
    # Calculate score based on how many terms match and their positions
    matches = 0
    total_terms = len(query_terms)
    for term in query_terms:
        if term in text:
            matches += 1
            # Give higher score if term appears at the beginning
            if text.startswith(term):
                matches += 0.5
    
    # Only return a score if a significant portion of terms match
    match_ratio = matches / max(total_terms, 1)
    if match_ratio >= 0.5:  # At least half the terms must match
        return 0.5 * match_ratio
    return 0.0 