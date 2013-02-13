#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, dirnames, filenames in os.walk('cello'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))

    return packages

required_modules = ['cssselect', 'lxml']

setup(
    name='cello',
    version='0.0.5',
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
