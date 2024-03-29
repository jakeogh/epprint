# -*- coding: utf-8 -*-


from setuptools import find_packages
from setuptools import setup

import fastentrypoints

dependencies = [
    "eprint @ git+https://git@github.com/jakeogh/eprint",
]

config = {
    "version": "0.1",
    "name": "epprint",
    "url": "https://github.com/jakeogh/epprint",
    "license": "ISC",
    "author": "Justin Keogh",
    "author_email": "github.com@v6y.net",
    "description": "print() alias that writes to sys.stderr prepended by stack metadata",
    "long_description": __doc__,
    "packages": find_packages(exclude=["tests"]),
    "package_data": {"epprint": ["py.typed"]},
    "include_package_data": True,
    "zip_safe": False,
    "platforms": "any",
    "install_requires": dependencies,
}

setup(**config)
