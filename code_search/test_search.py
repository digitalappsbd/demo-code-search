import logging
import json
from code_search.hybrid_search import hybrid_search

# Set up logging for testing
logging.basicConfig(level=logging.DEBUG)

def test_hybrid_search():
    # Test a query that should find matches in function names, file paths, etc.
    queries = ["file", "repository", "config", "search"]
    
    print("Running hybrid search tests...")
    
    for query in queries:
        print(f"\n\nTesting query: {query}")
        results = hybrid_search(query, limit=10)
        
        print(f"Got {len(results)} results")
        
        # Count match types
        semantic_count = sum(1 for r in results if r["match_type"] == "semantic")
        text_count = sum(1 for r in results if r["match_type"] == "text")
        hybrid_count = sum(1 for r in results if r["match_type"] == "hybrid")
        
        print(f"Match type breakdown: {semantic_count} semantic, {text_count} text, {hybrid_count} hybrid")
        
        # Show details of each result
        print("\nDetailed results:")
        for i, r in enumerate(results):
            print(f"{i+1}. Type: {r['match_type']}, Field: {r.get('matched_field', '')}, Score: {r['similarity']}")
            print(f"   Path: {r['payload'].get('file_path', '')}")
            print(f"   Name: {r['payload'].get('name', '')}")
            print(f"   Line: {r['payload'].get('line_from', '-')} to {r['payload'].get('line_to', '-')}")
            
if __name__ == "__main__":
    test_hybrid_search() 