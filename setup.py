#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup configuration."""

import platform

from ez_setup import use_setuptools
use_setuptools()
import setuptools

# Configure the required packages and scripts to install, depending on
# Python version and OS.
REQUIRED_PACKAGES = [
    'ez_setup==0.9'
    ]

py_version = platform.python_version()
if py_version < '2.6':
  REQUIRED_PACKAGES.append('simplejson')

_PYTRACTS_VERSION = '0.6.0'

setuptools.setup(
    name='pytracts',
    version=_PYTRACTS_VERSION,
    description='Library to define data contracts for JSON and build RESTful services with Webapp2',
    url='https://github.com/rmorlok/pytracts',
    author='Ryan Morlok',
    author_email='ryan.morlok@morlok.com.com',
    # Contained modules and scripts.
    packages=setuptools.find_packages(),
    install_requires=REQUIRED_PACKAGES,
    provides=[
        'pytracts (%s)' % (_PYTRACTS_VERSION,),
        ],
    # PyPI package information.
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    license='Apache 2.0',
    keywords='protocol json contract',
    )
