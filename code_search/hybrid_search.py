import json
import os
import logging
from typing import List, Dict, Any
import numpy as np
from code_search.config import ROOT_DIR
from code_search.local_search import load_structures, load_embeddings

logger = logging.getLogger(__name__)
# Set logging level to DEBUG to get more detailed logs
logger.setLevel(logging.DEBUG)

def hybrid_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining semantic search with text-based search
    to find code structures matching the query.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of search results with payload and similarity score
    """
    logger.debug(f"Starting hybrid search for query: {query}")
    
    # Get embeddings and structures for semantic search
    from code_search.local_search import search as semantic_search
    semantic_results = semantic_search(query, limit=limit)
    
    # Check if we got any semantic results
    if not semantic_results:
        logger.warning(f"No semantic search results found for: {query}")
        return []
    
    logger.debug(f"Found {len(semantic_results)} semantic search results")
    
    # Get all structures for text-based search
    structures = load_structures()
    if not structures:
        logger.warning("No code structures found. Please run indexing first.")
        return []
    
    logger.debug(f"Loaded structures: {type(structures)} with {len(structures)} items")

    # Create a dictionary to store results with their scores
    results_dict = {}

    # Add semantic search results to the dictionary
    for item in semantic_results:
        file_path = item.get("file_path", "")
        name = item.get("name", "")
        
        structure_id = f"{file_path}:{name}"
        similarity = float(item.get("similarity", 0))
        # Slightly reduce semantic search scores to prioritize exact keyword matches
        adjusted_similarity = similarity * 0.95
        
        results_dict[structure_id] = {
            "similarity": adjusted_similarity,
            "payload": item,
            "match_type": "semantic",
            "matched_field": "content"
        }
        
        logger.debug(f"Added semantic result: {structure_id} with score {similarity} -> {adjusted_similarity}")
    
    # Perform text-based search on structures
    lower_query = query.lower()
    logger.debug(f"Performing text-based search with query: {lower_query}")
    
    # Check if structures is a dict (new format) or a list (old format)
    if isinstance(structures, dict):
        # Process dict format (file_path -> file_info)
        text_matches = 0
        for file_path, file_info in structures.items():
            # Search in file path
            if lower_query in file_path.lower():
                logger.debug(f"Found file path match: {file_path}")
                for func in file_info.get("functions", []):
                    structure_id = f"{file_path}:{func['name']}"
                    if structure_id not in results_dict:
                        # Create a new result entry
                        results_dict[structure_id] = {
                            "similarity": 0.98,  # High score for exact filename match
                            "payload": {
                                "file_path": file_path,
                                "file_name": os.path.basename(file_path),
                                "name": func.get("name", ""),
                                "structure_type": func.get("type", "function"),
                                "module": func.get("module", ""),
                                "docstring": func.get("docstring", ""),
                                "snippet": func.get("code", ""),
                                "line": func.get("line", 0),
                                "line_from": func.get("start_line", 0),
                                "line_to": func.get("end_line", 0),
                            },
                            "match_type": "text",
                            "matched_field": "file_path"
                        }
                        text_matches += 1
                        logger.debug(f"Added new text match for file path: {structure_id}")
                    else:
                        # Update existing entry if this is a better match
                        current = results_dict[structure_id]
                        if 0.98 > current["similarity"]:
                            current["similarity"] = 0.98
                            # If we already had a semantic match, mark as hybrid
                            if current["match_type"] == "semantic":
                                current["match_type"] = "hybrid"
                                logger.debug(f"Updated match to hybrid: {structure_id}")
                            else:
                                current["match_type"] = "text"
                            current["matched_field"] = "file_path"
                
            # Search in function names and content
            for func in file_info.get("functions", []):
                function_name = func.get("name", "").lower()
                code = func.get("code", "").lower()
                docstring = func.get("docstring", "").lower()
                structure_id = f"{file_path}:{func['name']}"
                
                # Skip if no match in any field
                if (lower_query not in function_name and 
                    (not docstring or lower_query not in docstring) and 
                    lower_query not in code):
                    continue
                
                # Search in function name (high priority)
                if lower_query in function_name:
                    similarity = 0.99  # Higher score for function name match
                    match_field = "function_name"
                    logger.debug(f"Found function name match: {function_name}")
                # Search in docstring (medium priority)
                elif docstring and lower_query in docstring:
                    similarity = 0.96  # Medium score for docstring match
                    match_field = "docstring"
                    logger.debug(f"Found docstring match in: {function_name}")
                # Search in code (lower priority)
                elif lower_query in code:
                    similarity = 0.93  # Lower score for code content match
                    match_field = "code"
                    logger.debug(f"Found code match in: {function_name}")
                else:
                    continue  # Shouldn't happen due to earlier check
                
                if structure_id not in results_dict:
                    # Create a new result entry
                    results_dict[structure_id] = {
                        "similarity": similarity,
                        "payload": {
                            "file_path": file_path,
                            "file_name": os.path.basename(file_path),
                            "name": func.get("name", ""),
                            "structure_type": func.get("type", "function"),
                            "module": func.get("module", ""),
                            "docstring": func.get("docstring", ""),
                            "snippet": func.get("code", ""),
                            "line": func.get("line", 0),
                            "line_from": func.get("start_line", 0),
                            "line_to": func.get("end_line", 0),
                        },
                        "match_type": "text",
                        "matched_field": match_field
                    }
                    text_matches += 1
                    logger.debug(f"Added new text match: {structure_id} for {match_field}")
                else:
                    # Update existing entry if this is a better match
                    current = results_dict[structure_id]
                    if similarity > current["similarity"]:
                        old_similarity = current["similarity"]
                        current["similarity"] = similarity
                        
                        # If this was already a semantic match, change to hybrid
                        if current["match_type"] == "semantic":
                            current["match_type"] = "hybrid"
                            logger.debug(f"Updated semantic to hybrid: {structure_id} score: {old_similarity} -> {similarity}")
                        else:
                            logger.debug(f"Updated text match score: {structure_id} score: {old_similarity} -> {similarity}")
                        
                        current["matched_field"] = match_field
        
        logger.debug(f"Found {text_matches} text-based matches in dictionary format structures")
    else:
        # Process list format (legacy)
        for structure in structures:
            # Check if the query appears in any of the relevant fields
            file_path = structure.get("file_path", "").lower()
            file_name = structure.get("file_name", "").lower()
            name = structure.get("name", "").lower()
            snippet = structure.get("snippet", "").lower()
            docstring = structure.get("docstring", "").lower()
            
            structure_id = f"{structure.get('file_path', '')}:{structure.get('name', '')}"
            
            # Skip if no match in any field
            if (lower_query not in name and 
                lower_query not in file_path and 
                lower_query not in file_name and
                (not docstring or lower_query not in docstring) and 
                lower_query not in snippet):
                continue
                
            # Search in different fields with different priorities
            if lower_query in name:
                similarity = 0.99  # Highest score for function name match
                match_field = "function_name"
                logger.debug(f"Found function name match: {name}")
            elif lower_query in file_path or lower_query in file_name:
                similarity = 0.98  # High score for file path/name match
                match_field = "file_path"
                logger.debug(f"Found file path/name match: {file_path or file_name}")
            elif docstring and lower_query in docstring:
                similarity = 0.96  # Medium score for docstring match
                match_field = "docstring"
                logger.debug(f"Found docstring match in: {name}")
            elif lower_query in snippet:
                similarity = 0.93  # Lower score for code content match
                match_field = "snippet"
                logger.debug(f"Found code match in: {name}")
            else:
                continue  # Shouldn't happen due to earlier check
            
            if structure_id not in results_dict:
                # Create a new result entry
                results_dict[structure_id] = {
                    "similarity": similarity,
                    "payload": structure,
                    "match_type": "text",
                    "matched_field": match_field
                }
                logger.debug(f"Added new text match: {structure_id} for {match_field}")
            else:
                # Update existing entry if this is a better match
                current = results_dict[structure_id]
                if similarity > current["similarity"]:
                    old_similarity = current["similarity"]
                    current["similarity"] = similarity
                    
                    # If this was already a semantic match, change to hybrid
                    if current["match_type"] == "semantic":
                        current["match_type"] = "hybrid"
                        logger.debug(f"Updated semantic to hybrid: {structure_id} score: {old_similarity} -> {similarity}")
                    else:
                        logger.debug(f"Updated text match score: {structure_id} score: {old_similarity} -> {similarity}")
                    
                    current["matched_field"] = match_field
    
    # Convert results dictionary to a sorted list
    results = list(results_dict.values())
    results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Log the final results summary
    semantic_count = sum(1 for r in results if r["match_type"] == "semantic")
    text_count = sum(1 for r in results if r["match_type"] == "text")
    hybrid_count = sum(1 for r in results if r["match_type"] == "hybrid")
    logger.debug(f"Final results: {len(results)} total ({semantic_count} semantic, {text_count} text, {hybrid_count} hybrid)")
    
    # Limit the number of results
    limited_results = results[:limit]
    logger.debug(f"Returning {len(limited_results)} results after limit")
    
    return limited_results 