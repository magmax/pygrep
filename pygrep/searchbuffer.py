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

"""
Implements a neverending buffer with a limited size.
"""

class Token:
    """
    Each token of a line.
    """
    def __init__ (self, token, matchs):
        assert type (token) == str
        assert type (matchs) == bool
        self.token = token
        self.matchs = matchs

    def __cmp__ ( self, item):
        #assert type (item) == Token
        return not (item.matchs == self.matchs and item.token == self.token)

    def __str__ ( self):
        return self.token

    def clone ( self ):
        """ Clones a Token """
        retval = Token ( self.token, self.matchs )
        return retval

    def prettyprint ( self ):
        """ Prints the Token. """
        print(self)

class Line:
    """
    Implements a list of Tokens
    """
    def __init__ (self, linenum):
        self.matchs    = 0
        self.tokenlist = []
        self.linenum   = linenum

    def __cmp__ ( self, item ):
        #assert item == Line
        if self.matchs != item.matchs:
            return 1
        if len (self.tokenlist) != len ( item.tokenlist):
            return 1
        for i in range ( len ( self.tokenlist) ):
            if self.tokenlist[i] != item.tokenlist[i]:
                return 1
        return 0

    def __str__ ( self ):
        retval = ""
        for token in self.tokenlist:
            if token.matchs:
                retval += "[%s]" % token.token
            else:
                retval += token.token
        return retval

    def append (self, token):
        """ Appens a token to a line. """
        #assert type (token) == Token
        if token.matchs:
            self.matchs += 1
        self.tokenlist.append ( token )

    def clone ( self ):
        """ Clones a Line """
        retval           = Line ( self.linenum )
        retval.tokenlist = self.tokenlist [:]
        retval.matchs    = self.matchs

class SearchBuffer:
    """
    This class allows to use buffers of things, implemented as queues:
    First in, fist out. Pygrep will use Search Buffer as a buffer of Line.
    """
    def __init__(self, maxprev=0, maxnext=0):
        """ Initializes the FIFO """
        self.max_prev = int(maxprev)
        self.max_next = int(maxnext)
        self.curr_prev = 0
        self.curr_next = 0
        self.matchs = False # saves if any element inside matched.
        self.linelist = []
        self._clean = False  # the buffer must be cleared before appending.

    def __len__ ( self ):
        return self.linelist.__len__

    def append (self, line):
        """
            Adds an element to the FIFO
            Returns True if the buffer is ready to be processed.
        """
        #assert type (line) == Line
        if self._clean:
            self.clear ()
            
        self.matchs = self.matchs or line.matchs > 0
        self.linelist.append(line)

        if line.matchs > 0:
            self.curr_next = 0

        if self.matchs:
            self.curr_next += 1
        else:
            self.curr_prev += 1

        if self.curr_prev > self.max_prev:
            self.linelist.pop(0)
            self.curr_prev -= 1

        retval = self.matchs and self.curr_next > self.max_next
        self._clean = retval

        return retval

    def clear (self):
        """ Clears the buffer """
        self._clean = False
        self.matchs = False
        self.curr_next = 0
        self.curr_prev = len(self.linelist)
        while self.curr_prev > self.max_prev:
            self.linelist.pop(0)
            self.curr_prev -= 1


    def get (self):
        """
        Returns a copy of the list.
        """
        return self.linelist[:]
    
if __name__ == "__main__":
    print("Hello World")
