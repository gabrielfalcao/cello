#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

if sys.version_info[:2] < (2, 6):
    sys.stderr.write("\033[1;31m")
    sys.stderr.write("Cello is not supported by python versions < 2.6\n")
    sys.stderr.write("\033[0m")
    raise SystemExit(1)

from setuptools import setup
from cello import version


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, dirnames, filenames in os.walk('cello'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))

    return packages

required_modules = ['cssselect', 'lxml', 'couleur==0.5.0']


setup(
    name='cello',
    version=version,
    description='A beautiful instrument for scraping',
    author=u'Gabriel Falcao',
    author_email='gabriel@yipit.com',
    url='http://yipit.github.com/cello',
    packages=get_packages(),
    install_requires=required_modules,
    package_data={
        'cello': ['*.md'],
    },
)
