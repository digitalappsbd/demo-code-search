#!/bin/bash

# Activate the virtual environment
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Virtual environment exists but activate script not found. Creating a new one..."
        python -m venv venv
        source venv/bin/activate
    fi
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check if .env file with Hugging Face token exists
if [ ! -f ".env" ] || ! grep -q "HUGGINGFACE_TOKEN" .env; then
    echo "==============================================================="
    echo "Hugging Face authentication required for Nomic Embed Code model"
    echo "==============================================================="
    echo "The Nomic Embed Code model requires authentication to download."
    echo "You need to:"
    echo "1. Create a Hugging Face account if you don't have one"
    echo "2. Visit https://huggingface.co/nomic-ai/nomic-embed-code and accept the terms"
    echo "3. Generate a token at https://huggingface.co/settings/tokens"
    echo ""
    echo "Would you like to set up your Hugging Face token now? (y/n)"
    read -r setup_token
    
    if [[ $setup_token == "y" || $setup_token == "Y" ]]; then
        python tools/setup_huggingface.py
        
        # Exit if setup failed
        if [ $? -ne 0 ]; then
            echo "Authentication setup failed. Please try again."
            exit 1
        fi
    else
        echo "You chose not to set up authentication. The script may fail to download the model."
        echo "You can set up authentication later by running: python tools/setup_huggingface.py"
    fi
fi

# Check if embeddings.json exists, if not, generate it
if [ ! -f "data/embeddings.json" ]; then
    echo "Embeddings file not found. Generating embeddings using Nomic Embed Code model..."
    python tools/generate_nomic_embeddings.py
    
    # Exit if generation failed
    if [ $? -ne 0 ]; then
        echo "Embeddings generation failed. Please check the error messages above."
        exit 1
    fi
fi

# Run the Nomic-powered service
echo "Starting the server with Nomic Embed Code model..."
python -m code_search.local_service_nomic 