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

""" Options for the viewers """

from paths import Paths
import ConfigParser
import re

class TextProperties ( object ):
    """ Properties for Text """
    def __init__ ( self ):
        self.weight     = 'normal'
        self.style      = 'normal'
        self._foreground = None
        self._background = None
        self.underline  = 'none'

    def get_pango_string ( self ):
        """ Transforms the TextProperties into a pango string """
        properties = ''
        if self.weight:
            properties += ' weight="%s"' % self.weight
        if self.style:
            properties += ' style="%s"' % self.style
        if self._foreground:
            properties += ' foreground="%s"' % self._foreground
        if self._background:
            properties += ' background="%s"' % self._background
        if self.underline:
            properties += ' underline="%s"' % self.underline
        return '<span%s>%s</span>' % (properties, '%s')

    def clone ( self ):
        """ Returns a copy of a TextProperties object """
        retval = TextProperties ()
        retval.copy ( self )
        return retval

    def copy ( self, text_properties ):
        """ copies the data from other TextProperty """
        self.weight = text_properties.weight
        self.style  = text_properties.style
        self._foreground = text_properties.get_foreground ()
        self._background = text_properties.get_background ()
        self.underline  = text_properties.underline

    def __str__ ( self ):
        """ Serializes the object into a string """
        return self.get_pango_string ( )

    def get_background ( self ):
        """ Returns the background color """
        return self._background

    def _normalize_color ( self, color ):
        """ Sets the color with only 3 componets, just like #123456 """
        if color == None:
            return None
        value = color.__str__()
        if re.match ( "^#[\da-fA-F]{3}$", value ):
            retval = "#"
            for i in [1, 2, 3]:
                retval += 2 * value[i]
            return retval
        if re.match ( "^#[\da-fA-F]{6}$", value ):
            return value
        if re.match ( "^#[\da-fA-F]{12}$", value ):
            retval = '#'
            for i in [1, 2, 5, 6, 9, 10]:
                retval += value[i]
            return retval
        return None

    def set_background ( self, value ):
        """ Sets the background color """
        self._background = self._normalize_color ( value )

    def get_foreground ( self ):
        """ Returns the foreground color """
        return self._foreground

    def set_foreground ( self, value ):
        """ Sets the foreground color """
        self._foreground = self._normalize_color ( value )
            
    background = property ( get_background, set_background )
    foreground = property ( get_foreground, set_foreground )

class ViewOptions ( object ):
    """ Defines the options for the view """
    def __init__ ( self ):
        self.format_fil_match     = TextProperties ()
        self.format_lin_match     = TextProperties ()
        self.format_lin_match_exp = TextProperties ()
        self.filename = Paths().join ( Paths().config, "general.vcfg" )

        # Default data
        self.format_fil_match.foreground = "#ff0000"
        self.format_fil_match.weight = "bold"

        self.format_lin_match.style = "italic"

        self.format_lin_match_exp.weight = "bold"
        self.format_lin_match_exp.underline = "single"
        self.format_lin_match_exp.foreground = "#ff0000"

    def _append_textprop ( self, config, section, properties ):
        """ Appends a TextProperties to a ConfigParser """
        config.add_section ( section )
        config.set ( section, "weight", properties.weight )
        config.set ( section, "style", properties.style )
        config.set ( section, "foreground", properties.foreground )
        config.set ( section, "background", properties.background )
        config.set ( section, "underline", properties.underline )

    def _load_textprop ( self, config, section, properties ):
        """ Loads the data from a ConfigParser to a TextProperties """
        if not config.has_section ( section ):
            return
        properties.weight = \
            self._get_option ( config, section, "weight", "normal")
        properties.style = \
            self._get_option ( config, section, "style", "normal")
        properties.foreground = \
            self._get_option ( config, section, "foreground", None)
        properties.background = \
            self._get_option ( config, section, "background", None)
        properties.underline = \
            self._get_option ( config, section, "underline", "none")

    def _get_option ( self, config, section, option, default ):
        """ gets an option with a default value """
        if not config.has_option ( section, option ):
            return default
        return config.get ( section, option )


    def save_to_file ( self ):
        """ Saves data to the config file """
        config = ConfigParser.ConfigParser()

        self._append_textprop ( config, "file match", self.format_fil_match )
        self._append_textprop ( config, "line match", self.format_lin_match )
        self._append_textprop ( config, "matching pattern",
                self.format_lin_match_exp )

        filed = open ( self.filename , 'w+' )
        config.write ( filed )
        filed.close ()
        
    def load_from_file ( self ):
        """ Loads data from the config file """
        config = ConfigParser.ConfigParser()
        config.read ( self.filename )

        self._load_textprop(config, "file match", self.format_fil_match )
        self._load_textprop(config, "line match", self.format_lin_match )
        self._load_textprop(config, "matching pattern",
                self.format_lin_match_exp )

    def clone ( self ):
        """ Returns a copy of itself """
        retval = ViewOptions ()
        retval.filename = self.filename
        retval.format_fil_match = self.format_fil_match.clone()
        retval.format_lin_match = self.format_lin_match.clone()
        retval.format_lin_match_exp = self.format_lin_match_exp.clone()
        return retval
