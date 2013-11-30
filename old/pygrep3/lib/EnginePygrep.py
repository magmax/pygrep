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

""" Specific options for the Pygrep Engine """
from EngineGeneric import EngineException
import os.path

import re
import os
from pygreplogger import PygrepLog
from EngineGeneric import GenericEngine, EventLine, EventFile, EventEnd
from searchbuffer import SearchBuffer, Line, Token
from gettext import gettext as _
import time

class PygrepEngine (GenericEngine):
    """ Pygrep own engine """
    myname        = "Pyrep Engine"
    mydescription = "Embeded pygrep engine"

    def __init__ ( self ):
        super(PygrepEngine, self).__init__ ( )

        self.__split_line = self.__split_line_match

    def __parse_common_options ( self ):
        """ parse common options to stablish common values """
        if self.options.regexp:
            PygrepLog().debug ( "PygrepEngine: using regexp")
            self.__split_line = self.__split_line_regexp
        elif self.options.ignore_case:
            PygrepLog().debug ( "PygrepEngine: using ignorecase")
            self.__split_line = self.__split_line_ignorecase
        else:
            PygrepLog().debug ( "PygrepEngine: using match")
            self.__split_line = self.__split_line_match

    def run ( self ):
        """ Begins the search process """
        # if self.options.regularExpresion:   return
        PygrepLog().debug ( "PygrepEngine: Starting")
        PygrepLog().debug ( [x.prettyprint() for x in self.options.directory_list ] )
        PygrepLog().debug ( [x.prettyprint() for x in self.options.inclusion_list ] )
        PygrepLog().debug ( [x.prettyprint() for x in self.options.exclusion_list ] )
        _begin = time.time ()
        _files = 0
        self.end = False
        pattern = self.options.pattern

        if self.options.whole_word:
            pattern = "\b%s\b" % pattern
        if self.options.ignore_case:
            pattern = "(?i)" + pattern
        _comppatern = re.compile ( pattern )

        self.__parse_common_options ( )

        for directory in self.options.directory_list :
            if self.end:
                    break
            if not self.must_be_visited ( directory.str ):
                continue
            for _dirpath, _dirnames, _filelist in os.walk ( directory.str ):
                if self.end:
                    break
                for _filename in _filelist:
                    if self.end:
                        break
                    _fullpath = os.path.join( _dirpath, _filename )
                    if not self.must_be_visited ( _fullpath ):
                        return
                    self.process_file ( self.options.pattern, _comppatern,
                        _fullpath )
                    _files += 1
        self.end = True
        self.events.notify ( EventEnd ( _files, time.time() - _begin ),
                    GenericEngine.TOPIC_END )

    def process_buffer ( self, pattern, buff ):
        """
        Processes a buffer. Do not launch events;
        Returns an array of Line
        """
        _comppattern = None
        try:
            _comppattern = re.compile ( pattern )
        except re.error as exc:
            raise EngineException ( exc )

        self.__parse_common_options ( )

        _lineno = 0
        _retval = []
        for _line in buff.split ( '\n' ):
            _lineno += 1
            _new_matchs = self.__split_line ( pattern, _comppattern, _line,
                _lineno)

            _retval.append ( _new_matchs )

        return _retval

    def process_file ( self, pattern, comppattern, filename ):
        """ processes a file. """
        _cnt = 0
        _lineno = 0
        _sbuffer = None
        _fd = None

        if comppattern == None:
           comppattern = re.compile ( pattern )

        _sbuffer = SearchBuffer ( self.options.lines_before,
            self.options.lines_after )
        
        try:
            _fd = open(filename)
        except IOError as exc:
            PygrepLog().warning ( _("Problems while opening file '%s': %s"),
                filename, exc )
            return
        except Exception as exc:
            PygrepLog().warning ( _("Unknown error opening file '%s': %s"),
                filename, exc )
            return

        _anymatch = False
        for _line in _fd.readlines():
            if self.end:
                break
            _lineno += 1
            _new_matchs = self.__split_line ( pattern, comppattern, _line,
                _lineno)
            _cnt += _new_matchs.matchs

            _anymatch = _anymatch or _new_matchs.matchs > 0

            if _sbuffer.append( _new_matchs ):
                _list_to_show = _sbuffer.get()

                self.events.notify ( EventLine(filename, _list_to_show),
                    GenericEngine.TOPIC_LINE )
                _anymatch = False
                _sbuffer.clear()

        #process last element if any
        if _anymatch:
            _list_to_show = _sbuffer.get()
            if _list_to_show and _sbuffer.matchs > 0:
                self.events.notify ( EventLine(filename, _list_to_show),
                    GenericEngine.TOPIC_LINE )

        splitfilename = self.__split_line ( pattern, comppattern, filename, 0 )
        if (_cnt and not self.end) or splitfilename.matchs :
            self.events.notify (
                EventFile ( _cnt, filename, splitfilename ),
                GenericEngine.TOPIC_FILE )

        _fd.close()
   

    def __split_line_regexp (self, pattern, comppattern, line, lineno):
        """  Splits a string line into a Line (for regexp searchs)"""
        _buf = line
        _lineobj = Line ( lineno )
        _match = None

        
        while _buf and _buf[-1] in ['\n', '\r']:
            _buf = _buf[:-1]

        while _buf:
            try:
                _match = re.search ( comppattern, _buf )
            except re.error as exc:
                raise EngineException ( exc.message )
            if _match == None:
                # no more matches
                _lineobj.append ( Token (_buf, False) )
                break
            if ( _match.start() == _match.end() ):
                # ignore this
                _buf = _buf[1:]
                continue

            if _match.start() > 0:
                # text before the match
                _lineobj.append ( Token (_buf[:_match.start()], False) )

            # matching text
            _lineobj.append ( Token ( _buf[_match.start():_match.end()], True ))

            _buf = _buf[_match.end():]
        return _lineobj

    def __split_line_ignorecase (self, pattern, comppatern, line, lineno):
        """ Splits a string line into a Line (for ignorecase searchs )"""
        _lineobj = Line (lineno)

        _up_line = line.upper()
        _exp = pattern.upper()

        _size = len(_exp)
        _pos = 0

        while True:
            _word = ""
            _begin = _up_line.find(_exp, _pos)
            #not matching part
            if _begin == -1:
                _word = line[_pos:]
            else:
                _word = line[_pos:_begin]

            _word = _word.rstrip("\r\n")

            if _word != "":
                _lineobj.append ( Token ( _word, False ) )

            #matching part
            if _begin == -1:
                break

            _word = line[_begin:_begin + _size].rstrip("\r\n")
            if _word != "":
                _lineobj.append ( Token (_word, True) )

            _pos = _begin + _size

        return _lineobj


    def __split_line_match (self, pattern, comppatern, line, lineno):
        """ Splits a string line into a Line (for regexp normal searchs)"""
        _lineobj = Line (lineno)

        _up_line = line
        _exp = pattern

        _size = len( _exp )
        _pos = 0

        while True:
            _word = ""
            _begin = _up_line.find (_exp, _pos)
            #not matching part
            if _begin == -1:
                _word = _up_line[_pos:]
            else:
                _word = _up_line[_pos:_begin]

            _word = _word.rstrip("\r\n")

            if _word != "":
                _lineobj.append ( Token ( _word, False ) )

            #matching part
            if _begin == -1:
                break

            _word = _up_line[_begin:_begin + _size].rstrip ( "\r\n" )
            if _word != "":
                _lineobj.append ( Token ( _word, True ) )

            _pos = _begin + _size

        return _lineobj
        
