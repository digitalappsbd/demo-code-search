#!/usr/bin/env bash

# Help function
show_help() {
    echo "Usage: ./tools/generate_jina_embeddings.sh [options]"
    echo
    echo "Generate code embeddings using the Jina Embeddings v2 small model."
    echo
    echo "Options:"
    echo "  --help                Show this help message and exit"
    echo "  --force               Force regeneration of all embeddings"
    echo "  --gpu                 Use GPU acceleration if available (CUDA or MPS)"
    echo "  --batch-size N        Set batch size for embedding generation (default: 8)"
    echo "  --checkpoint-interval N  Save checkpoints after processing N items (default: 10)"
    echo "  --output FILENAME     Specify custom output filename (default: jina_embeddings.json)"
    echo
    echo "Examples:"
    echo "  ./tools/generate_jina_embeddings.sh                  # Basic usage"
    echo "  ./tools/generate_jina_embeddings.sh --gpu            # Use GPU"
    echo "  ./tools/generate_jina_embeddings.sh --force          # Force regeneration"
    echo "  ./tools/generate_jina_embeddings.sh --output custom.json   # Custom filename"
}

# Check if help was requested
if [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Activate the virtual environment
if [[ -d "venv" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found at 'venv'. Using system Python."
fi

# Make sure the data directory exists
mkdir -p data

# Display file information
echo "Embedding Generation Settings:"
echo "  - Model: jinaai/jina-embeddings-v2-small-en"
echo "  - Input: data/structures.json"
echo "  - Default Output: data/jina_embeddings.json"
echo

# Run the embedding generation script with all arguments passed through
echo "Running Jina embedding generator with arguments: $@"
python tools/generate_jina_embeddings.py "$@"

# Check status
if [ $? -eq 0 ]; then
    echo "✅ Jina Embedding generation completed successfully!"
else
    echo "❌ Jina Embedding generation failed with exit code $?."
    exit 1
fi

echo "You can now use these embeddings with the code search application." 