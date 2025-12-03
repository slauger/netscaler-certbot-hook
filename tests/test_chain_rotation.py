"""Tests for Issue #12 - Chain Certificate Rotation.

These tests verify the behavior when Let's Encrypt rotates intermediate
certificates (e.g., E6 → E7) and how the script should handle unlinking
the old chain and linking the new one.
"""

import pytest
import requests
import threading
import time
from tests.mock_nitro.server import app
from tests.mock_nitro import state


@pytest.fixture
def mock_server():
    """Start the mock NITRO API server in a background thread."""
    import socket

    # Reset state before each test
    state.reset_state()

    # Configure app for testing
    app.config['TESTING'] = True

    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()

    # Start server in background thread
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    # Give server time to start
    time.sleep(0.5)

    yield f'http://127.0.0.1:{port}'

    # Cleanup after test
    state.reset_state()


@pytest.fixture
def auth_headers():
    """NITRO authentication headers."""
    return {
        'X-NITRO-USER': 'nsroot',
        'X-NITRO-PASS': 'nsroot',
        'Content-Type': 'application/json'
    }


def test_chain_rotation_without_unlink_fails(mock_server, auth_headers):
    """Test that linking to a new chain without unlinking the old one fails.

    This is the core issue from #12:
    - Certificate is linked to E6
    - User tries to link to E7 (Let's Encrypt rotation)
    - Should fail with error indicating already linked
    """
    base_url = mock_server

    # Step 1: Add old chain certificate E6
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={
            'sslcertkey': {
                'certkey': 'E6',
                'cert': '/nsconfig/ssl/E6-123.crt',
                'serial': '0xabc123'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to add E6: {response.text}"

    # Step 2: Add main certificate
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={
            'sslcertkey': {
                'certkey': 'example.com',
                'cert': '/nsconfig/ssl/example.com-123.crt',
                'key': '/nsconfig/ssl/example.com-123.key',
                'serial': '0xdef456'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to add example.com: {response.text}"

    # Step 3: Link main cert to E6
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={
            'sslcertkey': {
                'certkey': 'example.com',
                'linkcertkeyname': 'E6'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to link to E6: {response.text}"

    # Verify link
    response = requests.get(
        f'{base_url}/nitro/v1/config/sslcertkey/example.com',
        headers=auth_headers
    )
    assert response.status_code == 200
    cert_data = response.json()
    assert cert_data['sslcertkey'][0]['linkcertkeyname'] == 'E6'

    # Step 4: Add new chain certificate E7 (Let's Encrypt rotation)
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={
            'sslcertkey': {
                'certkey': 'E7',
                'cert': '/nsconfig/ssl/E7-456.crt',
                'serial': '0xghi789'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to add E7: {response.text}"

    # Step 5: Try to link to E7 WITHOUT unlinking E6 first
    # THIS SHOULD FAIL - this is the bug from Issue #12
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={
            'sslcertkey': {
                'certkey': 'example.com',
                'linkcertkeyname': 'E7'
            }
        },
        headers=auth_headers
    )

    # Verify it fails
    assert response.status_code == 409, "Should fail with conflict"
    error_data = response.json()
    assert error_data['errorcode'] == 1540
    assert 'already linked' in error_data['message']
    assert 'E6' in error_data['message']


def test_chain_rotation_with_unlink_succeeds(mock_server, auth_headers):
    """Test that chain rotation works correctly when unlinking first.

    This demonstrates the correct workflow for Issue #12:
    1. Detect that main cert is linked to E6
    2. Unlink from E6
    3. Add new chain E7
    4. Link to E7
    """
    base_url = mock_server

    # Setup: Add E6 and example.com, link them
    requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={'sslcertkey': {'certkey': 'E6', 'cert': '/nsconfig/ssl/E6-123.crt', 'serial': '0xabc'}},
        headers=auth_headers
    )
    requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={'sslcertkey': {'certkey': 'example.com', 'cert': '/nsconfig/ssl/example.com.crt', 'key': '/nsconfig/ssl/example.com.key'}},
        headers=auth_headers
    )
    requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={'sslcertkey': {'certkey': 'example.com', 'linkcertkeyname': 'E6'}},
        headers=auth_headers
    )

    # Step 1: Check existing link
    response = requests.get(
        f'{base_url}/nitro/v1/config/sslcertkey/example.com',
        headers=auth_headers
    )
    old_link = response.json()['sslcertkey'][0].get('linkcertkeyname')
    assert old_link == 'E6', "Should be linked to E6 initially"

    # Step 2: Unlink from E6
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=unlink',
        json={
            'sslcertkey': {
                'certkey': 'example.com',
                'linkcertkeyname': 'E6'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to unlink: {response.text}"

    # Verify unlinked
    response = requests.get(
        f'{base_url}/nitro/v1/config/sslcertkey/example.com',
        headers=auth_headers
    )
    cert_data = response.json()['sslcertkey'][0]
    assert 'linkcertkeyname' not in cert_data or cert_data['linkcertkeyname'] is None

    # Step 3: Add new chain E7
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={
            'sslcertkey': {
                'certkey': 'E7',
                'cert': '/nsconfig/ssl/E7-456.crt',
                'serial': '0xdef'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to add E7: {response.text}"

    # Step 4: Link to E7
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={
            'sslcertkey': {
                'certkey': 'example.com',
                'linkcertkeyname': 'E7'
            }
        },
        headers=auth_headers
    )
    assert response.status_code == 200, f"Failed to link to E7: {response.text}"

    # Verify new link
    response = requests.get(
        f'{base_url}/nitro/v1/config/sslcertkey/example.com',
        headers=auth_headers
    )
    cert_data = response.json()['sslcertkey'][0]
    assert cert_data['linkcertkeyname'] == 'E7', "Should now be linked to E7"


def test_link_is_idempotent(mock_server, auth_headers):
    """Test that linking to the same chain multiple times is idempotent."""
    base_url = mock_server

    # Setup
    requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={'sslcertkey': {'certkey': 'E6', 'cert': '/nsconfig/ssl/E6.crt'}},
        headers=auth_headers
    )
    requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey',
        json={'sslcertkey': {'certkey': 'example.com', 'cert': '/nsconfig/ssl/example.com.crt', 'key': '/nsconfig/ssl/example.com.key'}},
        headers=auth_headers
    )

    # Link first time
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={'sslcertkey': {'certkey': 'example.com', 'linkcertkeyname': 'E6'}},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Link second time (same chain) - should succeed (idempotent)
    response = requests.post(
        f'{base_url}/nitro/v1/config/sslcertkey?action=link',
        json={'sslcertkey': {'certkey': 'example.com', 'linkcertkeyname': 'E6'}},
        headers=auth_headers
    )
    assert response.status_code == 200, "Linking to same chain should be idempotent"


def test_authentication_required(mock_server):
    """Test that all endpoints require authentication."""
    base_url = mock_server

    # No auth headers
    response = requests.get(f'{base_url}/nitro/v1/config/nsversion')
    assert response.status_code == 401
    assert response.json()['errorcode'] == -1

    # Wrong password
    response = requests.get(
        f'{base_url}/nitro/v1/config/nsversion',
        headers={
            'X-NITRO-USER': 'nsroot',
            'X-NITRO-PASS': 'wrongpass'
        }
    )
    assert response.status_code == 401
    assert response.json()['errorcode'] == 354
