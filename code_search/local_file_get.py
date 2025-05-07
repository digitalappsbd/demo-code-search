import os
from typing import List, Dict, Any

class FileGet:
    def __init__(self, codebase_path=None):
        self.codebase_path = codebase_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def get(self, path, limit=5) -> List[Dict[str, Any]]:
        """Get the content of a file by path."""
        try:
            full_path = os.path.join(self.codebase_path, path)
            if not os.path.exists(full_path):
                return [{"error": f"File not found: {path}"}]
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            
            # Format the response to match what the frontend expects
            return [{
                "path": path,
                "content": content,
                "line_count": len(lines),
                # Add additional fields expected by the frontend
                "file_name": os.path.basename(path),
                "lines": [
                    {"content": line, "line_number": i+1} 
                    for i, line in enumerate(lines)
                ]
            }]
        except Exception as e:
            return [{"error": f"Error reading file {path}: {str(e)}"}]

if __name__ == '__main__':
    path = "core/utils/file_utils.dart"
    
    file_get = FileGet()
    
    res = file_get.get(path)
    for hit in res:
        if "error" in hit:
            print(f"Error: {hit['error']}")
        else:
            print(f"File: {hit['path']}")
            print(f"Line count: {hit['line_count']}")
            print("First 10 lines:")
            lines = hit['content'].split('\n')[:10]
            for i, line in enumerate(lines):
                print(f"{i+1}: {line}") 