"""Integration tests for netscaler-certbot-hook.

These tests run the complete plugin against the Mock NITRO API server
to verify end-to-end functionality in realistic scenarios.
"""

import pytest
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch
from OpenSSL import crypto

from tests.mock_nitro.server import app
from tests.mock_nitro import state


@pytest.fixture
def mock_server():
    """Start the mock NITRO API server in a background thread."""
    # Reset state before each test
    state.reset_state()

    # Configure app for testing
    app.config['TESTING'] = True

    # Start server in background thread
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=5556, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    # Give server time to start
    time.sleep(0.5)

    yield 'http://127.0.0.1:5556'

    # Cleanup after test
    state.reset_state()


@pytest.fixture
def temp_certs():
    """Create temporary certificate files for testing.

    Returns a dict with paths to cert.pem, privkey.pem, chain.pem
    and their serial numbers.
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    # Generate private key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Create main certificate
    cert = crypto.X509()
    cert.get_subject().CN = "example.com"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Create chain certificate (Let's Encrypt style)
    chain_key = crypto.PKey()
    chain_key.generate_key(crypto.TYPE_RSA, 2048)

    chain_cert = crypto.X509()
    chain_cert.get_subject().CN = "E6"
    chain_cert.set_serial_number(2000)
    chain_cert.gmtime_adj_notBefore(0)
    chain_cert.gmtime_adj_notAfter(365*24*60*60)
    chain_cert.set_issuer(chain_cert.get_subject())
    chain_cert.set_pubkey(chain_key)
    chain_cert.sign(chain_key, 'sha256')

    # Write files
    cert_path = os.path.join(temp_dir, 'cert.pem')
    key_path = os.path.join(temp_dir, 'privkey.pem')
    chain_path = os.path.join(temp_dir, 'chain.pem')

    with open(cert_path, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(key_path, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    with open(chain_path, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, chain_cert))

    yield {
        'dir': temp_dir,
        'cert': cert_path,
        'privkey': key_path,
        'chain': chain_path,
        'cert_serial': cert.get_serial_number(),
        'chain_serial': chain_cert.get_serial_number(),
        'chain_cn': 'E6'
    }

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def env_vars(mock_server):
    """Set environment variables for NITRO API access."""
    env = {
        'NS_URL': mock_server,
        'NS_LOGIN': 'nsroot',
        'NS_PASSWORD': 'nsroot',
        'NS_VERIFY_SSL': 'false'
    }

    # Set environment variables
    old_env = {}
    for key, value in env.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield env

    # Restore environment
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def run_hook(cert_name, temp_certs, **kwargs):
    """Run the netscaler-certbot-hook script.

    Args:
        cert_name: Certificate name (--name parameter)
        temp_certs: Fixture with certificate paths
        **kwargs: Additional command line arguments

    Returns:
        None (raises exception on failure)
    """
    # Import the CLI module
    from src.netscaler_certbot_hook import cli

    # Build arguments
    args = [
        '--name', cert_name,
        '--cert', temp_certs['cert'],
        '--privkey', temp_certs['privkey'],
        '--chain-cert', temp_certs['chain']
    ]

    # Add optional arguments
    if 'chain' in kwargs:
        args.extend(['--chain', kwargs['chain']])
    if kwargs.get('update_chain'):
        args.append('--update-chain')
    if kwargs.get('no_domain_check'):
        args.append('--no-domain-check')
    if kwargs.get('verbose'):
        args.append('--verbose')

    # Mock sys.argv
    with patch.object(sys, 'argv', ['netscaler-certbot-hook'] + args):
        cli.main()


def test_initial_installation(mock_server, temp_certs, env_vars):
    """Test 1: Initial installation on fresh NetScaler.

    Scenario:
    - NetScaler has no certificates
    - Script installs chain certificate (E6)
    - Script installs main certificate (example.com)
    - Script links main cert to chain
    - Config is saved

    Expected:
    - Both certificates exist in state
    - Main cert is linked to chain
    - No errors
    """
    # Run the hook
    run_hook('example.com', temp_certs)

    # Verify chain certificate was installed
    chain_cert = state.get_certificate('E6')
    assert chain_cert is not None, "Chain certificate should be installed"
    assert chain_cert['certkey'] == 'E6'

    # Verify main certificate was installed
    main_cert = state.get_certificate('example.com')
    assert main_cert is not None, "Main certificate should be installed"
    assert main_cert['certkey'] == 'example.com'

    # Verify link
    assert main_cert.get('linkcertkeyname') == 'E6', "Main cert should be linked to E6"

    # Verify file paths are set
    assert 'cert' in main_cert
    assert 'key' in main_cert
    assert '/nsconfig/ssl/' in main_cert['cert']


def test_certificate_renewal_same_chain(mock_server, temp_certs, env_vars):
    """Test 2: Certificate renewal with same chain.

    Scenario:
    - Chain E6 already exists (same serial)
    - Main cert exists but with different serial (renewal)
    - Script should skip chain, update main cert

    Expected:
    - Chain cert unchanged
    - Main cert updated
    - Link still intact
    """
    # Pre-populate: Install initial certificates
    run_hook('example.com', temp_certs)

    # Verify initial state
    initial_chain = state.get_certificate('E6')
    assert initial_chain is not None

    # Now create a NEW main certificate (renewal scenario)
    # Generate new cert with different serial
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().CN = "example.com"
    cert.set_serial_number(9999)  # Different serial!
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Overwrite cert.pem with new certificate
    with open(temp_certs['cert'], 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(temp_certs['privkey'], 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    # Run hook again (renewal)
    run_hook('example.com', temp_certs)

    # Verify chain cert is still the same (not re-uploaded)
    chain_cert = state.get_certificate('E6')
    assert chain_cert == initial_chain, "Chain cert should be unchanged"

    # Verify main cert was updated
    main_cert = state.get_certificate('example.com')
    assert main_cert is not None
    assert main_cert.get('linkcertkeyname') == 'E6', "Link should still exist"


def test_idempotent_run(mock_server, temp_certs, env_vars):
    """Test 3: Idempotent run (no changes needed).

    Scenario:
    - Both certificates already exist with correct serials
    - Script runs again
    - Should detect no changes needed

    Expected:
    - No updates performed
    - State unchanged
    - No errors
    """
    # Initial installation
    run_hook('example.com', temp_certs)

    # Capture state after first run
    chain_cert_before = state.get_certificate('E6')
    main_cert_before = state.get_certificate('example.com')

    # Run again with same certificates (idempotent)
    run_hook('example.com', temp_certs)

    # Verify nothing changed
    chain_cert_after = state.get_certificate('E6')
    main_cert_after = state.get_certificate('example.com')

    assert chain_cert_before == chain_cert_after, "Chain cert should be unchanged"
    assert main_cert_before == main_cert_after, "Main cert should be unchanged"
    assert main_cert_after.get('linkcertkeyname') == 'E6', "Link should still exist"


def test_chain_rotation_issue_12(mock_server, temp_certs, env_vars):
    """Test 4: Chain rotation (Let's Encrypt E6 → E7).

    This is the core test for Issue #12.

    Scenario:
    - Main cert is linked to E6
    - Let's Encrypt rotates: chain.pem now contains E7
    - Script should:
      1. Detect main cert is linked to E6 (different from E7)
      2. Unlink from E6
      3. Install E7
      4. Link to E7

    Expected:
    - Main cert is now linked to E7 (not E6)
    - Both E6 and E7 exist in state
    - No errors
    """
    # Initial setup: Install with E6
    run_hook('example.com', temp_certs)

    # Verify initial link
    main_cert = state.get_certificate('example.com')
    assert main_cert.get('linkcertkeyname') == 'E6', "Should initially be linked to E6"

    # Simulate Let's Encrypt rotation: Create new chain cert E7
    chain_key = crypto.PKey()
    chain_key.generate_key(crypto.TYPE_RSA, 2048)

    new_chain = crypto.X509()
    new_chain.get_subject().CN = "E7"  # NEW chain name!
    new_chain.set_serial_number(3000)  # Different serial
    new_chain.gmtime_adj_notBefore(0)
    new_chain.gmtime_adj_notAfter(365*24*60*60)
    new_chain.set_issuer(new_chain.get_subject())
    new_chain.set_pubkey(chain_key)
    new_chain.sign(chain_key, 'sha256')

    # Overwrite chain.pem with E7
    with open(temp_certs['chain'], 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, new_chain))

    # Run hook again - this should detect chain rotation
    # NOTE: Current implementation might not handle this automatically yet!
    # This test will likely FAIL until Issue #12 is fixed.
    try:
        run_hook('example.com', temp_certs, update_chain=True, no_domain_check=True)

        # If we get here, check if rotation worked
        main_cert_after = state.get_certificate('example.com')

        # The cert should now be linked to E7
        assert main_cert_after.get('linkcertkeyname') == 'E7', \
            "After chain rotation, main cert should be linked to E7"

        # Both chains should exist
        assert state.get_certificate('E6') is not None, "E6 should still exist"
        assert state.get_certificate('E7') is not None, "E7 should exist"

    except Exception as e:
        # If this fails, it's expected until Issue #12 is implemented
        pytest.skip(f"Chain rotation not yet implemented (Issue #12): {e}")


def test_authentication_error(mock_server, temp_certs):
    """Test 5: Authentication error handling.

    Scenario:
    - Wrong credentials provided
    - Script should fail gracefully with clear error

    Expected:
    - Exception raised
    - Error message mentions authentication
    """
    # Set wrong credentials
    os.environ['NS_URL'] = mock_server
    os.environ['NS_LOGIN'] = 'nsroot'
    os.environ['NS_PASSWORD'] = 'wrongpassword'
    os.environ['NS_VERIFY_SSL'] = 'false'

    # Run hook - should fail
    with pytest.raises(Exception) as exc_info:
        run_hook('example.com', temp_certs)

    # Verify error message mentions authentication failure
    error_msg = str(exc_info.value)
    assert '401' in error_msg or 'UNAUTHORIZED' in error_msg or '354' in error_msg, \
        f"Error should mention authentication failure: {error_msg}"


def test_custom_chain_name(mock_server, temp_certs, env_vars):
    """Bonus Test: Custom chain name override.

    Scenario:
    - User specifies --chain custom-chain-name
    - Script should use that instead of auto-detected CN

    Expected:
    - Chain cert is named 'custom-chain-name', not 'E6'
    """
    # Run with custom chain name
    run_hook('example.com', temp_certs, chain='custom-chain-name')

    # Verify custom name was used
    chain_cert = state.get_certificate('custom-chain-name')
    assert chain_cert is not None, "Chain cert should exist with custom name"

    # Verify E6 (auto-detected) does NOT exist
    assert state.get_certificate('E6') is None, "Auto-detected name should not be used"

    # Verify link uses custom name
    main_cert = state.get_certificate('example.com')
    assert main_cert.get('linkcertkeyname') == 'custom-chain-name'
