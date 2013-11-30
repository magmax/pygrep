#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007, 2008, 2009, 2010  Miguel Ángel García Martínez \
# <miguelangel.garcia@gmail.com>"

#     This file is part of Pygrep.

#  Pygrep is free software; you can redistribute it and/or modify \
#it under the terms of the GNU General Public License as published by \
#the Free Software Foundation; either version 3 of the License, or \
#(at your option) any later version.

#  Pygrep is distributed in the hope that it will be useful, \
#but WITHOUT ANY WARRANTY; without even the implied warranty of \
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \
#GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License along \
#with Pygrep (maybe in file "COPYING"); if not, write to the Free Software \
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from distutils.core import setup
from pygrepinfo import PygrepInfo


setup ( 
      name         = PygrepInfo.name,
      version      = PygrepInfo.version,
      description  = PygrepInfo.description,
      author       = PygrepInfo.author,
      author_email = PygrepInfo.author_email,
      url          = PygrepInfo.url,
      license      = PygrepInfo.license,
      data_files   = PygrepInfo.data_files,
      scripts      = PygrepInfo.scripts
      )


