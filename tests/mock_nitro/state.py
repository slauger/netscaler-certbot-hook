"""State management for Mock NITRO API.

This module maintains an in-memory state of certificates, links, and other
NetScaler configuration objects for testing purposes.
"""

from typing import Dict, Any, Optional
from copy import deepcopy
import base64
from OpenSSL import crypto

# In-memory certificate storage
_certificates: Dict[str, Dict[str, Any]] = {}

# In-memory file storage (filename -> base64 content)
_uploaded_files: Dict[str, str] = {}

# User database for authentication
USERS = {
    "nsroot": "nsroot",
    "testuser": "testpass123"
}


def reset_state() -> None:
    """Reset all state to empty (useful for test cleanup)."""
    global _certificates, _uploaded_files
    _certificates = {}
    _uploaded_files = {}


def store_uploaded_file(filename: str, content_base64: str) -> None:
    """Store an uploaded file in memory.

    Args:
        filename: Name of the file
        content_base64: Base64-encoded file content
    """
    _uploaded_files[filename] = content_base64


def extract_serial_from_cert(cert_path: str) -> Optional[str]:
    """Extract serial number from an uploaded certificate file.

    Args:
        cert_path: Full path to certificate (e.g., '/nsconfig/ssl/example.com.crt')

    Returns:
        Hex serial number string (e.g., '0x123abc') or None if not found
    """
    # Extract just the filename from the path
    filename = cert_path.split('/')[-1]

    if filename not in _uploaded_files:
        return None

    try:
        # Decode base64 content
        cert_pem = base64.b64decode(_uploaded_files[filename])

        # Parse certificate
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem)

        # Get serial number and convert to hex string
        serial_int = cert.get_serial_number()
        serial_hex = hex(serial_int)

        return serial_hex
    except Exception:
        # If parsing fails, return None
        return None


def add_certificate(cert_data: Dict[str, Any]) -> None:
    """Add a certificate to the state.

    Args:
        cert_data: Certificate data dict with at least 'certkey' field

    Raises:
        ValueError: If certificate already exists
    """
    certkey = cert_data.get('certkey')
    if not certkey:
        raise ValueError("certkey is required")

    if certkey in _certificates:
        raise ValueError(f"Certificate {certkey} already exists")

    # If no serial provided, try to extract from uploaded certificate file
    if 'serial' not in cert_data and 'cert' in cert_data:
        serial = extract_serial_from_cert(cert_data['cert'])
        if serial:
            cert_data['serial'] = serial

    _certificates[certkey] = deepcopy(cert_data)


def get_certificate(certkey: str) -> Optional[Dict[str, Any]]:
    """Get certificate by name.

    Args:
        certkey: Certificate name

    Returns:
        Certificate data dict or None if not found
    """
    return deepcopy(_certificates.get(certkey))


def update_certificate(certkey: str, updates: Dict[str, Any]) -> None:
    """Update an existing certificate.

    Args:
        certkey: Certificate name
        updates: Fields to update

    Raises:
        ValueError: If certificate doesn't exist
    """
    if certkey not in _certificates:
        raise ValueError(f"Certificate {certkey} not found")

    # If cert file is being updated, extract new serial
    if 'cert' in updates and 'serial' not in updates:
        serial = extract_serial_from_cert(updates['cert'])
        if serial:
            updates['serial'] = serial

    _certificates[certkey].update(updates)


def link_certificate(certkey: str, chain_name: str) -> None:
    """Link a certificate to a chain certificate.

    Args:
        certkey: Certificate name to link
        chain_name: Chain certificate name

    Raises:
        ValueError: If certificate doesn't exist or is already linked to a different chain
    """
    if certkey not in _certificates:
        raise ValueError(f"Certificate {certkey} not found")

    if chain_name not in _certificates:
        raise ValueError(f"Chain certificate {chain_name} not found")

    cert = _certificates[certkey]
    current_link = cert.get('linkcertkeyname')

    # Check if already linked to a DIFFERENT chain
    if current_link and current_link != chain_name:
        raise ValueError(
            f"Certificate {certkey} is already linked to {current_link}. "
            f"Cannot link to {chain_name} without unlinking first."
        )

    # Same link - this is idempotent
    if current_link == chain_name:
        return

    # Set the link
    _certificates[certkey]['linkcertkeyname'] = chain_name


def unlink_certificate(certkey: str, chain_name: str) -> None:
    """Unlink a certificate from a chain certificate.

    Args:
        certkey: Certificate name to unlink
        chain_name: Chain certificate name

    Raises:
        ValueError: If certificate doesn't exist or is not linked to specified chain
    """
    if certkey not in _certificates:
        raise ValueError(f"Certificate {certkey} not found")

    cert = _certificates[certkey]
    current_link = cert.get('linkcertkeyname')

    if not current_link:
        raise ValueError(f"Certificate {certkey} is not linked to any chain")

    if current_link != chain_name:
        raise ValueError(
            f"Certificate {certkey} is linked to {current_link}, not {chain_name}"
        )

    # Remove the link
    del _certificates[certkey]['linkcertkeyname']


def list_certificates() -> Dict[str, Dict[str, Any]]:
    """Get all certificates.

    Returns:
        Dict of all certificates
    """
    return deepcopy(_certificates)
