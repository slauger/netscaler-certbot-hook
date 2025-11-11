#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""NITRO API Client - Python client library for Citrix NetScaler NITRO API.

This module provides a simple, lightweight client for interacting with the Citrix NetScaler
NITRO REST API. It handles authentication, request formatting, error handling, and response
parsing.

The NITRO API allows programmatic configuration and monitoring of NetScaler appliances.
This client implements the basic HTTP methods (GET, POST, PUT, DELETE) for working with
NetScaler configuration objects and statistics.

Features:
    - HTTP Basic Authentication via headers (X-NITRO-USER, X-NITRO-PASS)
    - SSL certificate verification control
    - Error handling with detailed exception messages
    - Support for all NITRO API endpoints (config, stat)
    - Request timeout handling (30 seconds default)
    - JSON request/response handling

Usage:
    from nitro import NitroClient

    # Initialize client
    client = NitroClient('https://192.168.1.1', 'nsroot', 'password')
    client.set_verify(True)  # Enable SSL verification

    # Make API request
    result = client.request('get', 'config', 'sslcertkey', 'my-cert')

    # Handle errors gracefully
    client.on_error('continue')

API Documentation:
    https://docs.citrix.com/en-us/citrix-adc/current-release/nitro-api.html

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

import requests
from typing import Dict, Optional, Union, Any


class NitroClient:
    """Client for interacting with Citrix NetScaler NITRO REST API.

    This class provides methods to perform CRUD operations on NetScaler configuration
    objects and retrieve statistics via the NITRO API.

    Attributes:
        _url (str): Base URL of the NetScaler appliance.
        _headers (dict): HTTP headers including authentication credentials.
        _verify (bool): Whether to verify SSL certificates.
        _result: Last HTTP response object.
        _error: Last error response if any.

    Example:
        >>> client = NitroClient('https://192.168.1.1', 'nsroot', 'password')
        >>> client.set_verify(False)
        >>> result = client.request('get', 'config', 'sslcertkey', 'my-cert')
    """

    def __init__(self, url: str, username: str, password: str) -> None:
        """Initialize the NITRO API client.

        Args:
            url (str): NetScaler management URL (e.g., 'https://192.168.1.1').
            username (str): Administrator username.
            password (str): Administrator password.
        """
        self._url: str = url
        self._headers: Dict[str, str] = {
            'X-NITRO-USER': username,
            'X-NITRO-PASS': password,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self._verify: bool = True
        self._result: Optional[requests.Response] = None
        self._error: Optional[Dict[str, Any]] = None

    def set_url(self, url: str) -> None:
        """Set the NetScaler management URL.

        Args:
            url (str): NetScaler management URL.
        """
        self._url = url

    def set_username(self, username: str) -> None:
        """Set the authentication username.

        Args:
            username (str): Administrator username.
        """
        self._headers['X-NITRO-USER'] = username

    def set_password(self, password: str) -> None:
        """Set the authentication password.

        Args:
            password (str): Administrator password.
        """
        self._headers['X-NITRO-PASS'] = password

    def set_verify(self, verify: bool) -> None:
        """Set SSL certificate verification.

        Args:
            verify (bool): True to verify SSL certificates, False to disable verification.
        """
        self._verify = verify

    def on_error(self, action: str) -> None:
        """Set error handling behavior for NITRO API.

        Args:
            action (str): Error handling action (e.g., 'continue', 'halt').
        """
        self._headers['X-NITRO-ONERROR'] = action

    def request(self, method: str, endpoint: str, objecttype: str,
                objectname: Optional[str] = None, params: Optional[Union[Dict[str, str], str]] = None,
                data: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """Make a request to the NITRO API.

        Args:
            method (str): HTTP method ('get', 'post', 'put', 'delete').
            endpoint (str): API endpoint ('config' or 'stat').
            objecttype (str): NetScaler object type (e.g., 'sslcertkey', 'lbvserver').
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.
            data (str, optional): JSON request body. Defaults to None.

        Returns:
            dict or Response: Parsed JSON response or raw response object.

        Raises:
            ValueError: If HTTP method is invalid.
            Exception: If request fails or API returns an error.

        Example:
            >>> client.request('get', 'config', 'sslcertkey', 'my-cert')
            >>> client.request('post', 'config', 'nsconfig', params={'action': 'save'})
        """
        # Build URL
        url = '{}/nitro/v1/{}/{}'.format(self._url, endpoint, objecttype)

        if objectname is not None:
            url += '/' + objectname

        if params is not None:
            url += '?'
            if isinstance(params, dict):
                url += '&'.join('{}={}'.format(k, v) for k, v in params.items())
            else:
                url += params

        # Validate HTTP method
        try:
            method_callback = getattr(requests, method)
        except AttributeError:
            raise ValueError("Invalid HTTP method: {}".format(method))

        # Execute request with error handling
        try:
            self._result = method_callback(
                url,
                data=data,
                headers=self._headers,
                verify=self._verify,
                timeout=30,
            )
            self._result.raise_for_status()
        except requests.exceptions.Timeout:
            raise Exception("Request timeout while connecting to NetScaler at {}".format(url))
        except requests.exceptions.ConnectionError as e:
            raise Exception("Failed to connect to NetScaler at {}: {}".format(url, str(e)))
        except requests.exceptions.HTTPError as e:
            raise Exception("HTTP error from NetScaler: {}".format(str(e)))
        except requests.exceptions.RequestException as e:
            raise Exception("Request failed: {}".format(str(e)))

        # Parse response
        try:
            result = self._result.json()
        except ValueError:
            # Not JSON response - return raw result
            result = self._result

        # Check for NITRO API errors
        if isinstance(result, dict) and 'severity' in result:
            if result['severity'] == 'ERROR':
                self._error = result
                raise Exception('{} {}: {} ({})'.format(
                    result['severity'],
                    result['errorcode'],
                    result['message'],
                    url
                ))

        return result

    def get_stat(self, objecttype: str, objectname: Optional[str] = None,
                 params: Optional[Union[Dict[str, str], str]] = None) -> Union[Dict[str, Any], requests.Response]:
        """Get statistics for a NetScaler object.

        Args:
            objecttype (str): Object type to query.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.

        Returns:
            dict: Statistics response from the API.
        """
        return self.request('get', 'stat', objecttype, objectname, params)

    def get_config(self, objecttype: str, objectname: Optional[str] = None,
                   params: Optional[Union[Dict[str, str], str]] = None) -> Union[Dict[str, Any], requests.Response]:
        """Get configuration for a NetScaler object.

        Args:
            objecttype (str): Object type to query.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.

        Returns:
            dict: Configuration response from the API.
        """
        return self.request('get', 'config', objecttype, objectname, params)

    def post_stat(self, objecttype: str, objectname: Optional[str] = None,
                  params: Optional[Union[Dict[str, str], str]] = None,
                  data: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """Create or update statistics object.

        Args:
            objecttype (str): Object type to create/update.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.
            data (str, optional): JSON request body. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('post', 'stat', objecttype, objectname, params, data)

    def post_config(self, objecttype: str, objectname: Optional[str] = None,
                    params: Optional[Union[Dict[str, str], str]] = None,
                    data: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """Create or update configuration object.

        Args:
            objecttype (str): Object type to create/update.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.
            data (str, optional): JSON request body. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('post', 'config', objecttype, objectname, params, data)

    def put_stat(self, objecttype: str, objectname: Optional[str] = None,
                 params: Optional[Union[Dict[str, str], str]] = None,
                 data: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """Update statistics object.

        Args:
            objecttype (str): Object type to update.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.
            data (str, optional): JSON request body. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('put', 'stat', objecttype, objectname, params, data)

    def put_config(self, objecttype: str, objectname: Optional[str] = None,
                   params: Optional[Union[Dict[str, str], str]] = None,
                   data: Optional[str] = None) -> Union[Dict[str, Any], requests.Response]:
        """Update configuration object.

        Args:
            objecttype (str): Object type to update.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.
            data (str, optional): JSON request body. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('put', 'config', objecttype, objectname, params, data)

    def delete_stat(self, objecttype: str, objectname: Optional[str] = None,
                    params: Optional[Union[Dict[str, str], str]] = None) -> Union[Dict[str, Any], requests.Response]:
        """Delete statistics object.

        Args:
            objecttype (str): Object type to delete.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('delete', 'stat', objecttype, objectname, params)

    def delete_config(self, objecttype: str, objectname: Optional[str] = None,
                      params: Optional[Union[Dict[str, str], str]] = None) -> Union[Dict[str, Any], requests.Response]:
        """Delete configuration object.

        Args:
            objecttype (str): Object type to delete.
            objectname (str, optional): Specific object name. Defaults to None.
            params (dict or str, optional): URL parameters. Defaults to None.

        Returns:
            dict: API response.
        """
        return self.request('delete', 'config', objecttype, objectname, params)
