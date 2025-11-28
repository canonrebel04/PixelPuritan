# PixelPuritan

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![CI](https://github.com/canonrebel04/PixelPuritan/actions/workflows/ci.yml/badge.svg)

**AI-powered NSFW content detection and organization toolkit**

PixelPuritan combines the raw speed of Rust for file operations with the accuracy of Vision Transformers (ViT) for content classification, orchestrating everything through a resilient Bash pipeline.

## ✨ Features

- **🦀 Rust-Powered Splitter**: Instantly organizes directories with 10,000+ files into manageable batches of 1,000
- **🤖 State-of-the-Art AI**: Uses [AdamCodd/vit-base-nsfw-detector](https://huggingface.co/AdamCodd/vit-base-nsfw-detector) (Vision Transformer) for superior accuracy
- **🔄 Resilient Pipeline**: Fully resume-capable - picks up exactly where it left off after crashes
- **💾 Robosync Integration**: Optional integration for secure, verified backups of batches before processing
- **🔒 Local & Private**: 100% offline inference via Dockerized API server - no data leaves your network

## 🏗 System Architecture

- **pp-split** (Rust): Scans target directory and sorts loose files into `batch_XXX` folders
- **pp-batcher** (Bash): The orchestrator - iterates through batches, triggers backups, and calls the scanner
- **pp-scan** (Python Client): Specialized async client that sends images to the AI server (optimized for 6GB VRAM GPUs)
- **AI Server** (Docker): FastAPI container running PyTorch and Transformers

## 🚀 Installation

### Prerequisites

- **OS**: Linux (Arch/CachyOS, Debian, Fedora)
- **Docker**: Required for the AI Server
- **NVIDIA GPU**: Recommended (6GB+ VRAM)
- **Rust Toolchain**: `sudo pacman -S rustup && rustup defualt nightly` (or equivalent for your distro)
- **Python**: 3.10+

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/canonrebel04/PixelPuritan.git
   cd PixelPuritan
   ```

2. Run the installer:
   ```bash
   ./install.sh
   ```

   This will:
   - Compile the Rust binary
   - Link commands to `~/.local/bin`
   - Build the Docker container


## 💻 Usage

### Automated Pipeline (Recommended)

Use the batcher to split, sync, and scan a large directory:

```bash
pp-batcher /path/to/your/dataset [optional_backup_path]
```

**What happens:**
1. **Split**: Automatically chunks files into `batch_001`, `batch_002`, etc.
2. **Sync**: If robosync is installed, backs up the batch to the destination
3. **Scan**: Classifies images into `./nsfw` and `./safe` subfolders
4. **Resume**: Run the same command again to resume after a stop/crash

### Manual Scanning

Scan a single folder or file without splitting or syncing:

```bash
pp-scan /path/to/specific/folder --move
```

**Options:**
- `--move` (`-m`): Physically moves files into `nsfw/` and `safe/` folders
- `--verbose` (`-v`): Shows safe files in output (default only shows NSFW and errors)

## ⚙️ Configuration

### AI Server

- Runs on port `8000`
- Model: [AdamCodd/vit-base-nsfw-detector](https://huggingface.co/AdamCodd/vit-base-nsfw-detector)
- Configuration: `server/main.py`

### Client Concurrency

The client is tuned to prevent GPU OOM (Out of Memory) errors on mid-range cards (like the GTX 1060 6GB).

- **Default**: 4 concurrent requests
- **Modify**: Edit `src/client/nsfw_tool.py` and change `CONCURRENT_REQUESTS`
  - For RTX 3090/4090: Set to 8-16 for better performance

## 🛠 Troubleshooting

### "Connection Refused"

Ensure the Docker container is running:

```bash
docker ps
# If not running:
cd ~/.local/share/PixelPuritan/server && docker compose up -d
```

### "Rust binary not found"

Re-run the installer to recompile:

```bash
./install.sh
```

### GPU Out of Memory

If the scanner crashes during processing, reduce concurrency in `src/client/nsfw_tool.py`.

## 🔐 Authentication (Optional)

To require an API key for the server, set:

```bash
export PIXELPURITAN_API_KEY="your-secret"
```

The client will automatically send `X-API-Key` if the same env var is set.

## 📈 Metrics

The server exposes Prometheus metrics at `GET /metrics`, including request counters and inference latency histogram. Point Prometheus at `http://<server>:8000/metrics`.

## 🧩 CPU vs GPU Compose

- **CPU (Default):** `server/compose.yml` builds a CPU-only image using `python:3.10-slim` and installs PyTorch (CPU).
- **GPU (Optional):** `server/compose.gpu.yml` requests GPU via the NVIDIA runtime. To use GPU, you must:
   - Install NVIDIA drivers and the Docker NVIDIA runtime.
   - Use a CUDA-enabled base image and PyTorch with CUDA in your local environment.
   - Review NVIDIA's EULA; avoid publishing images containing proprietary CUDA libraries unless redistribution is permitted.

## 🚦 Rate Limiting

The server enforces an optional per-IP rate limit via a token bucket:

- `PIXELPURITAN_RATE_LIMIT_RPS` (default `5`) — tokens refilled per second
- `PIXELPURITAN_RATE_LIMIT_BURST` (default `10`) — maximum burst capacity

When exceeded, the server returns `429 Too Many Requests`.

## 🧪 Benchmarking

Use the async benchmark tool to measure throughput and latency:

```bash
export PIXELPURITAN_API_URL="http://localhost:8000/v1/detect"
export BENCH_CONCURRENCY=4
export BENCH_ROUNDS=50
python scripts/bench_client.py
```

If `BENCH_IMAGE` does not exist, the benchmark will auto-generate a small sample PNG (requires Pillow).

## ⚙️ Configuration

You can configure defaults via `~/.config/pixelpuritan/config.ini` (overridden by environment variables):

```ini
[client]
api_url = http://localhost:8000/v1/detect
concurrency = 4

[server]
rate_limit_rps = 5
rate_limit_burst = 10
```




## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, coding standards, and workflow. Please follow the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 🔒 Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

## 📜 License

This project is licensed under the GNU GPL v3. See [LICENSE](LICENSE) for details.

