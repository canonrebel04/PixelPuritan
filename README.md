PixelPuritan

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![CI](https://github.com/${OWNER}/PixelPuritan/actions/workflows/ci.yml/badge.svg)

PixelPuritan

Overview
- A toolkit for detecting and managing NSFW content, with a Rust-based splitter and a Python server/client utility.

Features
- NSFW detection utilities (`src/client/nsfw_tool.py`).
- High-performance media splitter in Rust (`src/splitter`).
- Containerized server with Docker Compose (`server/compose.yml`).
- CLI batcher in `bin/pp-batcher`.

Getting Started
- Prerequisites: Python 3.10+, Rust stable, Docker (optional).
- Install Python deps:
	- `cd server && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
- Build Rust splitter:
	- `cd src/splitter && cargo build --release`

Run Server (Docker)
- `cd server && docker compose up --build`

Local Development
- Create a virtualenv and install deps as above.
- Run `python server/main.py` for local testing.

Contributing
- See `CONTRIBUTING.md` for guidelines, coding standards, and workflow.
- Please follow the `CODE_OF_CONDUCT.md`.

Security
- See `SECURITY.md` for reporting vulnerabilities.

License
- This project is licensed under the GNU GPL v3. See `LICENSE` for details.

It combines the raw speed of Rust for file operations with the accuracy of Vision Transformers (ViT) for content classification, orchestrating everything through a resilient Bash pipeline.

⚡ Features

Rust-Powered Splitter: Instantly organizes directories with 10,000+ files into manageable chunks (batches) of 1,000.

State-of-the-Art AI: Uses AdamCodd/vit-base-nsfw-detector (Vision Transformer) for superior accuracy over traditional ResNet models.

Resilient Pipeline: Fully resume-capable. If the system crashes, it picks up exactly where it left off.

Robosync Integration: Optional integration with robosync for secure, verified backups of batches before processing.

Local & Private: 100% offline inference via a Dockerized API server. No data leaves your network.

🏗 System Architecture

pp-split (Rust): Scans the target directory and sorts loose files into batch_XXX folders.

pp-batcher (Bash): The orchestrator. It iterates through batches, triggers backups, and calls the scanner.

pp-scan (Python Client): A specialized async client that sends images to the AI server. Optimized for 6GB VRAM GPUs (GTX 1060 friendly).

AI Server (Docker): A FastAPI container running PyTorch and Transformers.

🚀 Installation

Prerequisites

OS: Linux (Arch/CachyOS, Debian, Fedora)

Docker: Required for the AI Server.

NVIDIA GPU: Recommended (6GB+ VRAM).

Rust Toolchain: For compiling the splitter (sudo pacman -S rust).

Python 3.10+

Setup

Enter the project directory:

cd PixelPuritan


Run the installer:

./install.sh


This will compile the Rust binary, link commands to ~/.local/bin, and build the Docker container.

💻 Usage

1. The Automated Pipeline (Recommended)

Use the batcher to split, sync, and scan a large directory.

pp-batcher /path/to/your/dataset [optional_backup_path]


Split: Automatically chunks files into batch_001, batch_002, etc.

Sync: If robosync is installed, backs up the batch to the destination.

Scan: Classifies images into ./nsfw and ./safe subfolders.

Resume: Run the same command again to resume after a stop/crash.

2. Manual Scanning

Scan a single folder or file without splitting or syncing.

pp-scan /path/to/specific/folder --move


--move (-m): Physically moves files into nsfw/ and safe/ folders.

--verbose (-v): Shows safe files in the output list (default only shows NSFW and Errors).

⚙️ Configuration

AI Server

The server runs on port 8000.

Model: AdamCodd/vit-base-nsfw-detector

Logic: Defined in server/main.py.

Client Concurrency

The client is tuned to prevent GPU OOM (Out of Memory) errors on mid-range cards (like the GTX 1060 6GB).

Default: 4 concurrent requests.

Modify: Edit src/client/nsfw_tool.py and change CONCURRENT_REQUESTS if you have a more powerful GPU (e.g., set to 8 or 16 for RTX 3090/4090).

🛠 Troubleshooting

"Connection Refused"
Ensure the Docker container is running:

docker ps
# If not running:
cd ~/.local/share/PixelPuritan/server && docker compose up -d


"Rust binary not found"
Re-run the installer to recompile:

./install.sh


GPU Out of Memory
If the scanner crashes during processing, reduce concurrency in src/client/nsfw_tool.py.

📜 License

Unlicense / MIT. Use freely.
