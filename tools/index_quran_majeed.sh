#!/usr/bin/env bash

set -e

# Ensure current path is project root
cd "$(dirname "$0")/../"

# Set environment variables
export QDRANT_URL
export QDRANT_API_KEY

# Run the indexing script
python3 tools/index_quran.py 