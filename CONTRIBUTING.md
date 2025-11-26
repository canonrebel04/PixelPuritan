Contributing to PixelPuritan

Thank you for your interest in contributing! This document outlines how to propose changes and the development workflow.

Getting Started
- Fork the repo and create a feature branch from `main`.
- Ensure Python 3.10+ and Rust stable are installed.
- Set up Python env: `cd server && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`.
- Build Rust: `cd src/splitter && cargo build`.

Coding Standards
- Python: follow PEP8; type hints preferred.
- Rust: use `rustfmt` and `clippy`.
- Keep changes focused; avoid unrelated refactors.

Commit Messages
- Conventional commits encouraged: `feat:`, `fix:`, `docs:`, `chore:`.
- Reference issues when applicable.

Pull Requests
- Include a clear description, screenshots/logs when relevant.
- Add/adjust tests when feasible.
- Ensure CI passes.

Issue Reporting
- Use the bug report template; include reproduction steps and environment details.

Security
- Do not file vulnerabilities publicly; follow `SECURITY.md`.
