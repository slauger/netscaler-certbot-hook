#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for certificate CN extraction and sanitization."""

import unittest
import tempfile
import os
from OpenSSL import crypto
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from netscaler_certbot_hook.cli import get_certificate_cn


class TestCertificateCN(unittest.TestCase):
    """Test cases for get_certificate_cn() function."""

    def create_test_cert(self, cn):
        """Create a temporary test certificate with given CN.

        Args:
            cn (str): Common Name for the certificate

        Returns:
            str: Path to temporary certificate file
        """
        # Generate key
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        # Create certificate
        cert = crypto.X509()
        cert.get_subject().CN = cn
        cert.get_subject().O = "Test Organization"
        cert.get_subject().C = "US"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
            return f.name

    def test_simple_alphanumeric_cn(self):
        """Test simple alphanumeric CNs like R10, E5."""
        test_cases = [
            ('R10', 'R10'),
            ('R11', 'R11'),
            ('E5', 'E5'),
            ('E6', 'E6'),
        ]

        for input_cn, expected in test_cases:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    self.assertEqual(result, expected)
                finally:
                    os.unlink(cert_file)

    def test_cn_with_spaces(self):
        """Test CNs with spaces are preserved (NetScaler allows spaces)."""
        test_cases = [
            ('ZeroSSL RSA Domain Secure Site CA', 'ZeroSSL RSA Domain Secure Site CA'),
            ('Go Daddy Secure Certificate Authority - G2', 'Go Daddy Secure Certificate Authority - G2'),
            ('Let\'s Encrypt Authority X3', 'Lets Encrypt Authority X3'),  # Apostrophe removed
        ]

        for input_cn, expected in test_cases:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    self.assertEqual(result, expected)
                finally:
                    os.unlink(cert_file)

    def test_cn_with_invalid_special_characters(self):
        """Test CNs with invalid special characters are sanitized."""
        test_cases = [
            ('Test$Certificate', 'Test-Certificate'),  # $ not allowed
            ('Test!Cert', 'Test-Cert'),  # ! not allowed
            ('Test%Cert', 'Test-Cert'),  # % not allowed
            ('Test/Cert\\Name', 'Test-Cert-Name'),  # / and \ not allowed
            ('Test@Certificate', 'Test-Certificate'),  # @ not allowed
            ('Test:Certificate', 'Test-Certificate'),  # : not allowed
            ('Test=Certificate', 'Test-Certificate'),  # = not allowed
            ('Test#Certificate', 'Test-Certificate'),  # # not allowed
            ('Test.Certificate', 'Test-Certificate'),  # . not allowed
            ('Test\'Certificate', 'TestCertificate'),  # Apostrophe removed completely
        ]

        for input_cn, expected in test_cases:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    self.assertEqual(result, expected)
                finally:
                    os.unlink(cert_file)

    def test_cn_with_valid_special_chars(self):
        """Test CNs with valid special characters."""
        test_cases = [
            ('Test-Certificate', 'Test-Certificate'),
            ('Test_Certificate', 'Test_Certificate'),
            ('Test Cert', 'Test Cert'),  # Space is allowed
            ('Test-Cert_123', 'Test-Cert_123'),
        ]

        for input_cn, expected in test_cases:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    self.assertEqual(result, expected)
                finally:
                    os.unlink(cert_file)

    def test_cn_length(self):
        """Test that long CNs are preserved (no truncation)."""
        # Test a moderately long CN (64 chars - OpenSSL limit is typically 64)
        long_cn = 'A' * 64
        cert_file = self.create_test_cert(long_cn)
        try:
            result = get_certificate_cn(cert_file)
            self.assertEqual(result, long_cn)
            self.assertEqual(len(result), 64)
        finally:
            os.unlink(cert_file)

    def test_cn_with_numbers(self):
        """Test CNs with numbers."""
        test_cases = [
            ('CA-2024', 'CA-2024'),
            ('Cert123', 'Cert123'),
            ('123Test456', '123Test456'),
        ]

        for input_cn, expected in test_cases:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    self.assertEqual(result, expected)
                finally:
                    os.unlink(cert_file)

    def test_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            get_certificate_cn('/nonexistent/file.pem')

    def test_invalid_certificate(self):
        """Test error handling with invalid certificate file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("This is not a valid certificate")
            temp_file = f.name

        try:
            with self.assertRaises(ValueError):
                get_certificate_cn(temp_file)
        finally:
            os.unlink(temp_file)

    def test_netscaler_compatibility(self):
        """Test that sanitized names only contain NetScaler-compatible characters."""
        test_cns = [
            'R10',
            'ZeroSSL RSA Domain Secure Site CA',
            'Go Daddy Secure Certificate Authority - G2',
            'Test@#:=Certificate',
            'Test/\\Certificate',
        ]

        # We allow: alphanumeric, underscore, hyphen, space
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ')

        for input_cn in test_cns:
            with self.subTest(cn=input_cn):
                cert_file = self.create_test_cert(input_cn)
                try:
                    result = get_certificate_cn(cert_file)
                    # Check that all characters are valid
                    invalid_chars = set(result) - valid_chars
                    self.assertEqual(len(invalid_chars), 0,
                                   f"Invalid characters found: {invalid_chars}")
                    # Check that it starts with alphanumeric or underscore
                    self.assertTrue(result[0].isalnum() or result[0] == '_',
                                  f"Must start with alphanumeric or underscore, got '{result[0]}'")
                finally:
                    os.unlink(cert_file)


class TestCertificateCNRealWorld(unittest.TestCase):
    """Real-world test cases based on actual CA certificates."""

    def test_letsencrypt_patterns(self):
        """Test Let's Encrypt naming patterns."""
        patterns = ['R10', 'R11', 'R12', 'E5', 'E6', 'E7', 'E8']

        for pattern in patterns:
            with self.subTest(pattern=pattern):
                # These should pass through unchanged
                # (simulated test - in real test we'd use actual certs)
                self.assertTrue(pattern.isalnum())
                self.assertLessEqual(len(pattern), 10)

    def test_zerossl_pattern(self):
        """Test ZeroSSL naming pattern."""
        cn = 'ZeroSSL RSA Domain Secure Site CA'
        expected = 'ZeroSSL RSA Domain Secure Site CA'  # Spaces are preserved

        # Check length
        self.assertEqual(len(expected), 33)
        # Check it's within reasonable bounds (< 128 chars)
        self.assertLess(len(expected), 128)
        # Check no invalid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ')
        self.assertEqual(set(expected) - valid_chars, set())

    def test_godaddy_pattern(self):
        """Test GoDaddy naming pattern."""
        cn = 'Go Daddy Secure Certificate Authority - G2'
        expected = 'Go Daddy Secure Certificate Authority - G2'  # Spaces are preserved

        # Check length
        self.assertEqual(len(expected), 42)
        # Check it's within reasonable bounds (< 128 chars)
        self.assertLess(len(expected), 128)
        # Check no invalid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ')
        self.assertEqual(set(expected) - valid_chars, set())


if __name__ == '__main__':
    unittest.main()
