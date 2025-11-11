#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Entry point for netscaler-certbot-hook when run as a module.

This allows the package to be run with:
    python -m netscaler_certbot_hook --name example.com
"""

from .cli import main

if __name__ == '__main__':
    main()
