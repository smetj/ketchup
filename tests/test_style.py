#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_style.py
#

from pathlib import Path
from subprocess import run

import black


def test_flake8_conformance():
    """
    Test code passed flake8
    """
    ignore = [
        "E501",  # E501 line too long (163 > 79 characters)
        "W503",  # line break before binary operator"
        "W1203",  # Use lazy % formatting in logging functions (logging-fstring-interpolation)
        "R0902",  # Too many instance attributes (11/7) (too-many-instance-attributes)
        "W0102",  # Dangerous default value [] as argument (dangerous-default-value)
        "R0913",  # Too many arguments (7/5) (too-many-arguments)
        "R0903",  # Too few public methods
    ]
    result = run(
        ["flake8", "--ignore", ",".join(ignore), "ketchup/"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        assert False, result.stdout.decode()


def test_black():
    """
    Test whether code is formatted with black
    """

    for path in Path("ketchup").rglob("*.py"):
        assert not black.format_file_in_place(
            Path(path),
            fast=False,
            mode=black.FileMode(),
        )
