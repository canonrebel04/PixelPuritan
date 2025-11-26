Third-Party Licenses and Attribution

This project is licensed under GPLv3 (see `LICENSE`). Below are the third-party components used and their licenses. All listed licenses are compatible with GPLv3. When distributing binaries or Docker images, include this notice and upstream license texts where required.

Python Dependencies (`server/requirements.txt`)
- FastAPI — MIT License
- Uvicorn (standard extras) — BSD-3-Clause
- python-multipart — Apache-2.0
- PyTorch (`torch`) — BSD-3-Clause
- Transformers — Apache-2.0
- Pillow — HPND (PIL License)

Docker Base Image
- `python:3.10-slim` — Derived from Debian; components under various permissive licenses (PSF/Apache/BSD). Compatible with GPLv3.

Model Weights
- AdamCodd/vit-base-nsfw-detector — License: See model card on Hugging Face. Typically Apache-2.0 or MIT; ensure attribution and include license notice when redistributing weights.
  - Attribution: "Uses AdamCodd/vit-base-nsfw-detector for NSFW image classification."

Rust Splitter
- No external crates detected (no `Cargo.toml` listing third-party dependencies). If crates are added later, update this file accordingly.

Optional Tools
- robosync (optional backup tool) — License unknown. If used or redistributed, verify its license and include attribution/notice.

Notes on Distribution
- If publishing Docker images, avoid bundling proprietary NVIDIA CUDA libraries unless permitted by NVIDIA’s EULA; proprietary components may impose redistribution restrictions incompatible with GPLv3 distribution. The current image installs CPU-only dependencies.
- Provide source code or instructions to obtain source, and retain GPLv3 notices for covered works.
