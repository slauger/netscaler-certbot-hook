# CHANGELOG

## v3.0.0 (2026-09-06)

### Breaking

* fix!: use None as sentinel for --chain auto-detection

Previously the default value letsencrypt doubled as the auto-detect
trigger, so an explicit --chain letsencrypt could never be used as a
literal object name and was silently overridden by the CN detection.

The default is now None: without --chain the name is auto-detected
from the chain certificate CN (falling back to letsencrypt only if
CN extraction fails), any explicit value is respected as-is.

BREAKING CHANGE: --chain letsencrypt is now taken literally instead
of triggering CN auto-detection ([`a4025e5`](https://github.com/slauger/netscaler-certbot-hook/commit/a4025e53d4aec196d46909b003dc1390689a586c))

* build!: migrate to pyproject-only dependencies and require Python 3.12+

- remove requirements.txt and requirements-dev.txt, dev tooling now
  installed via pip install -e .[dev]
- add ruff, black, mypy and pytest configuration to pyproject.toml
- add lint job to tests workflow and run pytest with coverage
- update CI matrices to Python 3.12, 3.13 and 3.14

BREAKING CHANGE: Python &lt; 3.12 is no longer supported ([`2ea6f4f`](https://github.com/slauger/netscaler-certbot-hook/commit/2ea6f4f46d44a2d011fa4dbd469840d06373f7d7))

### Chore

* chore: add renovate configuration (#14) ([`638a30f`](https://github.com/slauger/netscaler-certbot-hook/commit/638a30fcfb8663fba3de1c78c41dbffb8d400473))

### Ci

* ci: run tests workflow on all pull requests

The pull_request branches filter matches the PR base branch, so
stacked PRs that do not target master never got any CI checks. ([`4597540`](https://github.com/slauger/netscaler-certbot-hook/commit/4597540681818919ed22f7f62b4264c023185035))

* ci: install dev dependencies and use pytest in GitHub Actions

The new integration tests require pytest and other dev dependencies
(Flask, requests, etc.) which are defined in requirements-dev.txt.

Changes:
- Install requirements-dev.txt in addition to requirements.txt
- Use &#39;pytest tests/ -v&#39; instead of &#39;unittest discover&#39;
- This enables pytest-based tests (test_chain_rotation.py, test_integration.py)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`52f1481`](https://github.com/slauger/netscaler-certbot-hook/commit/52f1481039ea3695c41c1291389d5d4dbdbe064d))

### Documentation

* docs: replace architecture image with Mermaid diagrams (#16)

* docs: replace architecture image with Mermaid diagrams

- flowchart for the overall certificate flow from Let&#39;s Encrypt
  via Certbot to the NetScaler ADC
- sequence diagram for the idempotent hook logic including chain
  handling and serial comparison
- remove architecture.jpg

* docs: simplify architecture diagrams

- switch overall flow to top-down layout so it no longer overflows
- replace the sequence diagram with a plain decision flowchart ([`5c3a30e`](https://github.com/slauger/netscaler-certbot-hook/commit/5c3a30eeafe69e4a58b3eeb026f3a7b1b81520f2))

### Feature

* feat: add Mock NITRO API server for testing

Implemented a Flask-based mock of the NetScaler NITRO API to enable
testing without requiring a real NetScaler appliance.

Features:
- NITRO authentication with X-NITRO-USER/PASS headers
- Certificate management endpoints (add, update, get)
- Chain certificate linking/unlinking
- Proper error codes and messages matching real NetScaler
- Issue #12 simulation: Prevents linking to multiple chains

Files added:
- tests/mock_nitro/server.py: Flask server with all endpoints
- tests/mock_nitro/state.py: In-memory state management
- tests/mock_nitro/README.md: Documentation and usage
- tests/test_chain_rotation.py: Tests for Issue #12 scenario
- requirements-dev.txt: Development dependencies

All tests passing (4/4):
- test_chain_rotation_without_unlink_fails ✓
- test_chain_rotation_with_unlink_succeeds ✓
- test_link_is_idempotent ✓
- test_authentication_required ✓

This enables local testing and CI/CD without NetScaler hardware. ([`e3b0abe`](https://github.com/slauger/netscaler-certbot-hook/commit/e3b0abe5cf69b28a6cfc9d8dd6d0399144ae616c))

### Fix

* fix: relink certificate to the new chain after a CA rotation

When Let&#39;s Encrypt rotates its intermediate (e.g. E6 -&gt; E7), the new
chain gets installed under its auto-detected name, but the server
certificate stayed linked to the old chain forever: the link attempt
failed on the NetScaler (already linked) and the error was swallowed.
When the certificate serial was unchanged, nothing happened at all.

The hook now reads linkcertkeyname from the sslcertkey response,
unlinks from the old chain and relinks to the configured one - both
during install/update and for an otherwise unchanged certificate.

The chain rotation integration test (issue #12) is now a hard
assertion instead of skipping on failure. ([`b9012e5`](https://github.com/slauger/netscaler-certbot-hook/commit/b9012e547416448f23952223616a14488a5f4a33))

* fix: validate user-supplied NetScaler object names

Explicit --name and --chain values are now checked against the
NetScaler object name rules (ASCII alphanumeric or underscore first,
then alphanumerics plus &#39;_#. :@=-&#39;, at most 31 characters) and fail
fast with a clear error instead of surfacing cryptic NITRO errors.

Auto-detected chain names are unaffected, they are already sanitized
by get_certificate_cn. ([`3a561ad`](https://github.com/slauger/netscaler-certbot-hook/commit/3a561adb51bfe760134549de830351661567d641))

* fix: use dynamic ports for mock servers to avoid port conflicts

Previously, tests used fixed ports (5555, 5556) which caused &#39;Address already
in use&#39; exceptions when Flask server threads didn&#39;t clean up fast enough
between tests. This resulted in noisy test output with many thread exceptions.

Changes:
- Mock server fixtures now find a free port dynamically using socket.bind()
- Each test gets its own unique port, preventing conflicts
- Test output is now clean with no OSError exceptions

Test results: 24 passed, 1 skipped, 1 warning (down from 9 warnings)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`9e8ea44`](https://github.com/slauger/netscaler-certbot-hook/commit/9e8ea44ac59094e13a9ab1e6852ecdde1e240c40))

### Refactor

* refactor: adopt ruff, black and mypy across the codebase

- format all sources and tests with black
- fix ruff findings: exception chaining, unused imports, long lines
- tighten type annotations so mypy passes in strict-ish config
- read certificates in binary mode as required by pyOpenSSL
- drop stale module metadata from cli.py, version lives in
  __init__.py and pyproject.toml ([`bc1399b`](https://github.com/slauger/netscaler-certbot-hook/commit/bc1399b018eecaf52c3a21c285f33cb54a0f706a))

### Test

* test: add comprehensive integration tests with certificate serial tracking

This commit adds end-to-end integration tests that run the complete plugin
against the Mock NITRO API server to verify real-world scenarios.

Changes:
- Add tests/test_integration.py with 6 integration tests covering:
  * Initial certificate installation (fresh NetScaler)
  * Certificate renewal with same chain
  * Idempotent runs (no changes needed)
  * Chain certificate rotation (E6 → E7) for Issue #12
  * Authentication error handling
  * Custom chain name override

- Enhanced Mock NITRO API (tests/mock_nitro/):
  * Store uploaded certificate files in memory
  * Automatically extract serial numbers from uploaded PEM certificates
  * Serial number tracking for renewal detection
  * Realistic certificate state management

The mock server now parses uploaded certificate files using PyOpenSSL to
extract serial numbers, simulating NetScaler&#39;s behavior. This enables
accurate testing of certificate renewal scenarios where the plugin
compares serial numbers to detect changes.

Test for Issue #12 (chain rotation) is included but skipped until the
feature is implemented. It demonstrates the expected behavior:
1. Detect main cert is linked to old chain (E6)
2. Unlink from old chain
3. Install new chain certificate (E7)
4. Link to new chain

All tests pass: 24 passed, 1 skipped

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt; ([`85a6447`](https://github.com/slauger/netscaler-certbot-hook/commit/85a6447bb028aa5a045504fe3ded55fa5bd3fac9))

### Unknown

* Merge pull request #13 from slauger/feature/mock-nitro-api

test: Add integration tests with Mock NITRO API for Issue #12 ([`aacfa8c`](https://github.com/slauger/netscaler-certbot-hook/commit/aacfa8cadf5d2d977725d7c4a25197a3f34f3dcc))

## v2.0.0 (2025-11-25)

### Breaking

* feat!: implement 31-char limit for chain names with hash suffix

Chain certificate names are now limited to 31 characters (NetScaler limit)
and use hash suffixes for uniqueness when names exceed this limit.

Changes:
- Names &gt; 31 chars: truncated to 24 chars + hyphen + 6-char SHA256 hash
- Names &lt;= 31 chars: preserved as-is
- Hash ensures uniqueness (e.g., GoDaddy G2 vs G3 have different hashes)
- Apostrophes are removed completely instead of replaced

Examples:
- &#34;R11&#34; → &#34;R11&#34; (unchanged)
- &#34;ZeroSSL RSA Domain Secure Site CA&#34; → &#34;ZeroSSL RSA Domain Secur-f38a3d&#34;
- &#34;Go Daddy Secure Certificate Authority - G2&#34; → &#34;Go Daddy Secure Certific-68a0d1&#34;
- &#34;Go Daddy Secure Certificate Authority - G3&#34; → &#34;Go Daddy Secure Certific-499691&#34;

BREAKING CHANGE: Chain certificate auto-detection now uses the certificate&#39;s
Common Name (CN) instead of the hardcoded &#34;letsencrypt&#34; default. Existing
deployments must either:
1. Explicitly specify --chain letsencrypt to maintain old behavior
2. Delete/rename the old &#34;letsencrypt&#34; chain certificate on NetScaler
Otherwise, certificate installation will fail because NetScaler only allows
one instance of each CA certificate. ([`3c408ef`](https://github.com/slauger/netscaler-certbot-hook/commit/3c408efd5f18085dbd75053b61dc86ac0e413f37))

### Chore

* chore(release): 2.0.0 ([`04a9c90`](https://github.com/slauger/netscaler-certbot-hook/commit/04a9c90ffc50021752ab57e3a1254960880b81d9))

### Feature

* feat: add noDomainCheck flag and auto-detect chain certificate name

This commit adds two major improvements to handle chain certificate updates:

1. **New --no-domain-check flag**: Adds explicit control over the NITRO API&#39;s
   noDomainCheck parameter. This is required when updating chain certificates
   because they are registered to different domains (CA domains) than the
   end-entity certificate. The flag can be used for:
   - Chain certificate updates (required)
   - Multi-domain/SAN certificates
   - Certificates bound to multiple virtual servers
   - Any scenario triggering &#34;Certificate is registered to a different domain&#34; error

2. **Auto-detect chain certificate name**: The chain certificate name is now
   automatically detected from the Common Name (CN) in the certificate, instead
   of using a hardcoded &#34;letsencrypt&#34; default. This automatically adapts to
   Let&#39;s Encrypt issuer changes (e.g., R10, R11, E5, E6, E7, E8). Users can
   still override with --chain if needed.

Changes:
- Added --no-domain-check CLI parameter
- Added get_certificate_cn() function to extract CN from certificates
- Modified nitro_install_cert() to accept no_domain_check parameter
- Auto-detect chain name from certificate CN in get_config()
- Updated README.md with comprehensive documentation
- Updated process_chain_certificate() to use config[&#39;no_domain_check&#39;]
- Updated install_or_update_certificate() to use config[&#39;no_domain_check&#39;]

Fixes #10 ([`7fb9c3d`](https://github.com/slauger/netscaler-certbot-hook/commit/7fb9c3d0101ccf4849fae52117949e8cc571f78c))

### Fix

* fix: install package in editable mode for GitHub Actions tests

This ensures the netscaler_certbot_hook module can be imported in CI/CD. ([`2c1603c`](https://github.com/slauger/netscaler-certbot-hook/commit/2c1603c02664c3596896b9c0090b839579a0d44e))

### Test

* test: add comprehensive tests for certificate CN extraction

This commit adds extensive test coverage for the certificate CN extraction
and sanitization functionality:

1. **Unit tests** (tests/test_certificate_cn.py):
   - Test simple alphanumeric CNs (Let&#39;s Encrypt R10, E5, etc.)
   - Test CNs with spaces (preserved for readability)
   - Test CNs with special characters (sanitized to hyphens)
   - Test valid special characters (underscore, hyphen, space)
   - Test NetScaler compatibility validation
   - Test error handling (file not found, invalid certificate)
   - Test real-world CA naming patterns

2. **CA certificate test script** (test_ca_certificates.py):
   - Downloads real intermediate certificates from multiple CAs
   - Tests Let&#39;s Encrypt (R10, R11, E5, E6)
   - Tests ZeroSSL/Sectigo RSA intermediate
   - Tests GoDaddy G2 intermediate
   - Validates sanitized names are NetScaler-compatible
   - Handles both PEM and DER certificate formats

3. **Sanitization rules** (updated in cli.py):
   - Conservative whitelist: alphanumeric, underscore, hyphen, space
   - Explicitly excludes: # : . @ = and other special chars
   - Apostrophes are removed completely (not replaced)
   - Must start with alphanumeric or underscore
   - Preserves spaces for readability (shorter names)

4. **GitHub Actions workflow** (.github/workflows/tests.yml):
   - Runs tests on Python 3.8-3.12
   - Executes unit tests and CA certificate tests
   - Verifies module import

All tests pass successfully! ([`579a30f`](https://github.com/slauger/netscaler-certbot-hook/commit/579a30fc7dc53aa472b8e18cad264f421463ba1a))

### Unknown

* Merge pull request #11 from slauger/fix/10-chain-update-domain-check

feat: add noDomainCheck flag and auto-detect chain certificate name ([`920a6f1`](https://github.com/slauger/netscaler-certbot-hook/commit/920a6f1507b0643792a8912ba860dd4c2106a591))

## v1.0.3 (2025-11-11)

### Chore

* chore(release): 1.0.3 ([`db8f61e`](https://github.com/slauger/netscaler-certbot-hook/commit/db8f61e97ccd2c16728bfc7768f4471945a66e16))

### Fix

* fix(docs): optimize architecture diagram - convert to JPG

- Convert PNG to JPG for better compression (1.6MB → 243KB)
- 85% quality maintains visual clarity
- Faster loading on PyPI and GitHub ([`eb53179`](https://github.com/slauger/netscaler-certbot-hook/commit/eb53179bec6f9201d4881d5e007b99636f18442d))

## v1.0.2 (2025-11-11)

### Chore

* chore(release): 1.0.2 ([`4a2466f`](https://github.com/slauger/netscaler-certbot-hook/commit/4a2466f36c327675684e0c129ec4e1024cf226bc))

### Fix

* fix(docs): update architecture diagram for better clarity

- Replace architecture.png with improved horizontal layout
- Use absolute GitHub URL for PyPI compatibility
- Wider format for better readability on all platforms
- Professional design showing the complete workflow ([`f422e44`](https://github.com/slauger/netscaler-certbot-hook/commit/f422e44b088d4ae490c3b06f8093c0dc99e4f3fc))

## v1.0.1 (2025-11-11)

### Chore

* chore(release): 1.0.1 ([`f58002a`](https://github.com/slauger/netscaler-certbot-hook/commit/f58002a4becc67e369c13bef89b69db0a70141c7))

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
