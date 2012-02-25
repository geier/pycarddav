#!/usr/bin/env python

from distutils.core import setup

setup(name='pyCardDAV',
      version = '0.4',
      description = 'A CardDAV based address book tool',
      author = 'Christian Geier',
      author_email = 'pycarddav@lostpackets.de',
      url = 'http://pycarddav.lostpackets.de',
      license = 'beerware, see COPYING',
      py_modules=['pycard'],
      scripts=['pycardsyncer', 'pc_query'],
      data_files=[('config', ['pycard.conf.sample'])],
      )
