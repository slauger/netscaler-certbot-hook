# CHANGELOG

## v1.0.1 (2025-11-11)

### Ci

* ci: add GitHub Actions workflows and semantic versioning (#8)

- Add release.yml workflow for automated versioning and PyPI publishing
  - Uses python-semantic-release for automated version bumping
  - Publishes to TestPyPI and PyPI on release
  - Creates git tags automatically based on conventional commits

- Add test.yml workflow for CI testing
  - Tests across Python 3.6-3.12
  - Verifies package builds correctly
  - Runs on PRs and master branch pushes

- Configure semantic-release in pyproject.toml
  - Conventional commits (Angular style)
  - Automatic CHANGELOG.md generation
  - Version syncing in multiple locations

- Add CONTRIBUTING.md with commit convention guidelines
  - Explains semantic versioning
  - Documents commit message format
  - Provides examples for different change types

- Clean up README.md
  - Remove Troubleshooting section
  - Remove Development section (moved to CONTRIBUTING.md)
  - Remove Acknowledgments section
  - Link to CONTRIBUTING.md for contribution guidelines ([`3d1d924`](https://github.com/slauger/netscaler-certbot-hook/commit/3d1d924133164a8820c292e57f1d00db9e1f6752))

### Fix

* fix(ci): combine test and release workflows, drop Python 3.6/3.7 support (#9)

- Merge test.yml and release.yml into single workflow
- Tests must pass before release can run
- Release only runs on push to master, not on PRs
- Remove Python 3.6 and 3.7 from test matrix (EOL, not available on ubuntu-latest)
- Update minimum Python version to 3.8 in pyproject.toml
- Update Python version badge and prerequisites in README.md

This ensures releases only happen when all tests pass successfully. ([`a68aa9b`](https://github.com/slauger/netscaler-certbot-hook/commit/a68aa9bfb8cacde5004c1aa0dd9a2e8e8eb10b51))

## v1.0.0 (2025-11-11)

### Documentation

* docs: Comprehensive README.md overhaul

Completely rewrote README.md with professional structure and detailed
documentation for production use.

## Major Improvements

### Structure &amp; Organization
- Added badges (License, Python version)
- Clear feature list with checkmarks
- Organized sections with proper hierarchy
- Professional formatting throughout

### New Sections Added
- **Features** - Comprehensive list of capabilities
- **Prerequisites** - System requirements clearly stated
- **Installation** - Two installation methods (pip, package)
- **Configuration** - Tables for environment variables and CLI args
- **Usage** - Step-by-step guide with examples
  - Certbot enrollment examples (multiple DNS providers)
  - Basic and advanced usage examples
  - Automation with cron and deploy hooks
- **Example Output** - Three scenarios (initial, update, no-change)
- **Security Considerations** - Chain cert handling, credentials, SSL
- **Troubleshooting** - Common issues with solutions
- **API Reference** - Link to NITRO API docs
- **Development** - Contributing guidelines, code quality
- **Acknowledgments** - Credits to tools and services

### Enhanced Content
- Environment variables documented in table format
- Command-line arguments documented in table format
- Multiple Certbot DNS provider examples (Cloudflare, Route53, Google)
- Cron automation examples
- Certbot deploy hook script example
- Detailed troubleshooting for common errors
- Security best practices for credential management
- Exit codes documented

### Professional Polish
- Consistent formatting
- Code blocks properly syntax-highlighted
- Clear headers and navigation
- Links to external resources
- Call-to-action at the end

## Statistics
- Before: ~87 lines, basic documentation
- After: ~350 lines, comprehensive guide
- 4x more content with better organization

## TODO.md Updates
- Marked completed phases with ✅
- Updated progress tracking
- Shows what&#39;s done vs. what&#39;s pending

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`36b83db`](https://github.com/slauger/netscaler-certbot-hook/commit/36b83dba7b519d9c17da64a0d3239ee68076d6da))

### Fix

* fix: convert environment variable to boolean value (#3) ([`dde1a43`](https://github.com/slauger/netscaler-certbot-hook/commit/dde1a43f7b5e76f4d3045c3d6b13ecbac1cb0c64))

### Unknown

* Restructure as PyPI-ready package with console script (#7)

* Restructure as PyPI-ready package with console script

Transform the project into a proper Python package structure ready
for PyPI distribution, with system-wide command installation.

Package Structure:
- Created src/netscaler_certbot_hook/ package directory
- Moved code into proper package structure:
  - __init__.py - Package initialization and exports
  - __main__.py - Entry point for python -m execution
  - cli.py - Main CLI logic (from netscaler-certbot-hook.py)
  - nitro.py - NITRO API client

Build Configuration:
- Created pyproject.toml (modern Python packaging)
- Configured console_scripts entry point for system command
- Fixed license format (MIT string vs file)
- Removed deprecated License classifier
- Added comprehensive package metadata and keywords

Installation Methods After This Change:
1. From PyPI (when published):
   pip install netscaler-certbot-hook
   netscaler-certbot-hook --name example.com

2. From source:
   pip install -e .
   netscaler-certbot-hook --name example.com

3. As module:
   python -m netscaler_certbot_hook --name example.com

Console Script:
- Command: netscaler-certbot-hook
- Installed to: /usr/local/bin/ (or venv bin/)
- Works like: certbot, aws, pip, etc.

Documentation Updates:
- Updated installation instructions for PyPI
- Replaced all python3 netscaler-certbot-hook.py calls
- Updated cron examples to use system command
- Updated deploy hook examples
- Added note about command vs module execution

Build Files:
- Created MANIFEST.in for additional files
- Updated .gitignore for build artifacts
- Successfully tested: python3 -m build

Benefits:
- Professional Python package structure
- pip install directly from PyPI
- System-wide command after installation
- No need to specify script path in cron
- Standard Python packaging best practices
- Ready for PyPI publication

Breaking Changes:
- None - old netscaler-certbot-hook.py still works
- New package structure is additive

Next Steps for PyPI Publication:
1. Test installation: pip install dist/*.whl
2. Upload to TestPyPI: twine upload --repository testpypi dist/*
3. Test from TestPyPI
4. Upload to PyPI: twine upload dist/*

* Remove legacy files (moved to package structure)

Remove old root-level Python files that are now part of the
proper package structure in src/netscaler_certbot_hook/:

- netscaler-certbot-hook.py -&gt; src/netscaler_certbot_hook/cli.py
- nitro.py -&gt; src/netscaler_certbot_hook/nitro.py
- setup.py -&gt; replaced by pyproject.toml (modern packaging)

All functionality is preserved in the new package structure.

* Fix README: use netscaler-certbot-hook command in --update-chain examples

Replace remaining python3 netscaler-certbot-hook.py calls
with the new netscaler-certbot-hook system command. ([`6828b8a`](https://github.com/slauger/netscaler-certbot-hook/commit/6828b8ad0b2515787af905c56a9a626452eed813))

* Merge pull request #6 from slauger/feature/update-chain-flag

Add --update-chain flag for chain certificate updates ([`1eec8ca`](https://github.com/slauger/netscaler-certbot-hook/commit/1eec8ca1db22cac7d44b35bdd6fc7564f3bb4ee1))

* Add --update-chain flag for chain certificate updates

Implements feature request from issue #4 to allow updating chain
certificates when trust chains change (e.g., Let&#39;s Encrypt root
certificate rotation).

Changes:
- Added --update-chain command-line flag (default: false)
- Modified process_chain_certificate() to support chain updates
- Chain updates only occur when --update-chain flag is set
- Added warning log message when chain is being updated
- Shows old and new serial numbers in logs during update
- Improved error message to suggest --update-chain flag

Documentation:
- Added --update-chain to command-line arguments table
- Added usage example for chain certificate updates
- Updated Security Considerations section
- Added when to use --update-chain guidelines
- Added security warning about chain updates
- Updated CHANGELOG.md with feature details

Security:
- Chain updates remain disabled by default
- Explicit opt-in required via --update-chain flag
- Prevents unexpected trust chain changes
- Maintains backward compatibility

Fixes #4 ([`4db247f`](https://github.com/slauger/netscaler-certbot-hook/commit/4db247ff9a025266a0e96b8e9c2768679270ba2b))

* Merge pull request #5 from slauger/feature/code-quality-improvements

Comprehensive Code Quality Improvements ([`75b2eae`](https://github.com/slauger/netscaler-certbot-hook/commit/75b2eae8f299e5455aebfc2d34132ca223ab73af))

* Release v1.0.0 - Production Ready

Add CHANGELOG.md and bump version to 1.0.0 to reflect the comprehensive
improvements made to the codebase.

Changes:
- Created CHANGELOG.md with complete version history
- Bumped version from 0.0.1 to 1.0.0 in:
  - netscaler-certbot-hook.py
  - nitro.py
  - setup.py
- Updated setup.py classifier to Production/Stable
- Added TODO.md to .gitignore (project-specific planning file)

Rationale for 1.0.0:
This release represents a complete overhaul transforming the project
from a working script into a production-ready application with:
- Professional error handling
- Structured logging framework
- Comprehensive documentation
- Full type hints and docstrings
- Modern Python development practices
- 100% backward compatibility

The extensive improvements justify a major version bump to 1.0.0,
signaling production readiness and stability. ([`5beca73`](https://github.com/slauger/netscaler-certbot-hook/commit/5beca73280521f60477793be6f3fa1a5729aad49))

* Implement logging framework (Phase 1.3)

Replace all print() statements with Python&#39;s built-in logging module for structured, configurable output.

Changes:
- Added logging module import and logger initialization
- Replaced all 18 print() statements with logger.info/debug/error calls
- Added --verbose flag for DEBUG level output
- Added --quiet flag for ERROR-only output
- Created setup_logging() function for log configuration
- Added debug messages for connection and workflow steps
- Updated error handler to use logger when available
- Enhanced add_argument() to support action parameter

Documentation:
- Added logging section to README.md with examples
- Documented --verbose and --quiet flags
- Added cron job logging examples
- Updated command-line arguments table
- Marked Phase 1.3 as completed in TODO.md

Benefits:
- Configurable verbosity for different use cases
- Structured output format
- Better integration with cron jobs and automation
- Professional logging standards ([`7f5206b`](https://github.com/slauger/netscaler-certbot-hook/commit/7f5206b1da95e8cf3dda4aa5188564551e60eb65))

* Merge branch &#39;master&#39; into feature/code-quality-improvements

Resolved merge conflict by keeping refactored code from feature branch.

The master branch contained the old code from save-nsconfig merge, but our
feature branch has the complete refactoring with all improvements. Our
refactored version includes all functionality from master plus:

- Full type hints
- Comprehensive docstrings
- Better error handling
- Improved code structure
- Complete validation

Conflict resolution: Kept &#39;ours&#39; (feature branch) version.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`e862a0c`](https://github.com/slauger/netscaler-certbot-hook/commit/e862a0c847ccbabb5b64c4139fcc3bd15631c27e))

* save netscaler configuration (#1)

- save netscaler config after changes
- do not throw execption if a certificate link is already present ([`2b2ddc9`](https://github.com/slauger/netscaler-certbot-hook/commit/2b2ddc913f4ebdfee1c599ac41263a48c869d147))

* Refactor: Comprehensive code quality improvements

This commit includes a major refactoring of the codebase to improve
maintainability, readability, and professional code standards.

## Phase 1: Code Structure Refactoring (1.2)

### Main Script (netscaler-certbot-hook.py)
- Refactored linear code into well-structured functions
- Extracted argument parsing into parse_arguments()
- Extracted configuration into get_config() with validation
- Created get_certificate_serial() for certificate handling
- Split certificate logic into process_chain_certificate() and process_certificate()
- Eliminated code duplication with install_or_update_certificate()
- Added proper main() function with if __name__ == &#39;__main__&#39; block
- Improved exit codes and error handling

### Bug Fixes
- Fixed verify_ssl Boolean conversion (was incorrectly parsed as string)
- Added proper file existence validation before processing
- Added URL format validation (http:// or https:// prefix)
- Added empty credentials validation

## Phase 2: Project Files (2.2)

### New Files Created
- requirements.txt: Dependencies with version constraints
- .gitignore: Comprehensive Python and security-aware ignore rules
- setup.py: Full PyPI-ready installation script
- LICENSE: MIT License file
- TODO.md: Structured improvement roadmap

## Phase 3: Error Handling (1.1)

### Improved Exception Handling
- Replaced all bare except: blocks with specific exception types
- Added detailed error messages with context
- Implemented proper exception handling for:
  - File operations (FileNotFoundError, IOError)
  - Network operations (Timeout, ConnectionError, HTTPError)
  - Certificate parsing (crypto.Error, ValueError)
  - Configuration validation (ValueError)

### NITRO Client (nitro.py)
- Added 30-second timeout for all requests
- Specific exception types for all error scenarios
- Better error messages with URLs for debugging
- Proper JSON parsing error handling

## Phase 4: Documentation

### Module Headers
- Comprehensive module-level docstrings with usage examples
- Environment variables documented
- Command-line examples included
- Links to official API documentation

### Function Documentation
- All 14 functions in main script fully documented
- All 15 methods in NitroClient class fully documented
- Google/NumPy style docstrings with:
  - Args with type information
  - Returns with type information
  - Raises for all exceptions
  - Examples for complex functions
  - Notes for important behaviors

## Phase 5: Type Hints

### Complete Type Annotation
- Added typing imports (Dict, Optional, Union, Any)
- All function signatures type-hinted
- All method signatures type-hinted
- Class attributes type-hinted in __init__
- Return types specified for all functions
- Enables IDE autocomplete and mypy checking

### Code Quality Improvements
- PEP 8 compliant formatting in nitro.py (4-space indentation)
- Consistent parameter naming and formatting
- Better code organization with clear sections
- Improved readability throughout

## Statistics

### netscaler-certbot-hook.py
- Before: ~271 lines, mostly linear code
- After: ~567 lines with full documentation
- 14 well-documented functions
- Complete type hints
- Production-ready error handling

### nitro.py
- Before: ~99 lines, basic implementation
- After: ~334 lines with full documentation
- 15 fully documented methods
- Complete type hints
- Professional API client implementation

## Impact

This refactoring transforms the codebase from a working script into a
professional, maintainable, well-documented Python project suitable for
production use and collaborative development.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`c8153d0`](https://github.com/slauger/netscaler-certbot-hook/commit/c8153d05b44fd02a16285ed8471e6ece1a834202))

* fix typo ([`5e7dd9a`](https://github.com/slauger/netscaler-certbot-hook/commit/5e7dd9a5412641daa5e0be0b4f9a8601497d7f5c))

* add missing objecttype ([`b2fb25b`](https://github.com/slauger/netscaler-certbot-hook/commit/b2fb25b6c71ed928bf7696537c732ec2f0262a36))

* remove some whitespaces... ([`4399f44`](https://github.com/slauger/netscaler-certbot-hook/commit/4399f4416b6075ec363c778f1414c1bed69b08e3))

* fix print statemetn ([`16d7f05`](https://github.com/slauger/netscaler-certbot-hook/commit/16d7f0548c285a19b03b523458b0c3fe3af46142))

* fix print statemetn ([`198e756`](https://github.com/slauger/netscaler-certbot-hook/commit/198e7568b6b458a0c2f0048efebab34fa754f739))

* save netscaler configuration ([`410be12`](https://github.com/slauger/netscaler-certbot-hook/commit/410be12ada53bb73919079778552ee986dd1b2d1))

* fix typo ([`f713747`](https://github.com/slauger/netscaler-certbot-hook/commit/f7137473858b41320326805760302291ff3ecb1b))

* inital ([`b4937ab`](https://github.com/slauger/netscaler-certbot-hook/commit/b4937ab2aad9eab0809f7a3a24d5c6224812ff58))

* first commit ([`411b38b`](https://github.com/slauger/netscaler-certbot-hook/commit/411b38b71c2d39ff79029b305f4014351fcbb0f8))
