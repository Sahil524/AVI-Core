# Contributing to AVI Core

Thank you for your interest in contributing to **AVI Core**! We welcome bug reports, feature suggestions, documentation updates, and pull requests.

## Development Setup

To set up a local development environment:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Sahil524/avicore.git
   cd avicore
   ```

2. **Install Dependencies**:
   It is recommended to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Obtain FFmpeg**:
   Place a compiled `ffmpeg.exe` binary inside the `bin/` directory in the project root. This folder and binary are ignored by Git.

## Code Quality Standards

We use `ruff` for formatting and linting, and `mypy` for static type verification.

* **Format Code**:
  ```bash
  ruff format .
  ```
* **Lint Code**:
  ```bash
  ruff check .
  ```
* **Type Check**:
  ```bash
  mypy .
  ```

## Running Tests

We use `pytest` for unit testing. Make sure to run all tests before opening a pull request:
```bash
pytest --cov=avicore
```

## Pull Request Guidelines

1. Fork the repository and create your branch from `main`.
2. Follow Conventional Commits for commit messages (e.g. `feat: ...`, `fix: ...`, `docs: ...`).
3. Ensure the test suite passes completely.
4. Open a pull request targeting the `main` branch. Provide a clear description of the problem solved and modifications made.
