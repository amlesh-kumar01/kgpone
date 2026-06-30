# Local Infinity Reranker Server

This directory contains a standalone, non-Docker setup for running the [Infinity](https://github.com/michaelfeil/infinity) Text Embeddings Inference server locally, utilizing your host machine's GPU.

We run this locally instead of via Docker to bypass potential WSL2/Docker GPU translation layers and natively access the RTX 4050 for maximum performance.

## Setup & Requirements

This project uses `uv` as the package manager and is pinned to Python 3.11.

1. **Install uv** (if you haven't already):
   You can install it via PowerShell:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Sync Dependencies**:
   This project is pre-configured to download the heavy CUDA 12.1 PyTorch libraries automatically. Simply run:
   ```powershell
   uv sync
   ```

## Starting the Server

To start the server, just run:

```powershell
uv run python main.py
```

### What happens when you run this?
1. The script will initialize a FastAPI server running `infinity-emb`.
2. It will automatically load the `BAAI/bge-reranker-base` cross-encoder model.
3. The model will be placed onto your NVIDIA GPU (`device="cuda"` with the `torch` engine).
4. The server will bind to `0.0.0.0:7997`.

The backend API is already configured to automatically route reranking queries to `http://host.docker.internal:7997`.

## Troubleshooting

- **Server crashes immediately?** Check if you have another application (like a previous docker container) bound to port `7997`.
- **First startup is slow?** The very first time you start the server, it will download the model weights (about 1.1 GB) from Hugging Face. Subsequent startups will be near-instant.
