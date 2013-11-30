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

""" Options for all engines """

from reportlab.graphics.shapes import NotImplementedError
import os
import ConfigParser
import utilities
from paths import Paths
from pygrepinfo import PygrepInfo
from pygreplogger import PygrepLog

class EnabledString (object):
    """ Duple of Enabled + String with some methods improved. """
    def __init__ (self, string, enabled=True):
        self.str = string
        self.enabled = enabled
        self.__eq__ = self.str.__eq__
        self.__str__ = self.str.__str__
        
    def __getitem__ ( self, pos ):
        #print 'getitem %d'% pos
        if pos == 0:
            return self.enabled
        if pos == 1:
            return self.str
        return None

    def clone ( self ):
        """ Clones an EnabledString """
        retval = EnabledString ( self.str, self.enabled )
        return retval

    def prettyprint ( self ):
        """ Print it handsome """
        retval = ""
        if self.enabled:
            retval += '_' + self.str + '_'
        else:
            retval += self.str.lower()

        return retval

    def __str__ ( self ):
        """ Returns the object like a string """
        return self.prettyprint ()
        
ES = EnabledString

class EngineOptions (object):
    """
    Options valid for any of the engines.
    """
    def __init__ ( self ):
        super(EngineOptions, self).__init__()
        self.ignore_case      = True
        self.whole_word       = False
        self.lines_after      = 0
        self.lines_before     = 0
        self.max_size         = 0
        self.regexp           = False
        self.exclusion_list   = [ES('*CVS*'), ES('*.svn*'), ES('*~'),
                                    ES('*.avi'), ES('*.iso')]
        self.inclusion_list   = []
        self.directory_list   = [ES('.')]
        self.pattern          = ""

    def clone ( self ):
        """ Clones a EngineOptions """
        retval = EngineOptions ()
        retval.ignore_case      = self.ignore_case
        retval.whole_word       = self.whole_word
        retval.lines_after      = self.lines_after
        retval.lines_before     = self.lines_before
        retval.max_size         = self.max_size
        retval.regexp           = self.regexp
        retval.exclusion_list   = self.exclusion_list [:]
        retval.inclusion_list   = self.inclusion_list [:]
        retval.directory_list   = self.directory_list[:]
        retval.pattern          = self.pattern
        return retval

    def prettyprint ( self ):
        """ prints an object beautifully """
        retval = ''
        retval += 'Ignore case: %s\n' % self.ignore_case
        retval += 'Lines after: %s\n' % str ( self.lines_after )
        retval += 'Lines before: %s\n' % str ( self.lines_before )
        retval += 'Max file size: %d\n' % self.max_size
        return retval

    def __str__ ( self ):
        """ Returns the object like a string """
        return self.prettyprint ( )

class ExtendedOptions ( EngineOptions ):
    """
    Options valid for any of the engines with GUI.
    """
    def __init__ ( self ):
        super(ExtendedOptions, self).__init__()
        self._history             = []
        self.min_launch           = False
        self._command             = None
        self.profile_path         = Paths().config
        self.loaded_profile       = None
        
    def get_command ( self ):
        """ Gets the command value """
        if self._command:
            return self._command
        return os.environ.get ( "EDITOR", None ) + " %f"

    def set_command ( self, command ):
        """ Sets the command value"""
        self._command = command

    def change_history ( self, enabled, pattern ):
        """ adds a history entry or updates it """
        for item in self._history:
            if item.str == pattern:
                item.enabled = enabled
                return
        self._history.append ( EnabledString ( pattern, enabled ) )
        raise NotImplementedError ()

    def get_profile_list ( self ):
        """ gets the list of profiles """
        retval = []
        for name in os.listdir ( self.profile_path ):
            if name[-4:] == ".cfg":
                retval.append ( name[:-4] )
        retval.sort ()
        return retval

    def delete_profile ( self, profile ):
        """ deletes a profile """
        filename = self.__get_file_for_profile(profile)
        os.remove ( filename )

    def __get_file_for_profile ( self, profile):
        """ Gets the filename for a profile """
        retval =  Paths().join ( self.profile_path, profile + ".cfg" )
        PygrepLog().debug ( "Profile '%s' => file '%s'", profile, retval )
        return retval

    def load_from_file ( self, profile ):
        """ loads data from a profile """
        self.loaded_profile = None
        if not profile:
            return

        PygrepLog().debug ( "Loading profile %s", profile )

        config = ConfigParser.ConfigParser()
        config.read ( self.__get_file_for_profile(profile) )

        def list2vector ( section ):
            """ changes a list into a vector """
            retval = []
            if not config.has_section ( section ):
                return retval
            for item in config.items ( section ):
                enabled, value = item[1].split (',')
                if value:
                    retval.append ( EnabledString ( value, enabled == 'True' ) )
            return retval

        def get_option ( section, option, default ):
            """ gets an option with a default value """
            if not config.has_option ( section, option ):
                return default
            return config.get ( section, option )


        self.directory_list = list2vector ( 'search directories' )
        self.inclusion_list = list2vector ( 'patterns to include' )
        self.exclusion_list = list2vector ( 'patterns to exclude' )
        self._history       = list2vector ( 'pattern history' )

        self.ignore_case   = get_option ( 'miscelanea', 'ignore_case', True)
        self.whole_word    = get_option ( 'miscelanea', 'search_by_word', False)
        self._command      = get_option ( 'miscelanea', 'command', None)
        self.min_launch    = get_option ( 'miscelanea', 'minimize_on_launch',
                                            False)
        self.lines_before  = get_option ( 'miscelanea', 'lines_before_match', 0)
        self.lines_after   = get_option ( 'miscelanea', 'lines_after_match', 0)

        self.loaded_profile = profile

    def save_to_file ( self, profile ):
        """ saves data to a file from a profile """
        if not profile:
            return

        PygrepLog().debug ( "Saving profile %s", profile )

        config = ConfigParser.ConfigParser()

        def vector2list ( section, vector, allow_falses=True ):
            """ changes a vector into a list """
            config.add_section ( section )
            for item, i in zip ( reversed(vector), xrange ( len ( vector ) ) ):
                if allow_falses or item[0]:
                    config.set ( section, "entry %d"%i, "%s,%s" % (
                        item[0],item[1] )
                        )


        config.add_section ("metainfo")
        config.set("metainfo", "program", "Pygrep")
        config.set("metainfo", "version", PygrepInfo.version)
        config.set("metainfo", "repository",
            "$Id: pygrep.py,v 1.39 2009/11/03 06:13:21 magmax Exp $")


        vector2list ( "search directories", self.directory_list )
        vector2list ( "patterns to include", self.inclusion_list )
        vector2list ( "patterns to exclude", self.exclusion_list )
        vector2list ( "pattern history", self._history, False )

        config.add_section ( "miscelanea" )
        config.set( "miscelanea", "ignore_case", self.ignore_case )
        config.set( "miscelanea", "search_by_word", self.whole_word )
        config.set( "miscelanea", "command", self.command )
        config.set( "miscelanea", "minimize_on_launch", self.min_launch )
        config.set( "miscelanea", "lines_before_match", self.lines_before )
        config.set( "miscelanea", "lines_after_match",  self.lines_after )

        filed = open ( self.__get_file_for_profile(profile) , 'w+' )
        config.write ( filed )
        filed.close ()
        

    command            = property ( get_command, set_command )
    profile_list       = property ( get_profile_list, None )

class PersistentOptions (ExtendedOptions):
    """
    Options for engine and more.
    """
    __metaclass__ = utilities.Singleton


