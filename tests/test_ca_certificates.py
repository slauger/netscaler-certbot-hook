#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test script to download and test CA certificate CN extraction.

This script downloads various CA intermediate certificates from different
Certificate Authorities and tests the CN extraction and sanitization logic
to ensure NetScaler-compatible object names are generated.
"""

import sys
import os
import tempfile
import requests
from OpenSSL import crypto

# Add src directory to path to import our module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from netscaler_certbot_hook.cli import get_certificate_cn


# CA Certificates to test
CA_CERTIFICATES = {
    'Let\'s Encrypt R10': 'https://letsencrypt.org/certs/2024/r10.pem',
    'Let\'s Encrypt R11': 'https://letsencrypt.org/certs/2024/r11.pem',
    'Let\'s Encrypt E5': 'https://letsencrypt.org/certs/2024/e5.pem',
    'Let\'s Encrypt E6': 'https://letsencrypt.org/certs/2024/e6.pem',
    'ZeroSSL RSA': 'http://zerossl.crt.sectigo.com/ZeroSSLRSADomainSecureSiteCA.crt',
    'GoDaddy G2': 'https://certs.godaddy.com/repository/gdig2.crt.pem',
    # Add more CAs as needed
}


def download_certificate(url):
    """Download certificate from URL.

    Args:
        url (str): URL to certificate file

    Returns:
        str: Path to downloaded certificate file

    Raises:
        Exception: If download fails
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Create temporary file
        # Handle both PEM (text) and DER (binary) formats
        content = response.content

        # Try to decode as text (PEM)
        try:
            content_text = content.decode('utf-8')
            # If it's PEM format, it should contain BEGIN CERTIFICATE
            if 'BEGIN CERTIFICATE' in content_text:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                    f.write(content_text)
                    return f.name
        except UnicodeDecodeError:
            pass

        # If not PEM, assume DER and convert to PEM
        cert = crypto.load_certificate(crypto.FILETYPE_ASN1, content)
        pem_data = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')

        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(pem_data)
            return f.name

    except Exception as e:
        raise Exception(f"Failed to download {url}: {e}")


def get_raw_cn(cert_file):
    """Get raw CN without sanitization.

    Args:
        cert_file (str): Path to certificate file

    Returns:
        str: Raw Common Name from certificate
    """
    with open(cert_file, 'r') as f:
        cert_data = f.read()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
    subject = cert.get_subject()
    return subject.CN


def validate_netscaler_name(name):
    """Validate if name is NetScaler-compatible.

    NetScaler object names must:
    - Begin with ASCII alphanumeric or underscore (_)
    - Contain only: alphanumeric, underscore, hash (#), period (.), space,
      colon (:), at (@), equals (=), hyphen (-)
    - Have minimum length = 1

    Args:
        name (str): Object name to validate

    Returns:
        tuple: (is_valid, warnings)
    """
    warnings = []
    is_valid = True

    # Check minimum length
    if len(name) < 1:
        warnings.append("Name must have at least 1 character")
        is_valid = False
        return is_valid, warnings

    # Check first character (must be alphanumeric or underscore)
    if not (name[0].isalnum() or name[0] == '_'):
        warnings.append(f"Must start with alphanumeric or underscore, got '{name[0]}'")
        is_valid = False

    # Check allowed characters (conservative whitelist)
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ')
    invalid_chars = [c for c in name if c not in allowed_chars]
    if invalid_chars:
        warnings.append(f"Invalid chars: {set(invalid_chars)}")
        is_valid = False

    # Check maximum length (NetScaler limit for certificate names is 31 chars)
    if len(name) > 31:
        warnings.append(f"Name too long ({len(name)} chars, max 31)")
        is_valid = False

    return is_valid, warnings


def main():
    """Main test function."""
    print("=" * 80)
    print("CA Certificate CN Extraction Test")
    print("=" * 80)
    print()

    results = []

    for ca_name, url in CA_CERTIFICATES.items():
        print(f"Testing: {ca_name}")
        print(f"URL: {url}")

        try:
            # Download certificate
            cert_file = download_certificate(url)

            # Get raw CN
            raw_cn = get_raw_cn(cert_file)
            print(f"  Raw CN: '{raw_cn}'")

            # Get sanitized CN using our function
            sanitized_cn = get_certificate_cn(cert_file)
            print(f"  Sanitized: '{sanitized_cn}'")

            # Validate
            is_valid, warnings = validate_netscaler_name(sanitized_cn)
            status = "✓ OK" if is_valid else "✗ FAIL"

            if warnings:
                print(f"  Warnings: {', '.join(warnings)}")

            print(f"  Status: {status}")

            results.append({
                'ca': ca_name,
                'raw_cn': raw_cn,
                'sanitized': sanitized_cn,
                'length': len(sanitized_cn),
                'valid': is_valid,
                'warnings': warnings
            })

            # Cleanup
            os.unlink(cert_file)

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                'ca': ca_name,
                'raw_cn': 'ERROR',
                'sanitized': 'ERROR',
                'length': 0,
                'valid': False,
                'warnings': [str(e)]
            })

        print()

    # Print summary table
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"{'CA':<25} {'Raw CN':<35} {'Sanitized':<20} {'Len':<5} {'Status':<10}")
    print("-" * 80)

    for result in results:
        status = "✓" if result['valid'] else "✗"
        raw_cn_truncated = result['raw_cn'][:33] + '...' if len(result['raw_cn']) > 35 else result['raw_cn']
        sanitized_truncated = result['sanitized'][:18] + '...' if len(result['sanitized']) > 20 else result['sanitized']

        print(f"{result['ca']:<25} {raw_cn_truncated:<35} {sanitized_truncated:<20} {result['length']:<5} {status:<10}")

        if result['warnings']:
            for warning in result['warnings']:
                print(f"  ⚠ {warning}")

    print()
    print("=" * 80)

    # Check if all passed
    all_valid = all(r['valid'] for r in results)
    if all_valid:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed - review sanitization logic")
        return 1


if __name__ == '__main__':
    sys.exit(main())
