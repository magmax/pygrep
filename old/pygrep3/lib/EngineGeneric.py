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

""" Implements an abstract Engine """

import os
import os.path
from abc import abstractmethod
import threading
from utilities import Observable
#from parserfields import PygrepParserFields
import fnmatch
from EngineOptions import EngineOptions

__author__ = "Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>"
__date__ = "$23-dic-2009 21:08:58$"

class EngineException (Exception):
    """ Generic Exception on the engines. """
    def __init__ ( self, value ):
        self.value = value
        
    def __str__ ( self ):
        return str (self.value).capitalize()

class GenericEngineOptions (EngineOptions):
    """ ¿¿ Esto hace falta ?? """
    def __str__ ( self ):
        retval = 'Options:'
        if self.ignore_case:
            retval += "i"
        if self.whole_word:
            retval += "w"
        #if self.regularExpresion: retval += "E"
        #if self.linesAfterMatch: retval+= "A" + self.linesAfterMatch
        #if self.linesBeforeMatch: retval+= "B" + self.linesBeforeMatch
        #if self.maxSize: retval+="^" + self.maxSize
        #if self.exclusionList: retval+= "-" + self.exclusionList
        #if self.inclusionList: retval+= "+" + self.inclusionList

        return retval

    def prettyprint ( self ):
        """ Prints the generic options """
        print ( self )

class EventFile (object):
    """ Event launched when a new file matchs """
    def __init__ ( self, matches, filename, splitted ):
        self.matches  = matches
        self.path     = splitted
        self.filename = os.path.basename ( filename )

    def __str__(self):
        retval = "[ event: %d, %s, %s]" % ( self.matches,
                                            self.path, self.filename )
        return retval

class EventLine (object):
    """ Event launched when a new line matchs """
    def __init__ ( self, filename, linelist ):
        self.filename = filename
        self.linelist = linelist
        
    def __str__(self):
        retval = "[ event: %s, %s]" % ( self.filename, self.linelist )
        return retval

class EventEnd (object):
    """ Event launched when the search has finished """
    def __init__ ( self, processed_files, time_wasted ):
        self.processed_files = processed_files
        self.time_wasted     = time_wasted

    def __str__(self):
        retval = "[ event: %s, %s]" % ( self.processed_files, self.time_wasted )
        return retval

class GenericEngine ( threading.Thread ):
    """
    Implements common operations for engines.
    """
#    arguments     = [ PygrepParserFields (short="-i"),
#                      PygrepParserFields (short="-w"),
#                    ]
    arguments = []
    TOPIC_LINE    = "line"
    TOPIC_FILE    = "file"
    TOPIC_END     = "end"

    def __init__ ( self ):
        super(GenericEngine, self).__init__()

        # options
        self.options         = GenericEngineOptions ()

        # default values
        self.end = False     # end of proccess
        self.processed_files = 0 # num of files processed

        self.events = Observable ( 
            [   GenericEngine.TOPIC_LINE,
                GenericEngine.TOPIC_FILE,
                GenericEngine.TOPIC_END
                ]
                )
        self.event_attach = self.events.attach
        self.event_detach = self.events.detach

    def __del__(self):
        if self.isAlive():
            self.events.notify ( None, None)

    def load_options_from_arguments ( self, args ):
        """ load option data from arguments """
        self.options.ignore_case = args.i

    def must_be_visited (self, pathname):
        """ checks if a pathname must be visited or not. """
        is_file = os.path.isfile(pathname)

        if self.options.max_size > 0 and is_file:
            stat = os.stat(pathname)
            if stat.st_size > self.options.max_size:
                return False

        for epat in self.options.exclusion_list:
            if fnmatch.fnmatchcase ( pathname, epat.str ):
                return False

        # no patterns to include, all included;
        # directories are not in inclusions.
        if len ( self.options.inclusion_list ) == 0 or not is_file:
            return True

        for ipat in self.options.inclusion_list:
            if fnmatch.fnmatchcase ( pathname, ipat.str ):
                return True

        return False

    @abstractmethod
    def run ( self ):
        """ Main method that must be implemented in each class """
        raise NotImplementedError()

    @abstractmethod
    def process_file ( self, pattern, comppattern, filename):
        """ Process a file. Throws events. """
        raise NotImplementedError ()

    @abstractmethod
    def process_buffer ( self, pattern, buffer ):
        """ Process a buffer. Throws events. """
        raise NotImplementedError ()

