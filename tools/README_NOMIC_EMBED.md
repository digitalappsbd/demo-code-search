# Nomic Embed Code Integration

This directory contains tools for integrating the Nomic Embed Code model into the code search system.

## About Nomic Embed Code

[Nomic Embed Code](https://huggingface.co/nomic-ai/nomic-embed-code) is a state-of-the-art code embedding model that excels at code retrieval tasks:

- High Performance: Outperforms Voyage Code 3 and OpenAI Embed 3 Large on CodeSearchNet
- Multilingual Code Support: Trained for multiple programming languages (Python, Java, Ruby, PHP, JavaScript, Go)
- Advanced Architecture: 7B parameter code embedding model
- Fully Open-Source: Model weights, training data, and evaluation code released

## Authentication Setup

The Nomic Embed Code model requires authentication to download. You need to:

1. Create a [Hugging Face account](https://huggingface.co/join) if you don't have one
2. Visit the [Nomic Embed Code model page](https://huggingface.co/nomic-ai/nomic-embed-code) and click "Access repository" to accept the terms
3. Generate a token at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Run the setup script to configure your token:

   ```bash
   python tools/setup_huggingface.py
   ```

## Generate Embeddings

To generate embeddings using the Nomic Embed Code model:

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Ensure you have a `structures.json` file in the `data/` directory that contains your code structures.

3. Run the embedding generation script:

   ```bash
   ./tools/generate_nomic_embeddings.py
   ```

4. The script will generate an `embeddings.json` file in the `data/` directory.

## Usage in Code

You can use the `NomicEmbeddingsProvider` in your code as follows:

```python
from code_search.model import NomicEmbeddingsProvider

# Initialize the provider
provider = NomicEmbeddingsProvider()

# Embed code
code_embedding = provider.embed_code(code="def hello(): print('Hello world')")

# Embed a query (for search)
query_embedding = provider.embed_query("function that prints hello world")
```

## Performance Comparison

| Model                    | Python   | Java     | Ruby     | PHP      | JavaScript | Go       |
| ------------------------ | -------- | -------- | -------- | -------- | ---------- | -------- |
| **Nomic Embed Code**     | **81.7** | **80.5** | 81.8     | **72.3** | 77.1       | **93.8** |
| Voyage Code 3            | 80.8     | **80.5** | **84.6** | 71.7     | **79.2**   | 93.2     |
| OpenAI Embed 3 Large     | 70.8     | 72.9     | 75.3     | 59.6     | 68.1       | 87.6     |
| Nomic CodeRankEmbed-137M | 78.4     | 76.9     | 79.3     | 68.8     | 71.4       | 92.7     |
