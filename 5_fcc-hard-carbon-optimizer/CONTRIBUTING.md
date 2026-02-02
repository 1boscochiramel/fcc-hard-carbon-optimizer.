# Contributing to FCC Hard Carbon Optimizer

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs
1. Check if the bug already exists in [Issues](https://github.com/yourusername/fcc-hard-carbon-optimizer/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS

### Suggesting Features
1. Open an issue with the `enhancement` label
2. Describe the feature and use case
3. Discuss implementation approach

### Pull Requests
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/fcc-hard-carbon-optimizer.git
cd fcc-hard-carbon-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black

# Run tests
pytest tests/ -v

# Format code
black src/
```

## Code Style
- Follow PEP 8
- Use type hints where possible
- Add docstrings to functions/classes
- Keep functions focused and small

## Testing
- Add tests for new features
- Maintain >80% code coverage
- Run full test suite before PR

## Questions?
Open an issue or contact maintainers.

Thank you for contributing! 🙏
