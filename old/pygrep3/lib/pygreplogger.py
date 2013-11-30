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

""" Module to manage the log """

import logging
import logging.config
import sys
import os
import traceback
import utilities
from paths import Paths

class PygrepLog ( object ):
    """ Manages the log """
    __metaclass__ = utilities.Singleton

    FILENAME = Paths.join ( Paths().share, "log.config" )

    def __init__ ( self ):
        logging.config.fileConfig ( PygrepLog.FILENAME )
        self.logger = logging.getLogger( "root" )
        self.logger.setLevel ( logging.DEBUG )
        self.fileloaded = False

        logging.getLogger("Pygrep").disabled = True

        self.debug = None
        self.info  = None
        self.warning = None
        self.error   = None
        self.critical = None

        self.__set_mappings ()

    def __set_mappings (self):
        """ Set mappings with python logger. """
        self.debug = self.logger.debug
        self.info  = self.logger.info
        self.warning = self.logger.warning
        self.error   = self.logger.error
        self.critical = self.logger.critical


    def set_debug_mode ( self ):
        """ Set the mode debug """
        self.logger = logging.getLogger("Pygrep")
        logging.getLogger("Pygrep").disabled = False
        self.__set_mappings()

    def print_system_info ( self ):
        """ Prints the system info. """
        self.info ( "Operating System: %s", os.uname() )
        self.info ( "Python version: %s", sys.version )
        self.info ( "Paths: %s", Paths() )
        self.info ( "Current Path: %s", os.path.abspath ( os.path.curdir ) )

    def print_stack_trace ( self, sys_exc_info ):
        """ Prints the stacktrace """
        exc_type, exc_value, exc_traceback = sys_exc_info
        trace = traceback.format_exception ( exc_type, exc_value,
                                                exc_traceback )
        self.set_debug_mode ()
        self.error ( trace )
        for i in trace:
            self.debug ( i )
        