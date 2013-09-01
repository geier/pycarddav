#!/usr/bin/env python2

import os
import string
import subprocess
import sys
import warnings

#from distutils.core import setup
from setuptools import setup

MAJOR = 0
MINOR = 5
PATCH = 1

RELEASE = True

VERSION = "{0}.{1}.{2}".format(MAJOR, MINOR, PATCH)

if not RELEASE:
    try:
        try:
            pipe = subprocess.Popen(["git", "describe", "--dirty", "--tags"],
                                    stdout=subprocess.PIPE)
        except EnvironmentError:
            warnings.warn("WARNING: git not installed or failed to run")

        revision = pipe.communicate()[0].strip().lstrip('v')
        if pipe.returncode != 0:
            warnings.warn("WARNING: couldn't get git revision")

        if revision != VERSION:
            revision = revision.lstrip(string.digits + '.')
            VERSION += '.dev' + revision
    except:
        VERSION += '.dev'
        warnings.warn("WARNING: git not installed or failed to run")


def write_version():
    """writes the pycarddav/version.py file"""
    template = """\
__version__ = '{0}'
"""
    filename = os.path.join(
        os.path.dirname(__file__), 'pycarddav', 'version.py')
    with open(filename, 'w') as versionfile:
        versionfile.write(template.format(VERSION))
        print("wrote pycarddav/version.py with version={0}".format(VERSION))

write_version()


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
    version=VERSION,
    description='A CardDAV based address book tool',
    long_description=open('README.rst').read(),
    author='Christian Geier',
    author_email='pycarddav@lostpackets.de',
    url='http://lostpackets.de/pycarddav/',
    license='Expat/MIT',
    packages=['pycarddav'],
    scripts=['bin/pycardsyncer', 'bin/pc_query', 'bin/pycard-import'],
    requires=requirements,
    install_requires=requirements,
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
