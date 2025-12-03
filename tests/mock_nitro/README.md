# Mock NITRO API Server

A lightweight Flask-based mock of the NetScaler NITRO API for testing purposes.

## Purpose

This mock server simulates the most important NetScaler NITRO API endpoints required for testing the `netscaler-certbot-hook` without needing access to a real NetScaler appliance.

## Features

- ✅ **NITRO Authentication** - Validates X-NITRO-USER/X-NITRO-PASS headers
- ✅ **Certificate Management** - Add, update, query SSL certificates
- ✅ **Chain Linking** - Link/unlink certificates to chain certificates
- ✅ **Issue #12 Simulation** - Correctly simulates the chain rotation problem
- ✅ **Realistic Error Messages** - Returns proper NITRO error codes and messages

## Installation

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

## Usage

### Running the Server Standalone

```bash
# Start the mock server on port 5000
python -m tests.mock_nitro.server

# Server will be available at http://127.0.0.1:5000
```

### Using in Tests

```python
import pytest
from tests.mock_nitro.server import app
from tests.mock_nitro import state

@pytest.fixture
def mock_server():
    """Start mock server for testing."""
    state.reset_state()
    app.config['TESTING'] = True

    # Use Flask test client
    with app.test_client() as client:
        yield client

def test_example(mock_server):
    response = mock_server.get(
        '/nitro/v1/config/nsversion',
        headers={
            'X-NITRO-USER': 'nsroot',
            'X-NITRO-PASS': 'nsroot'
        }
    )
    assert response.status_code == 200
```

## Authentication

**Default credentials:**
- Username: `nsroot`
- Password: `nsroot`

Additional users can be added in `state.py`:

```python
USERS = {
    "nsroot": "nsroot",
    "testuser": "testpass123"
}
```

## API Endpoints

### Version Information
```bash
GET /nitro/v1/config/nsversion
```

### Certificate Management

**Get all certificates:**
```bash
GET /nitro/v1/config/sslcertkey
```

**Get specific certificate:**
```bash
GET /nitro/v1/config/sslcertkey/<certkey>
```

**Add certificate:**
```bash
POST /nitro/v1/config/sslcertkey
Content-Type: application/json

{
  "sslcertkey": {
    "certkey": "example.com",
    "cert": "/nsconfig/ssl/example.com.crt",
    "key": "/nsconfig/ssl/example.com.key",
    "serial": "0x123456"
  }
}
```

**Update certificate:**
```bash
POST /nitro/v1/config/sslcertkey?action=update
Content-Type: application/json

{
  "sslcertkey": {
    "certkey": "example.com",
    "cert": "/nsconfig/ssl/example.com-new.crt",
    "key": "/nsconfig/ssl/example.com-new.key"
  }
}
```

**Link certificate to chain:**
```bash
POST /nitro/v1/config/sslcertkey?action=link
Content-Type: application/json

{
  "sslcertkey": {
    "certkey": "example.com",
    "linkcertkeyname": "E6"
  }
}
```

**Unlink certificate from chain:**
```bash
POST /nitro/v1/config/sslcertkey?action=unlink
Content-Type: application/json

{
  "sslcertkey": {
    "certkey": "example.com",
    "linkcertkeyname": "E6"
  }
}
```

### Configuration

**Save config (no-op):**
```bash
POST /nitro/v1/config/nsconfig?action=save
```

**Upload file (no-op):**
```bash
POST /nitro/v1/config/systemfile
```

## Testing Chain Rotation (Issue #12)

The mock server correctly simulates the behavior when trying to link a certificate to a new chain without unlinking from the old one:

```python
# Setup: Link cert to E6
state.add_certificate({'certkey': 'E6', ...})
state.add_certificate({'certkey': 'example.com', ...})
state.link_certificate('example.com', 'E6')

# Try to link to E7 without unlinking E6 first
# This will FAIL with error 1540
try:
    state.link_certificate('example.com', 'E7')
except ValueError as e:
    print(e)  # "Certificate example.com is already linked to E6..."

# Correct workflow:
state.unlink_certificate('example.com', 'E6')
state.add_certificate({'certkey': 'E7', ...})
state.link_certificate('example.com', 'E7')  # Now succeeds
```

## Error Codes

The mock returns the same error codes as a real NetScaler:

| Code | Message | Description |
|------|---------|-------------|
| -1 | Username and password not specified | Missing auth headers |
| 258 | No such resource | Certificate not found |
| 273 | Resource already exists | Certificate already exists |
| 354 | Invalid username or password | Wrong credentials |
| 1094 | Invalid argument | Missing required field |
| 1540 | Certificate already linked | Cannot link to multiple chains |
| 1541 | Certificate not linked | Cannot unlink non-linked cert |

## Limitations

This is a **test mock**, not a full NetScaler implementation:

- ❌ No persistence (in-memory state only)
- ❌ Only implements certificate-related endpoints
- ❌ No SSL/TLS validation
- ❌ No virtual server binding
- ❌ No statistics endpoints
- ❌ Simplified error handling

For production deployments, always use a real NetScaler appliance or VPX/CPX instance.

## Running Tests

```bash
# Run all tests including chain rotation tests
pytest tests/test_chain_rotation.py -v

# Run with coverage
pytest tests/test_chain_rotation.py --cov=tests.mock_nitro --cov-report=html
```

## Example: Testing Your Script

```bash
# Terminal 1: Start mock server
python -m tests.mock_nitro.server

# Terminal 2: Run your script against the mock
export NS_URL=http://127.0.0.1:5000
export NS_LOGIN=nsroot
export NS_PASSWORD=nsroot
export NS_VERIFY_SSL=false

python -m netscaler_certbot_hook --name example.com --verbose
```

## Contributing

When adding new features to the hook, update the mock to include any new NITRO API calls.

## License

Same license as the main project (MIT).
