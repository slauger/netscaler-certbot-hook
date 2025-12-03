"""Mock NITRO API Server for Testing.

This module provides a lightweight Flask-based mock of the NetScaler NITRO API
for testing purposes. It simulates the most important certificate management
endpoints without requiring a real NetScaler appliance.

Usage:
    from tests.mock_nitro.server import app

    # Run in tests
    app.run(port=5000)
"""

__version__ = "0.1.0"
