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

""" Manages the paths for the whole program """
import os
import utilities

FORCE_DEBIAN_DIRECTORIES = False

class Paths:
    """ Some generic paths useful for the application
    """
    __metaclass__ = utilities.Singleton


    application = None
    locale      = None
    help        = None
    share       = None
    glade       = None
    config      = None

    def __init__ ( self ):
        self.application = os.path.dirname(__file__)
        if self.application in ['/usr/bin/', '/usr/local/bin/'] \
                or FORCE_DEBIAN_DIRECTORIES:
            #self.locale      = '/usr/share/locale'
            self.locale      = None
            self.help        = os.path.join ( self.application, "help" )
            self.share       = "/usr/share/pygrep"
            self.glade       = self.share
            self.config      = os.path.expanduser (
                                    os.path.join ( '~', '.pygrep3' ) )
        else:
            self.locale      = os.path.join ( self.application, "po" )
            self.help        = os.path.join ( self.application, "help" )
            self.share       = os.path.join ( self.application )
            self.glade       = os.path.join ( self.application, "glade" )
            self.config      = os.path.expanduser (
                                    os.path.join ( '~', '.pygrep3' ) )

        if not os.path.exists ( self.config ):
            os.makedirs( self.config )

    @staticmethod
    def join ( *args ):
        """ Join two or more paths """
        return os.path.join ( *args )

    def __str__ ( self ):
        retval = ""
        retval += 'applications: ' + self.application + '\n'
        retval += 'locale: '       + self.locale + '\n'
        retval += 'help: '         + self.help + '\n'
        retval += 'share: '        + self.share + '\n'
        retval += 'glade: '        + self.glade + '\n'
        retval += 'config: '       + self.config + '\n'
        return retval
