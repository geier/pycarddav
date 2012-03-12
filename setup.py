#!/usr/bin/env python

from distutils.core import setup
import pycarddav

setup(name='pyCardDAV',
      version = pycarddav.__version__,
      description = pycarddav.__version__,
      author = pycarddav.__version__,
      author_email = pycarddav.__author_email__,
      url = pycarddav.__homepage__,
      license = pycarddav.__license__,
      packages = ['pycarddav'],
      scripts=['bin/pycardsyncer', 'bin/pc_query'],
      data_files=[('config', ['pycard.conf.sample']),('README', ['README.rst'])],
      )
