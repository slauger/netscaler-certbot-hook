#!/usr/bin/env python3

"""nitro.py: Client for the Citrix NetScaler NITRO API."""

__author__ = "Simon Lauger"
__copyright__ = "Copyright 2020, IT Consulting Simon Lauger"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Simon Lauger"
__email__ = "simon@lauger.de"

import requests

class NitroClient():
  def __init__(self, url, username, password):
    self._url      = url
    self._headers = {
      'X-NITRO-USER': username,
      'X-NITRO-PASS': password,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    }
    self._verify = True
    
  def set_url(self, url):
    self._url = url

  def set_username(self, username):
    self._headers['X-NITRO-USER'] = username

  def set_password(self, password):
    self._headers['X-NITRO-PASS'] = password

  def set_verify(self, verify):
    self._verify = verify

  def on_error(self, action):
    self._headers['X-NITRO-ONERROR'] = action

  def request(self, method, endpoint, objecttype, objectname = None, params = None, data = None):
    url = self._url + '/nitro/v1/' + endpoint + '/' + objecttype

    if objectname != None:
      url += '/' + objectname

    if params != None:
      url += '?'

      if isinstance(params, dict):
        for key, value in params.items():
          url += key + "=" + value
      else:
        url += params

    method_callback = getattr(requests, method)

    self._result = method_callback(
      url,
      data=data,
      headers=self._headers,
      verify=self._verify,
    )

    try:
      result = self._result.json()
    except:
      result = self._result

    if 'severity' in result:
      if result['severity'] == 'ERROR':
        self._error = result
        raise Exception('{} {}: {} ({})'.format(result['severity'], result['errorcode'], result['message'], url))

    return result

  def get_stat(self, objecttype, objectname = None, params = None):
    return self.request(get, 'stat', objecttype, objectname, params)

  def get_config(self, objecttype, objectname = None, params = None):
    return self.request(get, 'config', objecttype, objectname, params)

  def post_stat(self, objecttype, objectname = None, params = None):
    return self.request(post, 'stat', objecttype, objectname, params)

  def post_config(self, objecttype, objectname = None, params = None):
    return self.request(post, 'config', objecttype, objectname, params)
  
  def put_stat(self, objecttype, objectname = None, params = None):
    return self.request(put, 'stat', objecttype, objectname, params)

  def put_config(self, objecttype, objectname = None, params = None):
    return self.request(put, 'config', objecttype, objectname, params)

  def delete_stat(self, objecttype, objectname = None, params = None):
    return self.request(delete, 'stat', objecttype, objectname, params)

  def delete_config(self, objecttype, objectname = None, params = None):
    return self.request(delete, 'config', objecttype, objectname, params)
