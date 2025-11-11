#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""NetScaler Certbot Hook - Automated SSL Certificate Management for Citrix NetScaler ADC.

This package provides automated installation and renewal of SSL certificates
(e.g., Let's Encrypt) on Citrix NetScaler ADC appliances using the NITRO API.

Main Components:
    - NitroClient: NITRO API client for NetScaler communication
    - CLI: Command-line interface for certificate management

Example:
    >>> from netscaler_certbot_hook import NitroClient
    >>> client = NitroClient('https://192.168.1.1', 'nsroot', 'password')
    >>> client.set_verify(True)

Author: Simon Lauger <simon@lauger.de>
License: MIT
"""

from .nitro import NitroClient

__version__ = "1.0.3"
__author__ = "Simon Lauger"
__email__ = "simon@lauger.de"
__license__ = "MIT"

__all__ = ["NitroClient"]
