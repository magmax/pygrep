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

from EngineGeneric import GenericEngine
from EnginePygrep import PygrepEngine
from EngineOptions import EngineOptions
import os.path
import os
from pygreplogger import PygrepLog
from viewergeneric import GenericViewer

__author__ = "Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>"
__date__ = "$28-dic-2009 21:04:30$"

class PygrepText ( GenericViewer ):
    COLOR_RED  = chr(27) + '[0;31m'
    COLOR_BOLD = chr(27) + '[0;32m'
    COLOR_NONE = chr(27) + '[0m'

    def _highlight ( self, text, highlight=False, color=COLOR_RED):
        if highlight:
            return "%s%s%s"% (color, text, PygrepText.COLOR_NONE)
        else:
            return text

    def _matchingLine ( self, obj ):
        filename, linevector = obj
        text = ""
        begin = ""
        beginline = ""
        end   = ""
        if len (linevector) == 1:
            beginline = self._highlight ( "%s:%d>" % (
                filename, linevector[0].linenum), True, PygrepText.COLOR_BOLD )
        else:
            end = "--"

        print begin,
        for line in linevector:
            text = beginline
            for token in line.tokenlist:
                text +=  self._highlight(token.token, token.matchs)

            print text
        print end,

        

    def main ( self ):
        PygrepLog().info ("Pygrep Text Viewer launched.")

        if len (self.options) == 0 :
            PygrepLog().debug("No options passed.")
            PygrepLog().error("Text viewer needs a pattern to search for.")
            return
        if len (self.options) == 1 :
            PygrepLog().debug( "No directories passed.")
            PygrepLog().error (
                "Text viewer needs one or more "+\
                "directories where begin to search.")
            return

        options = EngineOptions ()

        # @type engine PygrepEngine
        engineinst = self.engine()
        engineinst.loadOptionsFromArguments ( self.arguments )
        print engineinst.options

        engineinst.event_attach ( self._matchingLine, GenericEngine.TOPIC_LINE )
        
        # Load directories to search in
        engineinst.setpattern ( self.options[0] )
        for directory in self.options[1:]:
            path = os.path.abspath ( os.path.expanduser (
                os.path.expandvars( directory ) ) )
            engineinst.setdirectory ( path )
            engineinst.start ( )
            engineinst.join ()
            

