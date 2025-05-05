#!/usr/bin/env bash

set -e

# Ensure current path is project root
cd "$(dirname "$0")/../"

# Set environment variables explicitly
export QDRANT_URL="https://9df15c3b-de26-4423-a1b6-b5b0413cbe56.us-east4-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0._U0pQ2njqoOeEk2TW_nVbaBxJgacLvucRaIjIUeL5kg"

# Run the indexing script
python3 tools/index_quran_simple.py 