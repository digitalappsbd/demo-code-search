#!/usr/bin/env python3

import os
import json
import sys
import glob
from pathlib import Path
from tqdm import tqdm

# Add the code_search module to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_search.local_search import simple_encode, DATA_DIR, STRUCTURES_FILE, EMBEDDINGS_FILE

# Set up paths
QURAN_CODEBASE_PATH = "/Users/devsufi/Documents/GitHub/Quran-Majeed/lib"
Path(DATA_DIR).mkdir(exist_ok=True)

# Process and index Flutter files
def process_flutter_files():
    print("Processing Flutter files...")
    
    # Get all Dart files
    dart_files = glob.glob(f"{QURAN_CODEBASE_PATH}/**/*.dart", recursive=True)
    code_structures = []
    
    for file_path in tqdm(dart_files):
        try:
            relative_path = os.path.relpath(file_path, start=QURAN_CODEBASE_PATH)
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Extract file parts
            file_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            module = os.path.basename(dir_path) if dir_path else ""
            
            # Process code line by line
            lines = code.split('\n')
            line_index = 0
            
            while line_index < len(lines):
                # Look for class or function definitions
                if line_index < len(lines) and ('class ' in lines[line_index] or 
                                              'void ' in lines[line_index] or 
                                              'Future<' in lines[line_index] or
                                              'Stream<' in lines[line_index] or
                                              'Widget ' in lines[line_index]):
                    start_line = line_index
                    # Look for opening brace
                    brace_count = 0
                    end_line = start_line
                    
                    # Collect docstring if any (usually before the definition)
                    docstring = ""
                    if start_line > 0 and "///" in lines[start_line - 1]:
                        comment_lines = []
                        i = start_line - 1
                        while i >= 0 and "///" in lines[i]:
                            comment_lines.insert(0, lines[i].strip("/ "))
                            i -= 1
                        docstring = "\n".join(comment_lines)
                    
                    # Find the end of the definition
                    while end_line < len(lines):
                        line = lines[end_line]
                        brace_count += line.count('{') - line.count('}')
                        if brace_count <= 0 and '{' in line:
                            break
                        end_line += 1
                    
                    # Check if we found a complete definition
                    if end_line < len(lines) and '{' in lines[end_line]:
                        # Find matching closing brace
                        brace_count = 1  # We've found an opening brace
                        end_line += 1
                        
                        while end_line < len(lines) and brace_count > 0:
                            line = lines[end_line]
                            brace_count += line.count('{') - line.count('}')
                            end_line += 1
                        
                        # Adjust for over-counting
                        if brace_count <= 0:
                            end_line -= 1
                        
                        # Extract the code segment
                        code_segment = "\n".join(lines[start_line:end_line+1])
                        
                        # Create structure
                        structure_type = "class" if "class " in lines[start_line] else "function"
                        name = lines[start_line].split("class ")[1].split("{")[0].strip() if "class " in lines[start_line] else lines[start_line].split("(")[0].split(" ")[-1].strip()
                        
                        structure = {
                            "structure_type": structure_type,
                            "name": name,
                            "docstring": docstring,
                            "module": module,
                            "file_path": relative_path,
                            "file_name": file_name,
                            "line": start_line + 1,
                            "line_from": start_line + 1,
                            "line_to": end_line + 1,
                            "snippet": code_segment
                        }
                        
                        code_structures.append(structure)
                        line_index = end_line
                
                line_index += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Save structures to file
    with open(STRUCTURES_FILE, 'w') as f:
        json.dump(code_structures, f)
    
    print(f"Found {len(code_structures)} code structures")
    
    # Generate embeddings
    generate_embeddings(code_structures)

# Generate and store embeddings
def generate_embeddings(structures):
    print("Generating embeddings...")
    
    embeddings = {}
    
    for i, structure in enumerate(tqdm(structures)):
        try:
            # Create searchable text representation
            searchable_text = f"{structure['structure_type']} {structure['name']} {structure['docstring']} {structure['module']} {structure['file_path']}"
            
            # Create simple vector encoding
            vector = simple_encode(searchable_text + " " + structure['snippet'])
            
            # Store embedding
            embeddings[str(i)] = vector
            
        except Exception as e:
            print(f"Error encoding structure {i}: {e}")
    
    # Save embeddings to file
    with open(EMBEDDINGS_FILE, 'w') as f:
        json.dump(embeddings, f)
    
    print(f"Generated {len(embeddings)} embeddings")

if __name__ == "__main__":
    # Process and index files
    process_flutter_files() 