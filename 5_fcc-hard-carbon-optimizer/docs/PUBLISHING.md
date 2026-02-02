# Publishing to PyPI

This guide explains how to publish the FCC Hard Carbon Optimizer package to PyPI.

## Prerequisites

1. Create accounts on:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. Install build tools:
   ```bash
   pip install build twine
   ```

## Manual Publishing

### Step 1: Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Build source distribution and wheel
python -m build
```

This creates:
- `dist/fcc_hard_carbon-1.0.0.tar.gz` (source distribution)
- `dist/fcc_hard_carbon-1.0.0-py3-none-any.whl` (wheel)

### Step 2: Verify the Package

```bash
# Check package metadata
twine check dist/*

# Test installation locally
pip install dist/fcc_hard_carbon-1.0.0-py3-none-any.whl
fcc-hard-carbon --version
```

### Step 3: Upload to TestPyPI (Recommended First)

```bash
twine upload --repository testpypi dist/*
```

Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fcc-hard-carbon
```

### Step 4: Upload to PyPI

```bash
twine upload dist/*
```

## Automated Publishing (GitHub Actions)

The repository includes a GitHub Actions workflow (`.github/workflows/publish.yml`) that automates publishing.

### Setup

1. **Configure PyPI Trusted Publisher** (Recommended):
   - Go to PyPI → Your projects → fcc-hard-carbon → Settings → Publishing
   - Add a new "GitHub" publisher:
     - Owner: `yourusername`
     - Repository: `fcc-hard-carbon-optimizer`
     - Workflow: `publish.yml`

2. **Or use API Token** (Alternative):
   - Create API token on PyPI
   - Add as GitHub secret: `PYPI_API_TOKEN`

### Publishing

**Option A: Create a GitHub Release**
1. Go to GitHub → Releases → "Create a new release"
2. Tag version: `v1.0.0`
3. Release title: `v1.0.0`
4. Publish release
5. Package automatically publishes to PyPI

**Option B: Manual Workflow Dispatch**
1. Go to GitHub → Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Select `testpypi` or `pypi`
4. Click "Run workflow"

## Version Bumping

1. Update version in:
   - `src/fcc_hard_carbon/__init__.py`
   - `pyproject.toml`

2. Update `CHANGELOG.md`

3. Commit and tag:
   ```bash
   git add .
   git commit -m "Bump version to 1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```

## Troubleshooting

### "File already exists" Error
Each version can only be uploaded once. Bump the version number.

### "Invalid distribution" Error
Run `twine check dist/*` to see detailed errors.

### Missing Dependencies
Users need to install with extras for dashboard:
```bash
pip install fcc-hard-carbon[dashboard]
```

## Package Structure

```
fcc-hard-carbon/
├── pyproject.toml          # Package metadata (PEP 621)
├── MANIFEST.in             # Non-Python files to include
├── src/
│   └── fcc_hard_carbon/
│       ├── __init__.py     # Version, exports
│       ├── cli.py          # CLI entry point
│       ├── models.py       # Core predictors
│       ├── optimization.py # LHS, sensitivity
│       ├── economics.py    # Business case
│       └── py.typed        # PEP 561 type hints marker
└── dist/
    ├── fcc_hard_carbon-1.0.0.tar.gz    # Source dist
    └── fcc_hard_carbon-1.0.0-py3-none-any.whl  # Wheel
```

## Links

- [PyPI Project Page](https://pypi.org/project/fcc-hard-carbon/)
- [TestPyPI Project Page](https://test.pypi.org/project/fcc-hard-carbon/)
- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
