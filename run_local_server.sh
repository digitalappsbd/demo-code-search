#!/usr/bin/env bash

set -e

# Ensure we're in the project root
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Make sure we have embeddings
if [ ! -f "data/qodo_embeddings.json" ] || [ ! -f "data/structures.json" ]; then
    echo "Generating embeddings and structures..."
    python3 tools/index_quran_local.py
fi

# Run the server
python -m uvicorn code_search.local_service:app --host 0.0.0.0 --port 8000 --reload 