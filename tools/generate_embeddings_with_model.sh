#!/usr/bin/env bash

# Help function
show_help() {
    echo "Usage: ./tools/generate_embeddings_with_model.sh [options]"
    echo
    echo "Generate code embeddings using your choice of embedding model."
    echo
    echo "Options:"
    echo "  --help                Show this help message and exit"
    echo "  --model MODEL         Embedding model to use: nomic (default) or qodo"
    echo "  --force               Force regeneration of all embeddings"
    echo "  --gpu                 Use GPU acceleration if available (CUDA or MPS)"
    echo "  --batch-size N        Set batch size for embedding generation (default: 8)"
    echo "  --checkpoint-interval N  Save checkpoints after processing N items (default: 10)"
    echo "  --output FILENAME     Specify custom output filename (defaults to model-specific name)"
    echo
    echo "Examples:"
    echo "  ./tools/generate_embeddings_with_model.sh                       # Use default model (nomic)"
    echo "  ./tools/generate_embeddings_with_model.sh --model qodo          # Use the Qodo model"
    echo "  ./tools/generate_embeddings_with_model.sh --gpu --model qodo    # Use GPU with Qodo model"
    echo "  ./tools/generate_embeddings_with_model.sh --output custom.json  # Save to custom filename"
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

# Check if model was specified
MODEL="nomic"  # Default model
for arg in "$@"; do
    if [[ "$arg" == "--model" ]]; then
        MODEL_FLAG=true
    elif [[ "$MODEL_FLAG" == true ]]; then
        MODEL="$arg"
        unset MODEL_FLAG
    fi
done

# Display execution info
echo "Starting embedding generation with model: $MODEL"
echo "Platform: $(uname -s), Python: $(python --version)"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
elif [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
    echo "Apple Silicon detected with MPS support"
fi

# Run the embedding generation script with all arguments passed through
echo "Running embedding generator with arguments: $@"
python tools/generate_embeddings_with_model.py "$@"

# Check status
if [ $? -eq 0 ]; then
    echo "✅ Embedding generation completed successfully!"
else
    echo "❌ Embedding generation failed with exit code $?."
    exit 1
fi

echo "You can now use these embeddings with the code search application." 