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

""" Default info of pygrep, to add it to the program and to the deb package """


class PygrepInfo (object):
    """
    Saves data for using in setup and in main program.
    """
    name          = "pygrep"
    version       = '3.0.0.alpha'
    description   = 'The Python Graphical Grep-like Tool'
    author        = 'Miguel Angel Garcia'
    author_email  = '<miguelangel.garcia@gmail.com>'
    url           = 'http://www.magmax.org'
    license       = 'GPL v3 or later'
    data_files    = [('/usr/share/man/man1', ['pygrep.1']),
                     ('/usr/share/pygrep', [
                        'glade2/logo.png',
                        'glade2/logo2.png',
                        'glade2/logo2.svg',
                        'glade2/pygrep.glade',
                        'log.config'
                        ]
                        )
                    ]
    scripts       = [
                    'pygrep.py',
                    'EngineGeneric.py',
                    'EnginePygrep.py',
                    'EngineGrep.py',
                    'EngineOptions.py',
                    'parsefields.py',
                    'paths.py',
                    'pygrepinfo.py',
                    'pygreplogger.py',
                    'searchbuffer.py',
                    'utilities.py',
                    'viewergeneric.py',
                    'viewergtk.py',
                    'viewertext.py'
                    ]
    revision      = '$Id$'
    author_list   = [
                     u"%s %s" % ( author, author_email ),
                     u"Rubén Martínez",
                     u"Ángel Manuel Carcelén",
                     u"Karl Berry",
                     u"David Villa, for the Debian package"
                    ]
    artists       = [ u"Sergio Camacho (brue)", u"Miguel Ángel García" ]

    license_text  = u"""\
   Pygrep is free software; you can redistribute it and/or modify \
it under the terms of the GNU General Public License as published by \
the Free Software Foundation; either version 3 of the License, or \
(at your option) any later version.

  Pygrep is distributed in the hope that it will be useful, \
but WITHOUT ANY WARRANTY; without even the implied warranty of \
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \
GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along \
with Pygrep (maybe in file "COPYING"); if not, write to the Free Software \
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
    copyright_text = u"Copyright 2007-2010  Miguel Ángel García Martínez \
<miguelangel.garcia@gmail.com>"
