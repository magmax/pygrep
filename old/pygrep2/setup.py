#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(name         = 'pygrep',
      version      = '2.0.0',
      description  = 'The GUI for Grep',
      author       = 'Miguel Angel Garcia',
      author_email = '<miguelangel.garcia@gmail.com>',
      url          = 'http://www.magmax.org',
      license      = 'GPL v3 or later',
      data_files   = [('/usr/share/man/man1',['pygrep.1']),
                      ('/usr/share/pygrep', ['glade2/logo.png', 'glade2/logo2.png', 'glade2/logo2.svg', 'glade2/pygrep.glade'])],
      scripts      = ['pygrep.py']
      )
