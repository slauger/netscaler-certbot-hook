"""Flask-based Mock NITRO API Server.

This server simulates the NetScaler NITRO API for testing purposes.
It implements the most important endpoints for certificate management.
"""

from flask import Flask, request, jsonify
from functools import wraps
from typing import Dict, Any, Tuple
import logging

from . import state

app = Flask(__name__)
app.config['TESTING'] = True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def error_response(error_code: int, message: str, status: int = 400) -> Tuple[Dict[str, Any], int]:
    """Create a NITRO-style error response.

    Args:
        error_code: NITRO error code
        message: Error message
        status: HTTP status code

    Returns:
        Tuple of (response dict, status code)
    """
    return jsonify({
        "errorcode": error_code,
        "message": message,
        "severity": "ERROR"
    }), status


def success_response(data: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """Create a NITRO-style success response.

    Args:
        data: Optional response data

    Returns:
        Tuple of (response dict, status code)
    """
    if data:
        return jsonify(data), 200
    else:
        return jsonify({
            "errorcode": 0,
            "message": "Done",
            "severity": "NONE"
        }), 200


def check_nitro_auth(f):
    """Decorator for NITRO API authentication.

    Checks X-NITRO-USER and X-NITRO-PASS headers against the user database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = request.headers.get('X-NITRO-USER')
        password = request.headers.get('X-NITRO-PASS')

        # Check if credentials provided
        if not username or not password:
            logger.warning("Authentication attempt without credentials")
            return error_response(
                -1,
                "Username and password not specified",
                401
            )

        # Validate credentials
        if username not in state.USERS or state.USERS[username] != password:
            logger.warning(f"Failed authentication attempt for user: {username}")
            return error_response(
                354,
                "Invalid username or password",
                401
            )

        logger.debug(f"Successful authentication for user: {username}")
        return f(*args, **kwargs)

    return decorated_function


@app.route('/nitro/v1/config/nsversion', methods=['GET'])
@check_nitro_auth
def get_version():
    """Get NetScaler version information."""
    logger.info("GET /nitro/v1/config/nsversion")
    return jsonify({
        "nsversion": [{
            "version": "NS14.1: Build 56.74 (Mock)",
            "installedversion": "14.1-56.74",
            "mode": "1"
        }]
    })


@app.route('/nitro/v1/config/sslcertkey', methods=['GET'])
@check_nitro_auth
def list_certificates():
    """List all SSL certificates."""
    logger.info("GET /nitro/v1/config/sslcertkey")
    certs = state.list_certificates()
    return jsonify({
        "sslcertkey": list(certs.values())
    })


@app.route('/nitro/v1/config/sslcertkey/<certkey>', methods=['GET'])
@check_nitro_auth
def get_certificate(certkey: str):
    """Get a specific SSL certificate.

    Args:
        certkey: Certificate name
    """
    logger.info(f"GET /nitro/v1/config/sslcertkey/{certkey}")

    cert = state.get_certificate(certkey)
    if not cert:
        logger.warning(f"Certificate not found: {certkey}")
        return error_response(
            258,
            "No such resource",
            404
        )

    return jsonify({
        "sslcertkey": [cert]
    })


@app.route('/nitro/v1/config/sslcertkey', methods=['POST'])
@check_nitro_auth
def manage_certificate():
    """Manage SSL certificates (add, update, link, unlink).

    The action is determined by the 'action' query parameter:
    - No action: Add new certificate
    - action=update: Update existing certificate
    - action=link: Link certificate to chain
    - action=unlink: Unlink certificate from chain
    """
    action = request.args.get('action')
    data = request.get_json()

    if not data or 'sslcertkey' not in data:
        return error_response(
            1094,
            "Invalid argument [sslcertkey]"
        )

    cert_data = data['sslcertkey']
    certkey = cert_data.get('certkey')

    if not certkey:
        return error_response(
            1094,
            "Invalid argument [certkey]"
        )

    logger.info(f"POST /nitro/v1/config/sslcertkey action={action} certkey={certkey}")

    if action == 'link':
        return link_certificate(cert_data)
    elif action == 'unlink':
        return unlink_certificate(cert_data)
    elif action == 'update':
        return update_certificate(cert_data)
    else:
        return add_certificate(cert_data)


def add_certificate(cert_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Add a new certificate.

    Args:
        cert_data: Certificate data from request

    Returns:
        Tuple of (response dict, status code)
    """
    certkey = cert_data['certkey']

    try:
        state.add_certificate(cert_data)
        # Get the stored certificate to check if serial was extracted
        stored_cert = state.get_certificate(certkey)
        serial_info = f"with serial {stored_cert.get('serial')}" if stored_cert.get('serial') else "without serial"
        logger.info(f"Certificate added: {certkey} {serial_info}")
        return success_response()
    except ValueError as e:
        if "already exists" in str(e):
            logger.warning(f"Certificate already exists: {certkey}")
            return error_response(
                273,
                f"Resource already exists [{certkey}]",
                409
            )
        raise


def update_certificate(cert_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Update an existing certificate.

    Args:
        cert_data: Certificate data from request

    Returns:
        Tuple of (response dict, status code)
    """
    certkey = cert_data['certkey']

    try:
        # Extract fields to update (cert, key, nodomaincheck, etc.)
        updates = {}
        if 'cert' in cert_data:
            updates['cert'] = cert_data['cert']
        if 'key' in cert_data:
            updates['key'] = cert_data['key']
        if 'nodomaincheck' in cert_data:
            updates['nodomaincheck'] = cert_data['nodomaincheck']

        state.update_certificate(certkey, updates)
        logger.info(f"Certificate updated: {certkey}")
        return success_response()
    except ValueError as e:
        if "not found" in str(e):
            logger.warning(f"Certificate not found for update: {certkey}")
            return error_response(
                258,
                "No such resource",
                404
            )
        raise


def link_certificate(cert_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Link a certificate to a chain certificate.

    Args:
        cert_data: Certificate data with 'linkcertkeyname' field

    Returns:
        Tuple of (response dict, status code)
    """
    certkey = cert_data['certkey']
    chain_name = cert_data.get('linkcertkeyname')

    if not chain_name:
        return error_response(
            1094,
            "Invalid argument [linkcertkeyname]"
        )

    try:
        state.link_certificate(certkey, chain_name)
        logger.info(f"Certificate linked: {certkey} -> {chain_name}")
        return success_response()
    except ValueError as e:
        error_msg = str(e)

        if "not found" in error_msg:
            logger.warning(f"Certificate or chain not found: {error_msg}")
            return error_response(
                258,
                "No such resource",
                404
            )
        elif "already linked" in error_msg:
            # THIS IS THE KEY ERROR FOR ISSUE #12!
            logger.warning(f"Certificate already linked to different chain: {error_msg}")
            return error_response(
                1540,
                error_msg,
                409
            )
        raise


def unlink_certificate(cert_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Unlink a certificate from a chain certificate.

    Args:
        cert_data: Certificate data with 'linkcertkeyname' field

    Returns:
        Tuple of (response dict, status code)
    """
    certkey = cert_data['certkey']
    chain_name = cert_data.get('linkcertkeyname')

    if not chain_name:
        return error_response(
            1094,
            "Invalid argument [linkcertkeyname]"
        )

    try:
        state.unlink_certificate(certkey, chain_name)
        logger.info(f"Certificate unlinked: {certkey} -X- {chain_name}")
        return success_response()
    except ValueError as e:
        error_msg = str(e)

        if "not found" in error_msg:
            logger.warning(f"Certificate not found for unlink: {error_msg}")
            return error_response(
                258,
                "No such resource",
                404
            )
        elif "not linked" in error_msg:
            logger.warning(f"Certificate not linked: {error_msg}")
            return error_response(
                1541,
                error_msg,
                400
            )
        raise


@app.route('/nitro/v1/config/nsconfig', methods=['POST'])
@check_nitro_auth
def save_config():
    """Save NetScaler configuration.

    This is a no-op in the mock but returns success to simulate the real API.
    """
    action = request.args.get('action')

    if action == 'save':
        logger.info("POST /nitro/v1/config/nsconfig?action=save")
        return success_response()

    return error_response(
        1094,
        "Invalid action"
    )


@app.route('/nitro/v1/config/systemfile', methods=['POST'])
@check_nitro_auth
def upload_file():
    """Upload a file to NetScaler.

    Stores the base64-encoded file content so certificate serials can be extracted.
    """
    data = request.get_json()

    if not data or 'systemfile' not in data:
        return error_response(
            1094,
            "Invalid argument [systemfile]"
        )

    system_file = data['systemfile']
    filename = system_file.get('filename')
    filecontent = system_file.get('filecontent')

    if not filename:
        return error_response(
            1094,
            "Invalid argument [filename]"
        )

    # Store the file content for later serial extraction
    if filecontent:
        state.store_uploaded_file(filename, filecontent)
        logger.info(f"POST /nitro/v1/config/systemfile - uploaded: {filename} ({len(filecontent)} bytes)")
    else:
        logger.info(f"POST /nitro/v1/config/systemfile - uploading: {filename} (no content)")

    return success_response()


if __name__ == '__main__':
    # Run the mock server on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
