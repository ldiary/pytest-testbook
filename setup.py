#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import codecs
from setuptools import setup


directory_name = os.path.dirname(__file__)
with codecs.open(os.path.join(directory_name, 'pytest_testbook', '__init__.py'), encoding='utf-8') as fd:
    VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(fd.read()).group(1)

def read(fname):
    file_path = os.path.join(directory_name, fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-testbook',
    version=VERSION,
    author='Ernesto D. Luzon Jr.',
    author_email='raise_a_bug_in_myrepo@github.com',
    maintainer='Ernesto D. Luzon Jr.',
    maintainer_email='please_raise_a_bug_in_myrepo@github.com',
    license='MIT',
    url='https://github.com/ldiary/pytest-testbook',
    description='A plugin to run tests written in Jupyter notebook',
    long_description=read('README.rst'),
    packages=["pytest_testbook"],
    install_requires=['pytest == 2.9.1',
                      'jupyter'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'testbook = pytest_testbook.plugin',
        ],
    },
)
