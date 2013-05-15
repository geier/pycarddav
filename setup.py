#!/usr/bin/env python

import sys
#from distutils.core import setup
from setuptools import setup

requirements = [
    'lxml',
    'vobject',
    'requests',
    'urwid',
    'pyxdg'
]
if sys.version_info[:2] in ((2, 6),):
    # there is no argparse in python2.6
    requirements.append('argparse')

setup(
    name='pyCardDAV',
    version='0.4.1',
    description='A CardDAV based address book tool',
    long_description=open('README.rst').read(),
    author='Christian Geier',
    author_email='pycarddav@lostpackets.de',
    url='http://lostpackets.de/pycarddav/',
    license='Expat/MIT',
    packages=['pycarddav'],
    scripts=['bin/pycardsyncer', 'bin/pc_query', 'bin/pycard-import'],
    requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console :: Curses",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Utilities",
        "Topic :: Communications :: Email :: Address Book"
    ],
)
