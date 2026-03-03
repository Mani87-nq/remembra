# Contributing to Remembra

First off, thanks for taking the time to contribute! 🎉

## Ways to Contribute

### 🐛 Bug Reports

Found a bug? [Open an issue](https://github.com/remembra-ai/remembra/issues/new) with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Version info (`remembra --version`)

### 💡 Feature Requests

Have an idea? [Open an issue](https://github.com/remembra-ai/remembra/issues/new) with:
- Clear use case
- Proposed solution
- Alternatives considered

### 🔧 Pull Requests

1. Fork the repo
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/remembra
cd remembra

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Start dev server
remembra-server --reload
```

## Code Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Type hints required for all public functions
- Docstrings for public modules, classes, and functions
- Tests for new features

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add conversation ingestion endpoint
fix: Handle empty query in recall
docs: Update MCP server guide
chore: Bump dependencies
```

## Questions?

- [Discord](https://discord.gg/remembra)
- [GitHub Discussions](https://github.com/remembra-ai/remembra/discussions)

Thanks for helping make Remembra better! 🚀
