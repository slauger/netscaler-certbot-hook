#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""NetScaler Certbot Hook - Automated SSL Certificate Management for Citrix NetScaler ADC.

This script automates the installation and renewal of SSL certificates (e.g., Let's Encrypt)
on Citrix NetScaler ADC appliances using the NITRO API. It handles certificate uploads,
installations, updates, and chain certificate linking.

The script is designed to work seamlessly with Certbot's DNS-01 challenge for fully
automated certificate renewal workflows.

Usage:
    python3 netscaler-certbot-hook.py --name <cert-name> [options]

Environment Variables:
    NS_URL: NetScaler management URL (required, e.g., https://192.168.1.1)
    NS_LOGIN: NetScaler admin username (default: nsroot)
    NS_PASSWORD: NetScaler admin password (default: nsroot)
    NS_VERIFY_SSL: Verify SSL certificate (default: true)

Examples:
    # Basic usage with Let's Encrypt default paths
    export NS_URL=https://192.168.10.10
    export NS_LOGIN=nsroot
    export NS_PASSWORD=secretpassword
    python3 netscaler-certbot-hook.py --name mydomain.com

    # Custom certificate paths
    python3 netscaler-certbot-hook.py --name mydomain.com \\
        --cert /path/to/cert.pem \\
        --privkey /path/to/privkey.pem \\
        --chain-cert /path/to/chain.pem

Author: Simon Lauger <simon@lauger.de>
License: MIT
Version: 1.0.0
Copyright: Copyright 2020, IT Consulting Simon Lauger
"""

__author__ = "Simon Lauger"
__email__ = "simon@lauger.de"
__version__ = "1.0.0"
__license__ = "MIT"
__copyright__ = "Copyright 2020, IT Consulting Simon Lauger"
__maintainer__ = "Simon Lauger"

import argparse
import os
import sys
import json
import time
import base64
import urllib.parse
import logging
from typing import Dict, Optional, Union, Any
from OpenSSL import crypto
from . import nitro

# Initialize logger
logger = logging.getLogger(__name__)

add_args = {
  '--name': {
    'metavar': '<string>',
    'help': 'object name of the ssl certificate',
    'type': str,
    'default': None,
    'required': True,
  },
  '--chain': {
    'metavar': '<string>',
    'help': 'object name of the ssl chain certificate',
    'type': str,
    'default': 'letsencrypt',
    'required': False,
  },
  '--cert': {
    'metavar': '<file>',
    'help': 'path to the ssl certificate (default: /etc/letsencrypt/live/name/cert.pem)',
    'type': str,
    'default': None,
    'required': False,
  },
  '--privkey': {
    'metavar': '<file>',
    'help': 'path to the ssl private key (default: /etc/letsencrypt/live/name/privkey.pem)',
    'type': str,
    'default': None,
    'required': False,
  },
  '--chain-cert': {
    'metavar': '<file>',
    'help': 'path to the ssl chain certificate (default: /etc/letsencrypt/live/name/chain.pem)',
    'type': str,
    'default': None,
    'required': False,
  },
  '--verbose': {
    'help': 'enable verbose output (DEBUG level)',
    'action': 'store_true',
    'default': False,
    'required': False,
  },
  '--quiet': {
    'help': 'suppress all output except errors (ERROR level)',
    'action': 'store_true',
    'default': False,
    'required': False,
  },
  '--update-chain': {
    'help': 'allow updating chain certificate if serial differs',
    'action': 'store_true',
    'default': False,
    'required': False,
  },
}

def add_argument(parser: argparse.ArgumentParser, arg: str, params: Dict[str, Any]) -> None:
    """Add an argument to the argument parser.

    Args:
        parser (argparse.ArgumentParser): The argument parser instance.
        arg (str): The argument name (e.g., '--name').
        params (dict): Argument parameters (metavar, type, help, default, required, action).
    """
    # Build kwargs dynamically based on params
    kwargs = {'help': params['help']}

    if 'metavar' in params:
        kwargs['metavar'] = params['metavar']
    if 'type' in params:
        kwargs['type'] = params['type']
    if 'default' in params:
        kwargs['default'] = params['default']
    if 'required' in params:
        kwargs['required'] = params['required']
    if 'action' in params:
        kwargs['action'] = params['action']

    parser.add_argument(arg, **kwargs)


def nitro_check_cert(nitro_client: nitro.NitroClient, objectname: str) -> Union[Dict[str, Any], bool]:
    """Check if a certificate exists on the NetScaler.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        objectname (str): Name of the certificate object to check.

    Returns:
        dict or bool: Certificate information dict if found, False otherwise.

    Example:
        >>> cert = nitro_check_cert(client, 'mydomain.com')
        >>> if cert:
        ...     print(cert['sslcertkey'][0]['serial'])
    """
    try:
        result = nitro_client.request(
            'get',
            endpoint='config',
            objecttype='sslcertkey',
            objectname=objectname,
        )
    except Exception as e:
        # Certificate not found or other API error
        return False
    return result


def nitro_upload(nitro_client: nitro.NitroClient, source_file: str, target_filename: str) -> Dict[str, Any]:
    """Upload a file to the NetScaler /nsconfig/ssl directory.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        source_file (str): Local path to the file to upload.
        target_filename (str): Target filename on the NetScaler.

    Returns:
        dict: API response from the upload operation.

    Raises:
        Exception: If the upload fails or file cannot be read.
    """
    return nitro_client.request(
        'post',
        endpoint='config',
        objecttype='systemfile',
        data=json.dumps({
            'systemfile': {
                'filename': target_filename,
                'filecontent': base64.b64encode(open(source_file, 'rb').read()).decode('utf-8'),
                'filelocation': '/nsconfig/ssl',
                'fileencoding': 'BASE64',
            }
        }),
    )


def nitro_delete(nitro_client: nitro.NitroClient, filename: str) -> Dict[str, Any]:
    """Delete a file from the NetScaler /nsconfig/ssl directory.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        filename (str): Name of the file to delete.

    Returns:
        dict: API response from the delete operation.
    """
    return nitro_client.request(
        'delete',
        endpoint='config',
        objecttype='systemfile',
        objectname=filename,
        params={'args': 'filelocation:%%2Fnsconfig%%2Fssl'},
    )


def nitro_install_cert(nitro_client: nitro.NitroClient, name: str, cert: Optional[str] = None,
                       key: Optional[str] = None, update: bool = False) -> Dict[str, Any]:
    """Install or update a certificate on the NetScaler.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        name (str): Certificate object name.
        cert (str, optional): Certificate filename on NetScaler. Defaults to None.
        key (str, optional): Private key filename on NetScaler. Defaults to None.
        update (bool, optional): True to update existing cert, False to create new. Defaults to False.

    Returns:
        dict: API response from the installation/update operation.

    Example:
        >>> nitro_install_cert(client, 'mydomain.com', cert='mydomain.crt', key='mydomain.key')
    """
    data = {
        'sslcertkey': {
            'certkey': name,
        }
    }

    if update:
        params = {'action': 'update'}
    else:
        params = {}

    if cert:
        data['sslcertkey']['cert'] = "/nsconfig/ssl/{}".format(cert)
    if key:
        data['sslcertkey']['key'] = "/nsconfig/ssl/{}".format(key)

    return nitro_client.request(
        'post',
        endpoint='config',
        objecttype='sslcertkey',
        data=json.dumps(data),
        params=params,
    )


def nitro_link_cert(nitro_client: nitro.NitroClient, name: str, chain: str) -> Dict[str, Any]:
    """Link a certificate to its chain certificate.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        name (str): Certificate object name.
        chain (str): Chain certificate object name to link to.

    Returns:
        dict: API response from the link operation.

    Raises:
        Exception: If the link operation fails (e.g., link already exists).
    """
    return nitro_client.request(
        'post',
        endpoint='config',
        objecttype='sslcertkey',
        data=json.dumps({
            'sslcertkey': {
                'certkey': name,
                'linkcertkeyname': chain,
            }
        }),
        params={'action': 'link'},
    )


def nitro_save_config(nitro_client: nitro.NitroClient) -> Dict[str, Any]:
    """Save the NetScaler running configuration to disk.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.

    Returns:
        dict: API response from the save operation.

    Note:
        This makes configuration changes persistent across reboots.
    """
    return nitro_client.request(
        'post',
        endpoint='config',
        objecttype='nsconfig',
        data=json.dumps({
            'nsconfig': {}
        }),
        params={'action': 'save'},
    )

def parse_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - name: Certificate object name (required)
            - chain: Chain certificate name (default: 'letsencrypt')
            - cert: Path to certificate file (optional)
            - privkey: Path to private key file (optional)
            - chain_cert: Path to chain certificate file (optional)

    Example:
        >>> args = parse_arguments()
        >>> print(args.name)
        'mydomain.com'
    """
    parser = argparse.ArgumentParser(
        description='Install and manage SSL certificates on Citrix NetScaler ADC.'
    )

    for key in add_args:
        add_argument(parser, key, add_args[key])

    return parser.parse_args()


def get_config(args: argparse.Namespace) -> Dict[str, Union[str, bool, int]]:
    """Build and validate configuration from environment variables and arguments.

    Reads configuration from environment variables (NS_URL, NS_LOGIN, NS_PASSWORD, NS_VERIFY_SSL)
    and combines them with command line arguments. Validates all required settings and ensures
    certificate files exist.

    Args:
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        dict: Configuration dictionary containing:
            - username (str): NetScaler admin username
            - password (str): NetScaler admin password
            - verify_ssl (bool): Whether to verify SSL certificates
            - url (str): NetScaler management URL
            - cert_file (str): Path to certificate file
            - privkey_file (str): Path to private key file
            - chain_file (str): Path to chain certificate file
            - cert_name (str): Certificate object name
            - chain_name (str): Chain certificate object name
            - update_chain (bool): Whether to allow chain certificate updates
            - timestamp (int): Unix timestamp for file naming

    Raises:
        ValueError: If required environment variables are missing or invalid.
        FileNotFoundError: If any certificate file does not exist.

    Example:
        >>> config = get_config(args)
        >>> print(config['url'])
        'https://192.168.10.10'
    """
    config = {
        'username': os.getenv('NS_LOGIN', 'nsroot'),
        'password': os.getenv('NS_PASSWORD', 'nsroot'),
        'verify_ssl': os.getenv('NS_VERIFY_SSL', 'true').lower() in ('true', '1', 'yes'),
        'url': os.getenv('NS_URL', None),
        'cert_file': args.cert or '/etc/letsencrypt/live/{}/cert.pem'.format(args.name),
        'privkey_file': args.privkey or '/etc/letsencrypt/live/{}/privkey.pem'.format(args.name),
        'chain_file': args.chain_cert or '/etc/letsencrypt/live/{}/chain.pem'.format(args.name),
        'cert_name': args.name,
        'chain_name': args.chain,
        'update_chain': args.update_chain,
        'timestamp': int(time.time()),
    }

    # Validate required configuration
    if config['url'] is None:
        raise ValueError('required environment variable NS_URL not set')

    if not config['url'].startswith('http://') and not config['url'].startswith('https://'):
        raise ValueError('NS_URL must start with http:// or https://')

    if not config['username']:
        raise ValueError('NS_LOGIN environment variable must not be empty')

    if not config['password']:
        raise ValueError('NS_PASSWORD environment variable must not be empty')

    # Validate certificate files exist
    for file_key, file_path in [('cert_file', config['cert_file']),
                                 ('privkey_file', config['privkey_file']),
                                 ('chain_file', config['chain_file'])]:
        if not os.path.isfile(file_path):
            raise FileNotFoundError('{} not found: {}'.format(file_key, file_path))

    return config

def get_certificate_serial(cert_file: str) -> int:
    """Extract serial number from a PEM certificate file.

    Args:
        cert_file (str): Path to the PEM-encoded certificate file.

    Returns:
        int: Certificate serial number.

    Raises:
        FileNotFoundError: If certificate file does not exist.
        IOError: If certificate file cannot be read.
        ValueError: If certificate format is invalid.

    Example:
        >>> serial = get_certificate_serial('/etc/letsencrypt/live/mydomain.com/cert.pem')
        >>> print(serial)
        409596789458967997345847308430335698529007
    """
    if not os.path.isfile(cert_file):
        raise FileNotFoundError("Certificate file not found: {}".format(cert_file))

    try:
        with open(cert_file, 'r') as f:
            cert_data = f.read()
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        return cert.get_serial_number()
    except (IOError, OSError) as e:
        raise IOError("Failed to read certificate file {}: {}".format(cert_file, str(e)))
    except crypto.Error as e:
        raise ValueError("Invalid certificate format in {}: {}".format(cert_file, str(e)))


def process_chain_certificate(nitro_client: nitro.NitroClient, config: Dict[str, Union[str, bool, int]]) -> None:
    """Process and install chain certificate if needed.

    Checks if the chain certificate exists on the NetScaler. If it exists and matches
    the local serial number, no action is taken. If it doesn't exist, uploads and
    installs the chain certificate. If the serial differs and --update-chain flag is set,
    updates the chain certificate.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        config (dict): Configuration dictionary from get_config().

    Raises:
        Exception: If installed chain certificate serial doesn't match local certificate
                  and --update-chain flag is NOT set.

    Note:
        By default, this function does NOT update existing chain certificates if the
        serial number differs. Use --update-chain flag to enable chain certificate updates.
        This is disabled by default for security reasons to prevent unexpected chain changes.
    """
    chain_serial = get_certificate_serial(config['chain_file'])
    check_chain = nitro_check_cert(nitro_client, config['chain_name'])

    if check_chain:
        installed_serial = int(check_chain['sslcertkey'][0]['serial'], 16)
        logger.info("chain certificate %s found with serial %s", config['chain_name'], installed_serial)

        if installed_serial == chain_serial:
            logger.info("installed chain certificate matches our serial - nothing to do")
        else:
            if config['update_chain']:
                logger.warning("chain certificate serial differs - updating due to --update-chain flag")
                logger.info("old serial: %s, new serial: %s", installed_serial, chain_serial)
                chain_filename = '{}-{}.crt'.format(config['chain_name'], config['timestamp'])
                logger.info("uploading chain certificate as %s", chain_filename)
                nitro_upload(nitro_client, config['chain_file'], chain_filename)
                logger.info("updating chain certificate with serial %s", chain_serial)
                nitro_install_cert(nitro_client, config['chain_name'], cert=chain_filename, update=True)
            else:
                raise Exception('serial of installed chain certificate does not match our serial (use --update-chain to allow updates)')
    else:
        logger.info("chain certificate %s not found", config['chain_name'])
        chain_filename = '{}-{}.crt'.format(config['chain_name'], config['timestamp'])
        logger.info("uploading chain certificate as %s", chain_filename)
        nitro_upload(nitro_client, config['chain_file'], chain_filename)
        logger.info("installing chain certificate with serial %s", chain_serial)
        nitro_install_cert(nitro_client, config['chain_name'], cert=chain_filename)


def install_or_update_certificate(nitro_client: nitro.NitroClient, config: Dict[str, Union[str, bool, int]],
                                   cert_serial: int, update: bool = False) -> None:
    """Install or update a certificate on the NetScaler.

    Uploads the certificate and private key files, installs or updates the certificate
    object, links it to the chain certificate, and saves the configuration.

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        config (dict): Configuration dictionary from get_config().
        cert_serial (int): Serial number of the certificate being installed.
        update (bool, optional): True to update existing certificate, False to create new.
                                Defaults to False.

    Note:
        This function automatically handles linking to the chain certificate and
        saves the NetScaler configuration after installation.
    """
    cert_filename = '{}-{}.crt'.format(config['cert_name'], config['timestamp'])
    key_filename = '{}-{}.key'.format(config['cert_name'], config['timestamp'])

    logger.info("uploading certificate as %s", cert_filename)
    nitro_upload(nitro_client, config['cert_file'], cert_filename)
    logger.info("uploading private key as %s", key_filename)
    nitro_upload(nitro_client, config['privkey_file'], key_filename)

    if update:
        logger.info("update certificate %s", config['cert_name'])
    else:
        logger.info("installing certificate with serial %s", cert_serial)

    nitro_install_cert(nitro_client, config['cert_name'], cert=cert_filename, key=key_filename, update=update)

    logger.info("link certificate %s to chain certificate %s", config['cert_name'], config['chain_name'])
    try:
        nitro_link_cert(nitro_client, config['cert_name'], config['chain_name'])
    except Exception as e:
        # Link already exists, which is fine
        logger.info("certificate link was already present - nothing to do")

    logger.info("saving configuration")
    nitro_save_config(nitro_client)


def process_certificate(nitro_client: nitro.NitroClient, config: Dict[str, Union[str, bool, int]]) -> None:
    """Process and install or update the main certificate.

    Checks if the certificate exists on the NetScaler. Compares serial numbers and
    decides whether to skip (if matching), update (if different), or install (if not found).

    Args:
        nitro_client (NitroClient): Configured NITRO API client instance.
        config (dict): Configuration dictionary from get_config().

    Behavior:
        - If certificate exists and serial matches: No action taken
        - If certificate exists and serial differs: Updates the certificate
        - If certificate doesn't exist: Installs new certificate
    """
    cert_serial = get_certificate_serial(config['cert_file'])
    check_cert = nitro_check_cert(nitro_client, config['cert_name'])

    if check_cert:
        installed_serial = int(check_cert['sslcertkey'][0]['serial'], 16)
        logger.info("certificate %s found with serial %s", config['cert_name'], installed_serial)

        if installed_serial == cert_serial:
            logger.info("installed certificate matches our serial - nothing to do")
        else:
            install_or_update_certificate(nitro_client, config, cert_serial, update=True)
    else:
        logger.info("certificate %s not found", config['cert_name'])
        install_or_update_certificate(nitro_client, config, cert_serial, update=False)

def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags.

    Args:
        verbose (bool): Enable DEBUG level logging if True.
        quiet (bool): Suppress all but ERROR level logging if True.

    Note:
        If both verbose and quiet are True, verbose takes precedence.
    """
    # Determine log level
    if verbose:
        log_level = logging.DEBUG
    elif quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    # Configure logging format
    log_format = '%(message)s'
    if verbose:
        # More detailed format for debug mode
        log_format = '%(levelname)s: %(message)s'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main() -> None:
    """Main entry point for certificate installation and management.

    This function orchestrates the entire certificate installation workflow:
    1. Parses command line arguments
    2. Configures logging based on verbosity flags
    3. Loads and validates configuration
    4. Connects to NetScaler via NITRO API
    5. Processes chain certificate (install if needed)
    6. Processes main certificate (install or update as needed)

    The function handles the complete lifecycle including validation, upload,
    installation, linking, and configuration persistence.

    Raises:
        ValueError: If configuration is invalid or missing required values.
        FileNotFoundError: If certificate files are not found.
        Exception: If any NITRO API operation fails.

    Exit Codes:
        0: Success - Certificate installed/updated or already up-to-date
        1: Error - Configuration, validation, or API error occurred

    Example:
        This function is called when the script is run directly:
        $ python3 netscaler-certbot-hook.py --name mydomain.com
        $ python3 netscaler-certbot-hook.py --name mydomain.com --verbose
        $ python3 netscaler-certbot-hook.py --name mydomain.com --quiet
    """
    args = parse_arguments()

    # Setup logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    logger.debug("Starting NetScaler Certbot Hook")
    logger.debug("Certificate name: %s", args.name)

    config = get_config(args)

    # Initialize NITRO client
    logger.debug("Connecting to NetScaler at %s", config['url'])
    nitro_client = nitro.NitroClient(config['url'], config['username'], config['password'])
    nitro_client.set_verify(config['verify_ssl'])
    nitro_client.on_error('continue')

    # Process chain certificate
    process_chain_certificate(nitro_client, config)

    # Process main certificate
    process_certificate(nitro_client, config)

    logger.debug("NetScaler Certbot Hook completed successfully")


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        # Use basic print for error before logging is configured, or logger if available
        if logger.hasHandlers():
            logger.error("Error: %s", e)
        else:
            print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
