#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if virtual environment exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Using existing virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "Creating virtual environment..."
    python -m venv "$PROJECT_ROOT/venv"
    source "$PROJECT_ROOT/venv/bin/activate"
    
    # Install requirements
    pip install -r "$PROJECT_ROOT/requirements.txt"
fi

# Run the embeddings generation script
python "$SCRIPT_DIR/generate_embeddings.py"

# Deactivate the virtual environment
deactivate

echo "Embeddings generation completed!" 