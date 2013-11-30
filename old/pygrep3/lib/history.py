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

""" History persistence """

# This class is not been used by now.

from paths import Paths
import ConfigParser

class HistoryEntry:
    """ Defines the data for an entry of the history patterns """
    default_save_mode = 0

    def __init__ ( self, pattern, save=HistoryEntry.default_save_mode ):
        self.pattern = pattern
        self.save = save

    def pretty_print ( self ):
        """ transforms the History Entry into a beautiful string """
        return "[%s] %s" % ([' ', 'X'][self.save % 2], self.pattern)

    def __str__ ( self ):
        """ Gets only the main part """
        return self.pattern
    
class History:
    """ Manages the history persistence """
    SAVE_NO  = 0
    SAVE_YES = 1
    def __init__ ( self ):
        self.filename = Paths().join ( Paths().config, "history.vcfg" )
        self.vector = []

    def __del__ ( self ):
        """ Destructor """
        print "Saving history"

    def set ( self, pattern, save=HistoryEntry.default_save_mode):
        """ Sets a new pattern to history or updates an old one. """
        for i in self.vector:
            if i.pattern == pattern:
                i.save = save
                return

        self.vector.append ( HistoryEntry ( pattern, save ) )

    def set_default_save_mode ( self, status ):
        """ Sets the default save mode. """
        HistoryEntry.default_save_status = status

    def save ( self ):
        """ Saves data to the config file """
        config = ConfigParser.ConfigParser()

        section = "History"
        config.add_section ( section )

        for i, item in enumerate ( self.vector ):
            if item.save == History.SAVE_YES:
                config.set ( section, "item " + i, item.pattern )

        filed = open ( self.filename , 'w+' )
        config.write ( filed )
        filed.close ()

    def load ( self ):
        config = ConfigParser.ConfigParser()
        config.read ( self.filename )

        section = "History"

        if not config.has_section ( section ):
            return

        for item in config.items ( section ):
            self.set ( item )

    