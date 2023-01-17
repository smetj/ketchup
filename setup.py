#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py

import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

PROJECT = "ketchup"
VERSION = "0.1.2"

install_requires = ["arrow==1.2.2", "rich==12.6.0", "slack-sdk==3.19.5", "click==8.1.3"]

dependency_links = []

try:
    with open("README.md", "rt") as f:
        long_description = f.read()
except IOError:
    long_description = ""


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["-v", "tests/"]
        self.test_suite = True

    def run_tests(self):
        import pytest

        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setup(
    name=PROJECT,
    version=VERSION,
    description="A CLI to keep track of unhandled Slack questions.",
    long_description=long_description,
    author="Jelle Smet",
    author_email="development@smetj.net",
    url="https://github.com/smetj/ketchup",
    download_url="https://github.com/smetj/ketchup",
    dependency_links=dependency_links,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    extras_require={
        "test": ["pytest", "flake8", "black"],
    },
    platforms=["Linux"],
    test_suite="tests.tests",
    cmdclass={"test": PyTest},
    scripts=[],
    provides=[],
    install_requires=install_requires,
    namespace_packages=[],
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "ketchup = ketchup:main"
        ]
    },
)
