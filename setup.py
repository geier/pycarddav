#!/usr/bin/env python

from distutils.core import setup

setup(
      name='pyCardDAV',
      version = '0.4a',
      description = 'A CardDAV based address book tool',
      author = 'Christian Geier',
      author_email = 'pycarddav@lostpackets.de',
      url = 'http://pycarddav.lostpackets.de',
      license = 'Beerware',
      packages = ['pycarddav'],
      scripts=['bin/pycardsyncer', 'bin/pc_query'],
      classifiers=[
          "Development Status :: 3 - Alpha",
          "License :: Beerware",
          "Environment :: Console :: Curses",
          "Intended Audience :: End Users/Desktop",
          "Operating System :: POSIX",
          "Programming Language :: Python :: 2 :: Only",
          "Topic :: Utilities",
          "Topic :: Communications :: Email :: Address Book"
          ],
      )
