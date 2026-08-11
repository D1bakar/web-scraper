# Contributing to Web Scraper Pro

Thank you for your interest in contributing. This project welcomes bug fixes, documentation improvements, and well-scoped feature additions.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

3. Copy `.env.example` to `.env` and run the app locally:

   ```bash
   uvicorn app.main:app --reload
   ```

## Development Workflow

1. Create a feature branch from `main`.
2. Make your changes with clear, focused commits.
3. Run lint and tests before opening a pull request:

   ```bash
   ruff check app/ cli.py tests/
   pytest tests/ -v
   ```

4. Open a pull request against `main` with a concise description of the change and how you tested it.

## Code Guidelines

- Match existing style: type hints, async where appropriate, minimal scope.
- Add tests for new behavior in `tests/`.
- Keep scraping defaults polite — respect robots.txt and rate limits.
- Do not commit secrets, `.env` files, or generated output in `data/` or `output/`.

## Reporting Issues

Use [GitHub Issues](https://github.com/D1bakar/web-scraper/issues) for bugs and feature requests. Include steps to reproduce, expected vs. actual behavior, and your environment (OS, Python version).

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities privately.
