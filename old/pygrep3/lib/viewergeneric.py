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

import gettext
from abc import abstractmethod

class GenericViewer (object):
    def __init__ ( self, engine, arguments, options = [] ):
        super ( GenericViewer, self ).__init__ ( )
        self.engine    = engine
        self.arguments = arguments
        self.options   = options
        self.pattern = None
        self.directory = None

    @abstractmethod
    def main( self ):
        raise NotImplementedError ()

    def run ( self ):
        # some checks
        self.main( )


if __name__ == "__main__":
    print "Hello World"
    