import os
import pyperclip
import logging

def merge_files_recursively(source_folder, output_file, base_path=""):
    for root, dirs, files in os.walk(source_folder):
        # Ignore .DS_Store files/folders
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        files = [f for f in files if not f.startswith('.')]
        
        relative_path = os.path.relpath(root, base_path) if base_path else ""
        for filename in files:
            # Ignore .g.dart files
            if not filename.endswith('.g.dart'):
                file_path = os.path.join(root, filename)
                rel_file_path = os.path.join(relative_path, filename) if base_path else filename
                append_file_content(file_path, output_file, rel_file_path)


def append_file_content(file_path, output_file, display_name):
    with open(output_file, "a", encoding="utf-8") as outfile:
        outfile.write(f"File Name : {display_name}\n\n")
        with open(file_path, "r", encoding="utf-8") as infile:
            content = infile.read()
            outfile.write(content)
        outfile.write("\n\n=====================\n\n")

def merge_specific_paths_from_file(paths_file, output_file):
    with open(paths_file, "r", encoding="utf-8") as file:
        paths = [line.strip() for line in file.readlines()]
    for path in paths:
        if os.path.isdir(path):
            merge_files_recursively(path, output_file, base_path=os.path.dirname(path))
        elif os.path.isfile(path):
            display_name = os.path.relpath(path, os.path.dirname(path))
            append_file_content(path, output_file, display_name)

def merge_search_results(file_paths, output_file=None):
    """
    Merge code from files specified in search results and return the content
    
    Args:
        file_paths (list): List of file paths from search results
        output_file (str, optional): Path to output file, if None will just return merged content
    
    Returns:
        str: The merged content for copying to clipboard
    """
    logging.info(f"Starting merge_search_results with {len(file_paths)} file paths")
    
    # Create merged content in memory
    merged_content = ""
    
    # If output_file is provided, clear or create it
    if output_file:
        open(output_file, "w").close()
    
    # Add prefix to file paths
    prefixed_paths = []
    prefix = "/Users/devsufi/Documents/GitHub/Quran-Majeed/lib/"
    for path in file_paths:
        prefixed_path = prefix + path if not path.startswith(prefix) else path
        prefixed_paths.append(prefixed_path)
    
    for path in prefixed_paths:
        if os.path.isfile(path):
            display_name = os.path.basename(path)
            logging.info(f"Processing file: {path}")
            
            # Add content to string
            merged_content += f"File Name : {display_name}\n\n"
            try:
                with open(path, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    merged_content += content
                merged_content += "\n\n=====================\n\n"
                
                # If output file is provided, also write to that file
                if output_file:
                    append_file_content(path, output_file, display_name)
            except Exception as e:
                logging.error(f"Error processing file {path}: {e}")
        else:
            logging.warning(f"File not found: {path}")
    
    logging.info(f"Finished merging. Content length: {len(merged_content)} characters")
    return merged_content

def copy_search_results_to_clipboard(file_paths):
    """
    Merge code from search results and copy to clipboard
    
    Args:
        file_paths (list): List of file paths from search results
        
    Returns:
        bool: True if copied successfully
    """
    try:
        merged_content = merge_search_results(file_paths)
        pyperclip.copy(merged_content)
        return True
    except Exception as e:
        print(f"Error copying to clipboard: {e}")
        return False

# For command line usage
if __name__ == "__main__":
    import sys
    
    # Default to reading from paths.txt if no arguments
    if len(sys.argv) == 1:
        # Clear or create the output files to start fresh
        path_output_file = "output.txt"
        open(path_output_file, "w").close()

        # Merging specific paths listed in a file
        paths_file = "paths.txt"  # This file should contain the paths as you wish to input them
        merge_specific_paths_from_file(paths_file, path_output_file)
        print(f"Merged code saved to {path_output_file}")
    else:
        # If file paths are provided as arguments, merge them and copy to clipboard
        file_paths = sys.argv[1:]
        result = copy_search_results_to_clipboard(file_paths)
        if result:
            print("Success! Copied to clipboard")
        else:
            print("Failed to copy to clipboard")

