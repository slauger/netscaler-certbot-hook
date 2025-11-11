# Contributing to NetScaler Certbot Hook

Thank you for your interest in contributing to NetScaler Certbot Hook!

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR-USERNAME/netscaler-certbot-hook.git
cd netscaler-certbot-hook
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

3. Make your changes in a feature branch:
```bash
git checkout -b feature/your-feature-name
```

## Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: A new feature (triggers MINOR version bump)
- **fix**: A bug fix (triggers PATCH version bump)
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes or bug fixes
- **perf**: Performance improvements (triggers PATCH version bump)
- **test**: Adding or updating tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Breaking Changes

Add `BREAKING CHANGE:` in the commit footer or `!` after the type to trigger a MAJOR version bump:

```
feat!: remove support for Python 3.5

BREAKING CHANGE: Python 3.5 is no longer supported
```

### Examples

**Feature (MINOR version bump):**
```
feat(cli): add --dry-run flag for testing without changes

This allows users to preview what would happen without making actual changes to NetScaler.
```

**Bug Fix (PATCH version bump):**
```
fix(nitro): handle timeout errors gracefully

Previously timeout errors would crash the application. Now they are caught
and reported with a user-friendly error message.
```

**Documentation:**
```
docs(readme): update installation instructions for Python 3.12
```

**Breaking Change (MAJOR version bump):**
```
feat!: change default behavior of chain certificate updates

BREAKING CHANGE: Chain certificates are now updated by default. Use --no-update-chain to disable.
```

## Pull Request Process

1. Update documentation if you're adding or changing features
2. Follow the commit message convention above
3. Ensure the code follows PEP 8 style guidelines
4. Add type hints to new functions
5. Update CHANGELOG.md if making manual changes (optional - automated on release)
6. Create a pull request with a clear description of the changes

## Code Quality Guidelines

- **Type Hints**: All functions should have type hints
- **Docstrings**: Use Google-style docstrings for all public functions
- **Error Handling**: Use specific exception types with clear error messages
- **Logging**: Use the logging framework instead of print statements
- **PEP 8**: Follow Python style guidelines

## Testing

Currently, the project uses manual testing. When adding features:

1. Test the CLI command manually
2. Verify error handling works correctly
3. Test with different NetScaler versions if possible

## Release Process

Releases are automated using GitHub Actions and python-semantic-release:

1. Merge commits to `master` branch
2. GitHub Actions automatically:
   - Analyzes commit messages
   - Determines the next version (MAJOR.MINOR.PATCH)
   - Updates version in `pyproject.toml` and `__init__.py`
   - Generates CHANGELOG.md
   - Creates a git tag (e.g., `v1.2.3`)
   - Publishes to TestPyPI
   - Publishes to PyPI

## Questions?

Feel free to open an issue for any questions or concerns!
