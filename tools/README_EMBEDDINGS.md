# Code Embedding Generation Tools

This directory contains various tools for generating embeddings from code using different embedding models.

## Available Models

1. **nomic-ai/nomic-embed-code** - A high-quality code embedding model from Nomic AI.
2. **Qodo/Qodo-Embed-1-1.5B** - A state-of-the-art code embedding model optimized for retrieval tasks in the software development domain.
3. **jinaai/jina-embeddings-v2-small-en** - Jina AI's small embedding model supporting 8192 sequence length for long context documents.

## Scripts Available

### Model-Specific Scripts

- `generate_nomic_embeddings.py` - Generate embeddings using the Nomic Embed Code model
- `generate_nomic_embeddings.sh` - Shell script wrapper for the Nomic embeddings generator
- `generate_qodo_embeddings.py` - Generate embeddings using the Qodo Embed 1 1.5B model
- `generate_qodo_embeddings.sh` - Shell script wrapper for the Qodo embeddings generator
- `generate_jina_embeddings.py` - Generate embeddings using the Jina Embeddings v2 small model
- `generate_jina_embeddings.sh` - Shell script wrapper for the Jina embeddings generator

### Multi-Model Script

- `generate_embeddings_with_model.py` - Unified script that supports multiple embedding models
- `generate_embeddings_with_model.sh` - Shell script wrapper for the multi-model embeddings generator

## Usage

### Using the Multi-Model Generator (Recommended)

The multi-model generator provides a unified interface for generating embeddings with any of the supported models.

```bash
# Generate embeddings with Nomic model (default)
./tools/generate_embeddings_with_model.sh

# Generate embeddings with Qodo model
./tools/generate_embeddings_with_model.sh --model qodo

# Generate embeddings with Jina model
./tools/generate_embeddings_with_model.sh --model jina

# Generate embeddings with GPU acceleration
./tools/generate_embeddings_with_model.sh --model qodo --gpu

# Force regeneration of all embeddings
./tools/generate_embeddings_with_model.sh --model qodo --force

# Specify a custom output filename
./tools/generate_embeddings_with_model.sh --model qodo --output custom_embeddings.json
```

For more options:

```bash
./tools/generate_embeddings_with_model.sh --help
```

### Using Model-Specific Generators

#### Nomic Embed Code

```bash
# Basic usage
./tools/generate_nomic_embeddings.sh

# With GPU acceleration
./tools/generate_nomic_embeddings.sh --gpu

# Force regeneration
./tools/generate_nomic_embeddings.sh --force
```

For more options:

```bash
./tools/generate_nomic_embeddings.sh --help
```

#### Qodo Embed

```bash
# Basic usage
./tools/generate_qodo_embeddings.sh

# With GPU acceleration
./tools/generate_qodo_embeddings.sh --gpu

# Force regeneration
./tools/generate_qodo_embeddings.sh --force

# Custom output filename
./tools/generate_qodo_embeddings.sh --output qodo_custom.json
```

For more options:

```bash
./tools/generate_qodo_embeddings.sh --help
```

#### Jina Embeddings v2

```bash
# Basic usage
./tools/generate_jina_embeddings.sh

# With GPU acceleration
./tools/generate_jina_embeddings.sh --gpu

# Force regeneration
./tools/generate_jina_embeddings.sh --force

# Custom output filename
./tools/generate_jina_embeddings.sh --output jina_custom.json
```

For more options:

```bash
./tools/generate_jina_embeddings.sh --help
```

## Requirements

The embedding generators require the following packages (included in requirements.txt):

- transformers
- sentence-transformers
- tqdm
- torch
- huggingface-hub
- python-dotenv

## Output Files

By default, the embedding generators produce the following files in the `data` directory:

- `embeddings.json` - For Nomic embeddings
- `qodo_embeddings.json` - For Qodo embeddings
- `jina_embeddings.json` - For Jina embeddings

You can specify custom output filenames using the `--output` parameter.
