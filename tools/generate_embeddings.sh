#!/usr/bin/env bash

# Help function
show_help() {
    echo "Usage: ./tools/generate_embeddings.sh [options]"
    echo
    echo "Generate code embeddings using the improved embedding script."
    echo
    echo "Options:"
    echo "  --help                Show this help message and exit"
    echo "  --force               Force regeneration of all embeddings"
    echo "  --gpu                 Use GPU acceleration if available (CUDA or MPS)"
    echo "  --batch-size N        Set batch size for embedding generation (default: 8)"
    echo "  --checkpoint-interval N  Save checkpoints after processing N items (default: 10)"
    echo
    echo "Examples:"
    echo "  ./tools/generate_embeddings.sh                         # Basic usage with defaults"
    echo "  ./tools/generate_embeddings.sh --gpu                   # Use GPU acceleration"
    echo "  ./tools/generate_embeddings.sh --force --batch-size 16 # Force regeneration with larger batch size"
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

# Display execution info
echo "Starting embedding generation..."
echo "Platform: $(uname -s), Python: $(python --version)"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
elif [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
    echo "Apple Silicon detected with MPS support"
fi

# Run the embedding generation script with all arguments passed through
echo "Running embedding generator with arguments: $@"
python tools/generate_nomic_embeddings.py "$@"

# Check status
if [ $? -eq 0 ]; then
    echo "✅ Embedding generation completed successfully!"
else
    echo "❌ Embedding generation failed with exit code $?."
    exit 1
fi

echo "You can now use these embeddings with the code search application." 