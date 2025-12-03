"""State management for Mock NITRO API.

This module maintains an in-memory state of certificates, links, and other
NetScaler configuration objects for testing purposes.
"""

from typing import Dict, Any, Optional
from copy import deepcopy

# In-memory certificate storage
_certificates: Dict[str, Dict[str, Any]] = {}

# User database for authentication
USERS = {
    "nsroot": "nsroot",
    "testuser": "testpass123"
}


def reset_state() -> None:
    """Reset all state to empty (useful for test cleanup)."""
    global _certificates
    _certificates = {}


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
