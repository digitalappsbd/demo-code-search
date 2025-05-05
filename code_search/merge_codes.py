import os

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

def merge_search_results(file_paths, output_file):
    """
    Merge code from files specified in search results
    
    Args:
        file_paths (list): List of file paths from search results
        output_file (str): Path to output file
    """
    # Clear or create the output file to start fresh
    open(output_file, "w").close()
    
    for path in file_paths:
        if os.path.isfile(path):
            display_name = os.path.basename(path)
            append_file_content(path, output_file, display_name)
    
    # Return the content of the output file
    with open(output_file, "r", encoding="utf-8") as file:
        return file.read()

# For command line usage
if __name__ == "__main__":
    # Clear or create the output files to start fresh
    path_output_file = "output.txt"
    open(path_output_file, "w").close()

    # Merging specific paths listed in a file
    paths_file = "paths.txt"  # This file should contain the paths as you wish to input them
    merge_specific_paths_from_file(paths_file, path_output_file)

