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
Main class for pygrep.
"""

# repository version: $Id$

###############################################################################

from paths import Paths
from pygreplogger import PygrepLog
from viewergtk import PygrepGtk
from viewertext import PygrepText
import sys
from optparse import OptionParser
from optparse import OptionGroup

from pygrepinfo import PygrepInfo
from EnginePygrep import PygrepEngine
from parserfields import PygrepParserFields

import gettext
_ = gettext.gettext

try:
    gettext.bindtextdomain ( "pygrep", Paths().locale )
    gettext.textdomain ( "pygrep" )
except IOError:
    pass
except Exception:
    pass

def array2parser ( array, group ):
    """ translates an array into a parser fields """
    for item in array:
        # @type item PygrepParserFields
        if item.short:
            group.add_option ( item.short, item.long, action=item.action,
                default=item.default, help=item.help )
        else:
            group.add_option ( item.long, action=item.action,
                default=item.default, help=item.help )


def get_argument_parser ( ):
    """ returns a list of parserfields, ready to translate into arguments """
    retval = []
    retval.append ( PygrepParserFields ( "--pygrep-engine", "store", "pygrep",
        'Select one of the engines ( grep, pygrep ). Default is "pygrep".') )
    retval.append ( PygrepParserFields ( "--pygrep-viewer", "store", 'gtk',
        'Selects one of the viewers ( gtk, text ). Default is "gtk".' ) )
    retval.append ( PygrepParserFields ( "--pygrep-usepsyco", "store_true",
        False, "Uses psyco to improve pygrep performance. "+\
        "It can crash in some distributions." ) )
    retval.append ( PygrepParserFields ( "--pygrep-debugdump", "store_true",
        False, "Enables the debug mode and sets a dump file." ) )
    return retval

def get_viewer ( engine, arguments, options ):
    """ Gets the viewer. """
    viewer = None
    if arguments.pygrep_viewer == 'gtk':
        viewer = PygrepGtk ( engine, arguments, options )
    elif arguments.pygrep_viewer == 'text':
        viewer = PygrepText ( engine, arguments, options )

    if not viewer:
        print "Sorry, you must specify a valid viewer."
        sys.exit (-1)
    PygrepLog().debug ( "VIEWER=%s", arguments.pygrep_viewer)
    return viewer

def load_psyco ( usepsyco ):
    """ Loads psyco library if required. """
    if usepsyco:
        try:
            import psyco
            #        psyco.log()
            psyco.full()
            #        psyco.profile(0.2, memory=100)
            PygrepLog().info ( "Using PSYCO library.")
        except ImportError:
            PygrepLog().warning ( "Install python-psyco to use this feature. " +
                                 "Program will continue without this feature." )


def run ():
    """ Main class: knows what to do. """
    #get arguments
    description = "Pygrep is a grep like tool app with GUI.\n"+\
        "Bugs, queries and pieces of pizza, refer %s" % PygrepInfo.url
    argparser = OptionParser ( usage="usage: %prog [options]",
                               version="    %s %s by %s %s" % ("%prog",
                                    PygrepInfo.version, PygrepInfo.author,
                                    PygrepInfo.author_email ),
                               description=description,
                               conflict_handler="resolve"
                               )
    array2parser ( get_argument_parser (), argparser)
    group = OptionGroup ( argparser, PygrepEngine.myname,
        "Valid options only for "  + PygrepEngine.mydescription )
    argparser.add_option_group ( group )
    array2parser ( PygrepEngine.arguments, group )
    arguments, options = argparser.parse_args()

    #configure logger if necessary
    if arguments.pygrep_debugdump:
        PygrepLog().set_debug_mode()

    #load psyco
    load_psyco(arguments.pygrep_usepsyco)

    #load the engine
    #this options has been removed. Only one engine will be supported.
    
    #load the viewer
    viewer = get_viewer( PygrepEngine, arguments, options )

    #run the viewer.
    viewer.run()

# MAIN
if __name__ == "__main__":
    try:
        run()
        #time.sleep(10)
    except Exception:
        try:
            PygrepLog().set_debug_mode()
        except Exception:
            # ignore
            pass
        PygrepLog().print_stack_trace( sys.exc_info () )
        PygrepLog().critical (
            "An error was found. Emergency file has been created.")
        PygrepLog().critical (
            "Please, send the file at ~/pygrep.dump file to %s %s"
            % ( PygrepInfo.author, PygrepInfo.author_email ) )
