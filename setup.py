#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setup script for netscaler-certbot-hook"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="netscaler-certbot-hook",
    version="0.0.1",
    author="Simon Lauger",
    author_email="simon@lauger.de",
    description="A Certbot Hook for Citrix NetScaler ADC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slauger/netscaler-certbot-hook",
    py_modules=["netscaler-certbot-hook", "nitro"],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    scripts=["netscaler-certbot-hook.py"],
)
