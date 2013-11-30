#!/usr/bin/env python
# -*- coding: utf-8 -*-

#     This file is part of Pygrep. 
#     Please, read the "Copyright" and "LICENSE" variables for copyright advisement
#   (just below this line):

COPYRIGHT = "Copyright 2007 Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>"

LICENSE = """
  Pygrep is free software; you can redistribute it and/or modify \
it under the terms of the GNU General Public License as published by \
the Free Software Foundation; either version 3 of the License, or \
(at your option) any later version.

  Pygrep is distributed in the hope that it will be useful, \
but WITHOUT ANY WARRANTY; without even the implied warranty of \
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \
GNU General Public License for more details.

  You should have received a copy of the GNU General Public License \
along with Pygrep (maybe in file "COPYING"); if not, write to the Free Software \
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

VERSION = "2.0.0"
# cvs version: $Id: pygrep.py,v 1.40 2009/12/23 05:15:16 magmax Exp $

WEBSITE = "http://www.magmax.org/drupal/node/2"

AUTHORS = u"Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>"

###################################################################################

import gtk, gtk.glade, pango
import sys, os, re, fnmatch
import threading
import gobject
import ConfigParser
import optparse
from optparse import OptionParser, OptionGroup
import string,time
import signal

#search tab
COL_FILENAME = 2
COL_CNT     = 1
COL_FILE    = 0
COL_LINE    = 1
COL_LINETXT = 2
COL_TEXT    = 3
COL_MARKED_TEXT = 3
#directories tab
COL_ENABLE = 0
COL_PATTERN = 1
COL_DIR = 1
#history model
COL_HIS_SAVE = 0
COL_HIS_TEXT = 1


DEFAULTCONF="[DEFAULT]"

class Paths:
    """ Some generic paths useful for the application
    """
    is_debian_package = False
    @staticmethod
    def app_dir():
        return os.path.dirname(__file__)
    
    @staticmethod
    def locale_dir(*args):
        return os.path.join(Paths.app_dir(),"po", *args)
    
    @staticmethod
    def help_dir(*args):
        return os.path.join(Paths.app_dir(),"help", *args)
    
    @staticmethod
    def share_dir ( *args ):
        if Paths.is_debian_package:
          return os.path.join ( "/usr/share/pygrep", *args )
        return os.path.join ( Paths.app_dir(), *args )

    @staticmethod
    def glade_dir ( *args ):
        if Paths.is_debian_package:
            return Paths.share_dir ( *args )
        return os.path.join ( Paths.app_dir(), "glade2", *args )
    @staticmethod
    def config_dir(*args):
        return os.path.expanduser(os.path.join('~', '.pygrep', *args))

class Utilities:
    @staticmethod
    def file_regex2pyregex(regex):
        """
        Translates a file regular expresion (*,?) into a python regular expresion (.*,.).
        """
        if not regex:
            return None
        
        pat = "^"

        for i in regex:
            if pat != "^":
                pat += "|"
            pat += i + "$"

        pat = pat.replace(".", "\\.")
        pat = pat.replace("?", ".")
        pat = pat.replace("*", ".*")
        return pat

    @staticmethod
    def url_transformation(text):
        for orig, target in [("&","&amp;"), ("<","&lt;"), (">","&gt;")]:
            text = text.replace(orig, target)
        return text


    @staticmethod
    def gtkMessage(window, message):
        dialog = gtk.MessageDialog(window,
                                   gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_OK,
                                   message)

        dialog.connect("response", lambda x,y: dialog.destroy())
  
        dialog.show()

class Persistence:
    """ Saves and loads a Pygrep Options object """
    def __init__(self, options):
        self.options = options

    def __listES2csv(self, dirlist, all=True, enabled=True):
        """ Transforms a list of EnabledString into Comma Separated Values """
        retval = ""
        sep = False
        for directory in dirlist:
            if not all and not directory.enabled == enabled: 
                continue
            if sep:
                retval += ","
                sep = False
            retval += str(directory)
            sep = True

        return retval
        
    def save_options(self, filename):
        if not filename:
            return
        config = ConfigParser.ConfigParser()
        config.add_section ("metainfo")
        config.set("metainfo", "program", "Pygrep")
        config.set("metainfo", "version", VERSION)
        config.set("metainfo", "repository", "$Id: pygrep.py,v 1.40 2009/12/23 05:15:16 magmax Exp $")
        
        config.add_section ("directories")

        
        config.set("directories", "dirs",                 self.__listES2csv(self.options.directories))
        if self.options.has_key(Options.INCLUDE):
            config.set("directories", "include",          self.__listES2csv(self.options[Options.INCLUDE]))
        if self.options.has_key(Options.EXCLUDE):
            config.set("directories", "exclude",          self.__listES2csv(self.options[Options.EXCLUDE]))


        config.add_section ("directories_disabled")
            
        config.set("directories_disabled", "dirs",        self.__listES2csv(self.options.directories, False, False))
        if self.options.has_key(Options.INCLUDE):
            config.set("directories_disabled", "include", self.__listES2csv(self.options[Options.INCLUDE], False, False))
        if self.options.has_key(Options.EXCLUDE):
            config.set("directories_disabled", "exclude", self.__listES2csv(self.options[Options.EXCLUDE], False, False))
        
        config.add_section ("miscelanea")
        config.set("miscelanea", "ignore_case", self.options.get(Options.IGNORECASE, False))
        config.set("miscelanea", "search_by_word", self.options.get(Options.BYWORD, False))
        config.set("miscelanea", "command", self.options.get(Options.COMMAND, ""))
        config.set("miscelanea", "minimize_on_launch", self.options.get(Options.MINIMIZEONLAUNCH, False))
#        entry = self.pygrep.xml.get_widget("entry_size_limit")
#        config.set("miscelanea", "file_size_limit", entry.get_text())
#        check = self.pygrep.xml.get_widget("checkbutton_searchRE")
#        config.set("miscelanea", "search_re", check.get_active())
#         check = self.pygrep.xml.get_widget("checkbutton_by_word")
#         config.set("miscelanea", "search_by_word", check.get_active())

        config.set("miscelanea", "lines_before_match", self.options.get(Options.BEFORECONTEXT, 0))
        config.set("miscelanea", "lines_after_match",  self.options.get(Options.AFTERCONTEXT, 0 ))

        config.add_section ( "history" )
        j = 1
        for i in self.options.get(Options.HISTORY,[]):
            config.set("history", "entry %d" % j, i)
            j += 1
        

        filename = Paths.config_dir(filename + ".cfg")
        fd = None
        try:
            fd = open(filename, 'w+')
        except:
            pass
        if not fd:
            try:
                os.mkdir (Paths.config_dir())
                fd = open(filename, 'w+')
            except:
                print "ERROR: configuration won't be saved"
                return
        config.write(fd)
        fd.close()

    def __addES2vector(self, vector, string, enabled, enabled_exists=False):
        """ adds a EnabledString formed by (string, enabled) to the vector or
        sets the correct value to the existing one"""
        # base case: string is empty
        if not string:
            return
        # The string exists
        for i in vector:
            if i.str == string:
                i.enabled = enabled_exists
                return
        # The string does not exists:
        vector.append(EnabledString(string, enabled))


    def __disable_dirs (self, items):
        dirs_disabled = []
        inc_disabled = []
        exc_disabled = []
        
        for name, val in items:
            if name == "dirs":
                for d in val.split(','):
                    for i in self.options.directories:
                        if i.str==d:
                            i.enabled = False
                            break

            if name in ["include"]:
                for d in val.split(','):
                    for i in self.options.get(Options.INCLUDE, []):
                        if i.str==d:
                            i.enabled = False
                            break

            if name in ["exclude"]:
                for d in val.split(','):
                    for i in self.options.get(Options.EXCLUDE, []):
                        if i.str==d:
                            i.enabled = False
                            break
        
    def __load_dirs(self, items):
        dirs_disabled = []
        inc_disabled = []
        exc_disabled = []
        
        for name, val in items:
            if name == "dirs":
                for d in val.split(','):
                    if d: self.options.directories.append(EnabledString(d, True))

            # Some of the next code is mantained for backwards compatibility
            if name == "dirs_disabled":
                for d in val.split(','):
                    for i in self.options.directories:
                        if i.str==d:
                            i.enabled = False
                            break

            if name in ["include", "include_disabled"]:
                if self.options.get(Options.INCLUDE, None) == None:
                    self.options[Options.INCLUDE] = []
                for d in val.split(','):
                    self.__addES2vector(self.options[Options.INCLUDE], d, name=="include")

            if name in ["exclude", "exclude_disabled"]:
                if self.options.get(Options.EXCLUDE, None) == None:
                    self.options[Options.EXCLUDE] = []
                for d in val.split(','):
                    self.__addES2vector(self.options[Options.EXCLUDE], d, name=="exclude")

    def __load_history(self, items):
        self.options[Options.HISTORY] = []
        for name, val in items:
            self.options[Options.HISTORY].append (val)

    def __load_miscelanea(self, items):
        for name, val in items:
            if name == "command":
                if val and len(val) > 0:
                    self.options[Options.COMMAND] = val
#             elif name == "file_size_limit":
#                 entry = self.pygrep.xml.get_widget("entry_size_limit")
#                 if val: entry.set_text(val)
#             elif name == "search_re":
#                 check = self.pygrep.xml.get_widget("checkbutton_searchRE")
#                 check.set_active(val == "True")
            elif name == "ignore_case":
                self.options[Options.IGNORECASE] = (val == "True")
            elif name == "search_by_word":
                self.options[Options.BYWORD] = (val == "True")
            elif name == "lines_before_match":
                self.options[Options.BEFORECONTEXT] = float(val)
            elif name == "lines_after_match":
                self.options[Options.AFTERCONTEXT] = float(val)
            elif name == "minimize_on_launch":
                self.options[Options.MINIMIZEONLAUNCH] = (val == "True")
        
    def load_options(self, filename=None):
        config = ConfigParser.ConfigParser()
        if filename:
            config.read (['defaults.cfg', filename+".cfg", Paths.config_dir(filename+".cfg")])
        else:
            config.read (['defaults.cfg', 'options.cfg', Paths.config_dir('options.cfg')])
        #directories
        if config.has_section("directories"):
            self.__load_dirs(config.items("directories", True))
        if config.has_section("directories_disabled"):
            self.__disable_dirs(config.items("directories_disabled", True))
        if config.has_section("history"):
            self.__load_history(config.items("history", True))
        
        #miscelanea
        if config.has_section("miscelanea"):
            self.__load_miscelanea(config.items("miscelanea"))

        return self.options

class SearchBuffer:
    """ This class allows to use buffers of things, implemented as queues: First in, fist out. Pygrep will use Search Buffer as a buffer of Line """
    def __init__(self, prev=0, next=0):
        """ Initializes the FIFO """
        self.max_prev = prev
        self.max_next = next
        self.prev = 0
        self.next = 0
        self.matchs = False # saves if any element inside matched.
        self.list = []

        self.__len__ = self.list.__len__

    def append (self, elem, matched):
        """ Adds an element to the FIFO """
        self.matchs = self.matchs or matched
        self.list.append(elem)

        if matched:
            self.next = 0

        if self.matchs:
            self.next += 1
        else:
            self.prev += 1

        if self.prev > self.max_prev:
            self.list.pop(0)
            self.prev -= 1

        return self.matchs and self.next > self.max_next

    def get_and_clean (self):
        retval = self.list[:]
        self.matchs = False
        self.next   = 0
        self.prev = len(self.list)
        while self.prev > self.max_prev:
            self.list.pop(0)
            self.prev -= 1
        return retval

class Component:
    """ Component of a (possibly) matching string """
    def __init__(self, string="", match=False):
        self.string = string
        self.match  = match

    def __str__(self):
        return "(" + str(self.match) + "," + self.string + ")"


class Line:
    """ Vector of Components with some properties """
    def __init__(self, number=0, matchnum=False, components=None):
        self.number     = number
        self.matchnum   = matchnum
        if components:
            self.components = components
        else:
            self.components = []

    def __str__(self):
        retval = "(" + str(self.number) + "," + str(self.matchnum) + ",["
        for i in self.components:
            retval+= str(i) + ","
        retval += "])"
        return retval
    
class EnabledString:
    """ Duple of Enabled + String with some methods improved. """
    def __init__ (self, string, enabled=True):
        self.str = string
        self.enabled = enabled
        self.__eq__ = self.str.__eq__
        self.__str__ = self.str.__str__

class SearchEngine(threading.Thread):
    def __init__(self, options):
        super(SearchEngine, self).__init__()

        # options
        self.options      = options

        # default values
        self.search_exp  = None
        self.comp_exp = None  # compiled expresion
        self.dir = "."       # search directory
        self.end = False     # end of proccess
        self.processed_files = 0 # num of files processed

        # callbacks
        self.file_callback = self.print_file
        self.line_callback = self.print_line
        self.end_callback = self.print_end
        self.processed_file = self.print_processed_file

        # other optimizations
        self.include = []
        if self.options.has_key(Options.INCLUDE):
            for i in self.options[Options.INCLUDE]:
                if i.enabled:
                    self.include.append(i.str)

        self.exclude = []
        if self.options.has_key(Options.EXCLUDE):
            for i in self.options[Options.EXCLUDE]:
                if i.enabled:
                    self.exclude.append(i.str)


    def __del__(self):
        if self.isAlive():
            self.end_callback()

    def print_file(self, filename, cnt, search_obj=None):
        """ default file_callback: prints the information about matched files. """
        print "%s:%s"%(filename, cnt)

    def print_line(self, filename, lineobj):
        """ default line_callback: prints the information about matched lines. """
        print "%s:%s"%(filename, lineobj)

    def print_end(self):
        """ default end_callback: prints at the end of the search"""
        print "ended"

    def print_processed_file(self):
        """ default processed_file_callback: prints another file processed """
        print "another file processed. Total: %d",self.processed_files


    def must_be_visited (self, pathname):
        """ checks if a pathname must be visited or not. """
        is_file = os.path.isfile(pathname)

#         if self.size_limit > 0 and is_file:
#             stat = os.stat(pathname)
#             if stat.st_size > self.size_limit:
#                 return False

        for epat in self.exclude:
            if fnmatch.fnmatchcase(pathname, epat):
                return False

        # no patterns to include, all included; directories are not in inclusions.
        if len(self.include)==0 or not is_file:
            return True

        for ipat in self.include:
            if fnmatch.fnmatchcase(pathname, ipat):
                return True

        return False

class PygrepEngine(SearchEngine):
    def __init__(self, options):
        super(PygrepEngine, self).__init__(options)

        self.__split_line = self.__split_line_match  # default check_line method
        
    def __compile(self):
        if self.comp_exp or not self.options.get(Options.REGEXP, False):
            return

        if self.options.get(self.BYWORD, False):
            self.search_exp = "\b%s\b"%self.search_exp
        if self.options.get(self.IGNORECASE, False):
            self.search_exp = "(?i)" + self.search_exp
        self.comp_exp = re.compile(self.search_exp)


    def __split_line_regexp (self, line, lineno):
        """  Splits a string line into a Line (for regexp searchs)"""
        # TODO: It is necessary to mark the regular expression
        #       The algorithm is next: to use findall and apply an algorithm similar to split_line_match to find every element of the result of findall.
        found =  re.findall(self.comp_exp, line)

        return Line(lineno, len(found), [Component(line.rstrip("\r\n"), False)])
            
    def __split_line_ignorecase (self, line, lineno):
        """ Splits a string line into a Line (for ignorecase searchs )"""
        lineobj = Line()
        lineobj.number = lineno

        tr_line = line.upper()
        exp = self.search_exp.upper()

        size = len(exp)
        pos = 0

        while True:
            word = ""
            begin = tr_line.find(exp, pos)
            #not matching part
            if begin == -1:
                word = line[pos:]
            else:
                word = line[pos:begin]

            word = word.rstrip("\r\n")

            if word != "":
                lineobj.components.append(Component(word, False))

            #matching part
            if begin == -1:
                break

            lineobj.matchnum += 1
            word = line[begin:begin+size].rstrip("\r\n")
            if word != "":
                lineobj.components.append(Component(word, True))

            pos = begin+size

        return lineobj


    def __split_line_match (self, line, lineno):
        """ Splits a string line into a Line (for regexp normal searchs)"""
        lineobj = Line()
        lineobj.number = lineno

        tr_line = line
        exp = self.search_exp

        size = len(exp)
        pos = 0
        

        while True:
            word = ""
            begin = tr_line.find(exp, pos)
            #not matching part
            if begin == -1:
                word = tr_line[pos:]
            else:
                word = tr_line[pos:begin]

            word = word.rstrip("\r\n")

            if word != "":
                lineobj.components.append(Component(word, False))

            #matching part
            if begin == -1:
                break

            lineobj.matchnum += 1
            word = tr_line[begin:begin+size].rstrip("\r\n")
            if word != "":
                lineobj.components.append(Component(word, True))

            pos = begin+size

        return lineobj


    def __sbuf_to_strings (self, sbuf_result):
        str_lineno = ""
        str_line = ""
        first = True
        
        for aux_lineno, aux_line in sbuf_result:
            if not first:
                str_lineno += "\n"
                str_line   += "\n"
            str_lineno += str(aux_lineno)
            str_line   +=     aux_line
            first = False
        return (str_lineno, str_line)
    
    def process_file(self, filename):
        """ processes a file. """
        cnt = 0
        lineno = 0

        sbuffer = SearchBuffer(self.options.get(Options.BEFORECONTEXT, 0), self.options.get(Options.AFTERCONTEXT, 0))
        
        if not self.must_be_visited(filename): return

        try:
            fd = open(filename)
        except:
            return

        anymatch = False
        for line in fd.readlines():
            if self.end: break
            lineno += 1
            new_matchs = self.__split_line(line, lineno)
            cnt += new_matchs.matchnum

            anymatch = anymatch or new_matchs > 0

            if sbuffer.append(new_matchs, new_matchs.matchnum > 0):
                list_to_show = sbuffer.get_and_clean()

                if list_to_show and self.line_callback:
                    self.line_callback(filename, list_to_show)
                    anymatch = False
                    
        #process last element if any

        if anymatch:
            list_to_show = sbuffer.get_and_clean()
            if list_to_show and self.line_callback:
                    self.line_callback(filename, list_to_show)

        if cnt and not self.end and self.file_callback:
            self.file_callback(filename, cnt, self)

        fd.close()
        self.processed_files+=1
        self.processed_file()
        
    def run(self):
        """ Main process. Walks over the files searching the string in EXP. """
        self.__compile()

        if self.options[Options.IGNORECASE]:
            self.__split_line = self.__split_line_ignorecase
        else:
            self.__split_line = self.__split_line_match
            
        for dirpath, dirnames, filelist in os.walk(self.dir):
            removelist = []
            for d in dirnames:
                if not self.must_be_visited(d):
                    removelist.append(d)
            for i in removelist:
                dirnames.remove(i)
            if self.end: break
            for filename in filelist:
                if self.end:break
                self.process_file(os.path.join(dirpath,filename))
        self.__del__()


class GrepEngine(SearchEngine):
    def __init__(self, options):
        super(GrepEngine, self).__init__(options)

        self.arguments   = "-Znr"

        # parse the options to add arguments for grep

        #aftercontext
        aux = options.get(Options.AFTERCONTEXT,1)
        if aux > 1:
            self.arguments += " -A%d"%aux

        #beforecontext
        aux = options.get(Options.BEFORECONTEXT,1)
        if aux > 1:
            self.arguments += " -B%d"%aux

        #ignorecase
        if options.get(Options.IGNORECASE, False):
            self.arguments += " -i"
        #whole word
        if options.get(Options.BYWORD, False):
            self.arguments += " -w"


    def add_exclusion_list(self, exclude):
        for i in exclude:
            self.arguments += " --exclude %s "%i

    def run(self):
        matching_line   = re.compile("^(.*)\0([0-9]+):(.*)$")
        contiguous_line = re.compile("^(.*)\0([0-9]+)-(.*)$")
        newfile_line    = re.compile("(--)")

        command = "grep %s '%s' '%s'"%(self.arguments, self.search_exp, self.dir)

        context = max(self.options.get(Options.AFTERCONTEXT, 0), self.options.get(Options.BEFORECONTEXT, 0)) > 0

        try:
            pin, pout = os.popen2 (command)
        except:
            print "ERROR: File/Directory %s could not be opened"%self.dir
            return

        cnt = 0
        last_file = None
        result = []
        for line in pout:
            m = matching_line.match(line)
            if m:
                filename, ln, sentence = m.groups()
                if last_file != filename:
                    if last_file != None:
                        if self.must_be_visited(last_file):
                            self.file_callback(last_file, cnt, None)
                            self.processed_file()
                    last_file = filename
                    cnt = 0
                                    
                cnt += 1

                if context:
                    result.append(Line(int(ln), 1, [Component(sentence, False)]))
                elif self.must_be_visited(filename):
                    self.line_callback(filename, [Line(int(ln), 1, [Component(sentence, False)])])
                continue

            m = contiguous_line.match(line)
            if m:
                filename, ln, sentence = m.groups()
                result.append(Line(int(ln), 0, [Component(sentence, False)]))
                continue

            m = newfile_line.match(line)
            if m:
                if last_file != None and self.must_be_visited(last_file):
                    self.line_callback (last_file, result)
                    
                result = []
            else:
                print "ERROR: string does not match. Maybe your grep app is too old or too new."
            
            continue

        if context and result and last_file != None and self.must_be_visited(last_file):
            self.file_callback(last_file, cnt, None)
            self.line_callback(last_file, result) 

        if not context and cnt and last_file:
            if self.must_be_visited(last_file):
                self.file_callback(last_file, cnt, None)
                self.processed_file()

        self.end_callback()


# MAIN
class PygrepGTK:
    def __init__(self, options):
        gtk.gdk.threads_init()

        self.xml = gtk.glade.XML(Paths.glade_dir('pygrep.glade'))
        self.xml.signal_autoconnect(self)
        
        self.__tab_dir_init()

        self.options = options

        self.model_files = None
        self.model_matches = None

        self.__general_init()
        self.__tab_search_init()
        self.__tab_history_init()

        self.status_bar = self.xml.get_widget("statusbar1")
        self.status_bar_msg = ""
        self.tip_bar = self.xml.get_widget("statusbar2")
        self.tip_bar_msg = ""
        
        self.threads = []

        self.threadsno = 0
        self.processed_files = 0

        self.initial_time = 0

        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

        self.profilesbox = self.ProfilesBox(self.xml, options.get(Options.PROFILE, None), self.save_options, self.load_options)
        gtk.main()

    def __notify (self):
        if self.status_bar_msg:
            self.status_bar.push(0, self.status_bar_msg)
        if self.tip_bar_msg:
            self.tip_bar.push(0,self.tip_bar_msg)
        self.status_bar_msg = ""
        self.tip_bar_msg = ""


    def notify (self, msg):
        self.status_bar_msg = msg
        gobject.idle_add(self.__notify)

    def notify_tip (self, msg):
        self.tip_bar_msg = msg
        gobject.idle_add(self.__notify)
    
    def on_window1_destroy(self, object):
        self.destroy()


    def __add_file(self, filename, cnt, search_obj):
        self.model_files.append([filename, cnt, os.path.basename(filename)])

    def add_file(self, filename, cnt, search_obj):
        gobject.idle_add(self.__add_file, filename, cnt, search_obj)

    def __add_line(self, filename, linevector):
        str_lineno = ""
        text = ""
        lineno = -1
        for lineobj in linevector:
            if str_lineno:
                str_lineno += "\n"
                text += "\n"
            if lineobj.matchnum > 0:
                text += "<i>"
                if lineno == -1:
                    lineno = lineobj.number
                    
            str_lineno += str(lineobj.number)
            for component in lineobj.components:
                string = unicode(Utilities.url_transformation(component.string), errors='ignore')
                if component.match:
                    text += "<b>" + string + "</b>"
                else:
                    text += string
            if lineobj.matchnum > 0:
                text += "</i>"
        self.model_matches.append([filename, lineno, str_lineno, text])
        
    def add_line(self, filename, lineobj):
        gobject.idle_add(self.__add_line, filename, lineobj)

    def endSearch(self):
        self.threadsno -= 1
        if self.threadsno <= 0:
            self.notify ("Search ended (%d files processed in %f seconds)"
                         %(self.processed_files, time.time()-self.initial_time))
            self.threadsno = 0
            self.threads = []
            self.processed_files = 0
            self.initial_time = 0

    def __create_search_object(self, exp, options):
        widget = self.xml.get_widget('radioSearchEngine')
        engine = widget.get_active()
        if engine == 1: # grep
            s = GrepEngine(options)
        else:
            s = PygrepEngine(options)

        s.search_exp = exp
        s.line_callback = self.add_line
        s.file_callback = self.add_file
        s.end_callback = self.endSearch
        s.processed_file = self.__add_processed_file
        
        self.initial_time = time.time()
        
        return s
    
    def __add_processed_file(self):
        self.processed_files+=1

    #search algorithm
    def search_dir(self, dirname, exp, options):
        # set the search tab
        notebook = self.xml.get_widget("notebook1")
        notebook.set_current_page(0)

        # create the thread
        s = self.__create_search_object(exp, options)
        s.dir = dirname
        self.threadsno += 1
        self.threads.append(s)
        s.start()

    def stop_threads(self):
        while len(self.threads):
            self.threads.pop().end = True

    def search(self, exp):
        self.stop_threads()
        self.notify ("Searching " + exp)
        #clean models
        self.model_matches.clear()
        self.model_files.clear()

        self.selected_filename = None

        self.options.reset()
        self.__gtk2options()

        self.table_dirs.model.foreach(lambda m,p,i:
                                      m.get_value(i, COL_ENABLE)
                                      and self.search_dir( m.get_value(i, COL_DIR), exp,
                                                           self.options))

    def search_on_model(self, model, column, pattern):
        for row in model:
            if model.get_value(row.iter, column) == pattern:
                return True
        return False
    
    # search tab
    def on_button_search_pressed (self, button):
        entry = self.xml.get_widget("entry_search_exp")
        text  = entry.get_text()
        
        if not (self.search_on_model( self.model_entry_search, COL_HIS_TEXT, text)):
            self.model_entry_search.append([False, text])
            
        self.search(text)
    

    def on_button_search_again_pressed(self, button):
        entry = self.xml.get_widget("entry_search_exp")
        exp = entry.get_text()

        if not (self.search_on_model( self.model_entry_search, COL_HIS_TEXT, exp)):
            self.model_entry_search.append([False, exp])
        
        filelist = []

        self.model_files.foreach(lambda m,p,i:
                                 filelist.append( m.get_value(i,COL_FILE)))

        self.notify ("Searching Again " + exp)

        #clean models
        self.model_matches.clear()
        self.model_files.clear()

        self.selected_filename = None

        s = self.__create_search_object(exp, options)
        for filename in filelist:
            s.process_file(filename)
        del (s)

        #search
        

        self.notify ("Search Again Ended")

    def on_button_search_clean_pressed (self, button):
        entry = self.xml.get_widget("entry_search_exp")
        entry.set_text("")


    def on_entry_search_exp_activate (self, entry):
        entry = self.xml.get_widget("entry_search_exp")
        text  = entry.get_text()

        if not (self.search_on_model( self.model_entry_search, 0, text)):
            self.model_entry_search.append([False, text])
            
        self.search(text)

    def __filter_entries(self, model, iter, data=None):
        value = model.get_value(iter, COL_FILE)
        return value == self.selected_filename

    def __general_init(self):
        entry = self.xml.get_widget("entry_search_exp")
        completion = gtk.EntryCompletion()
        entry.set_completion(completion)
        self.model_entry_search = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING)
        completion.set_model(self.model_entry_search)
        completion.set_text_column(COL_HIS_TEXT)

    def __tab_search_init(self):
        #set matching files defaults
        renderer = gtk.CellRendererText()
        
        treeview = self.xml.get_widget('treeview_matched_files')
        
        self.model_files = gtk.ListStore(str, str, str)
        self.model_matches = gtk.ListStore(str, str, str, str)

        treeview.set_model(self.model_files)
        self.model_files.clear()
        
        column = gtk.TreeViewColumn("#Matches", renderer, text=COL_CNT)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Filename", renderer, text=COL_FILENAME)
        column.set_sort_column_id(COL_FILENAME)
        treeview.append_column(column)
        treeview.set_search_column(2)
        column = gtk.TreeViewColumn("Path and file names", renderer, text=COL_FILE)
        column.set_sort_column_id(COL_FILE)
        treeview.append_column(column)
        
        #set matching lines defaults
        treeview = self.xml.get_widget('treeview_matches_list')

        column = gtk.TreeViewColumn("File", renderer, text=COL_FILE)
        column.set_sort_column_id(COL_FILE)
        column.set_visible(False)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Line", renderer, text=COL_LINE)
        column.set_sort_column_id(COL_LINE)
        column.set_visible(False)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Line", renderer, text=COL_LINETXT)
        column.set_sort_column_id(COL_LINETXT)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Text", renderer,  markup=COL_MARKED_TEXT)
        column.set_sort_column_id(COL_TEXT)
        treeview.append_column(column)

        # the model
        self.selected_filename = None
        self.treemodelfilter = self.model_matches.filter_new()
        self.treemodelfilter.set_visible_func(self.__filter_entries)

        treeview.set_model(self.treemodelfilter)


    def on_treeview_matched_files_cursor_changed(self, treeview):
        model, iter = treeview.get_selection().get_selected()
        self.selected_filename = model.get_value(iter, COL_FILE)
        self.treemodelfilter.refilter()



    def on_treeview_matches_list_cursor_changed (self, treeview):
        return
        model, iter = treeview.get_selection().get_selected()

    def __open_editor(self, filename, linenumber="1"):
        #get the command
        entry = self.xml.get_widget("entry_command")
        command = entry.get_text()

        sp_comm = command.split()

        #expand variables in command
        for i in xrange(len(sp_comm)):
            if "%F" in sp_comm[i]:
                sp_comm[i] = sp_comm[i].replace("%F", os.path.basename(filename))
            if "%P" in sp_comm[i]:
                sp_comm[i] = sp_comm[i].replace("%P", os.path.dirname(filename))
            if "%f" in sp_comm[i]:
                sp_comm[i] = sp_comm[i].replace("%f", filename)
            if "%l" in sp_comm[i]:
                sp_comm[i] = sp_comm[i].replace("%l", linenumber)
        self.notify("Launching " + string.join(sp_comm, ","))

        window = self.xml.get_widget("window1")
        if os.fork() == 0:
            window.set_accept_focus(True)
            os.execv (sp_comm[0], sp_comm)
            os.exit(0)

        if self.options.get(Options.MINIMIZEONLAUNCH, False):
            window.iconify()


    def on_treeview_matched_files_row_activated(self, treeview, path, treeviewcolumn):
        model, iter = treeview.get_selection().get_selected()
        self.__open_editor(model.get_value(iter, COL_FILE))


    def on_treeview_matches_list_row_activated (self, treeview, path, treeviewcolumn):
        model, iter = treeview.get_selection().get_selected()
        self.__open_editor(model.get_value(iter, COL_FILE), model.get_value(iter, COL_LINE))

    # dir tab
    class TableEnabledValues:
        """ Component that has a table with two columns: enabled/disabled and a text value.
        In addition, it will have two buttons: one for append values and one more to delete values.
        """
        def __init__(self, treeview, maincolumnname="", entryasociated=None, addButtonAssociated=None, delButtonAssociated=None):
            renderer = gtk.CellRendererText()
            self.treeview = treeview

            self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, str)
            self.treeview.set_model(self.model)

            rendererToggle = gtk.CellRendererToggle()
            rendererToggle.set_property("activatable", True)
            rendererToggle.connect('toggled', self.__toggle_button , self.model)
            column = gtk.TreeViewColumn("Enable", rendererToggle, active=0)
            column.set_sort_column_id(1)
            self.treeview.append_column(column)
            
            column = gtk.TreeViewColumn(maincolumnname, renderer, text=1)
            column.set_sort_column_id(0)
            self.treeview.append_column(column)

            # events and functions
            if entryasociated:
                self.entry = entryasociated
                self.treeview.connect("row_activated", self.on_tree_row_activated)

            if addButtonAssociated:
                self.addbutton = addButtonAssociated
                self.addbutton.connect("clicked", self.on_button_add)

            if delButtonAssociated:
                self.delbutton = delButtonAssociated
                self.delbutton.connect("clicked", self.on_button_del)

        def setListOfEnabledValues(self,listEV):
            self.model.clear()
            if not listEV:
                return
            for directory in listEV:
                self.model.append([directory.enabled, directory.str])

        def getValuesAsListOfEV(self, enableCol=0):
            """
            Gets the values model column as a list of Enabled String
            """
            retval = []
            self.model.foreach(
                lambda m, p, i:
                m.get_value(i, enableCol) and retval.append(EnabledString(m.get_value(i, column)))
                )
            return retval

        def getAllAsListOfEV(self):
            """
            Gets the values of the model as a list of duples of EnabledString
            """
            retval = []
            self.model.foreach(
                lambda m,p,i:
                retval.append( EnabledString(m[i][1], m[i][0]) )
                )
            return retval

        def __toggle_button (self, cell, path, model):
            model[path][COL_ENABLE] = not model[path][COL_ENABLE]
            return


        # signals
        def on_tree_row_activated (self, treeview, path, column):
            model, iter = treeview.get_selection().get_selected()
            self.entry.set_text(model.get_value(iter, COL_DIR))

        def on_button_add (self, button):
            text = self.entry.get_text().strip()
            if text:
                self.model.append([True, text])

        def on_button_del (self, button):
            self.treeview.get_selection().selected_foreach(lambda model,path,iter: model.remove(iter))



    def __tab_dir_init(self):
        self.table_dirs    = self.TableEnabledValues (self.xml.get_widget('dir_selection_tree'),
                                                      'Files/directories to search',
                                                      self.xml.get_widget('entry_directory'),
                                                      self.xml.get_widget('button_add_dir'),
                                                      self.xml.get_widget('button_del_dir'))
        self.table_include = self.TableEnabledValues (self.xml.get_widget('treeview_inclusion_patterns'),
                                                      'Patterns to search in', 
                                                      self.xml.get_widget('entry_inclusion'),
                                                      self.xml.get_widget('button_inclusion_add'),
                                                      self.xml.get_widget('button_inclusion_del'))
        self.table_exclude = self.TableEnabledValues (self.xml.get_widget('treeview_exclusion_patterns'),
                                                      'Patterns to ignore', 
                                                      self.xml.get_widget('entry_exclusion'),
                                                      self.xml.get_widget('button_exclusion_add'),
                                                      self.xml.get_widget('button_exclusion_del'))
        
    def __tab_history_init (self):
        treeview =  self.xml.get_widget('treeview_history')
        treeview.set_model(self.model_entry_search)
        rendererToggle = gtk.CellRendererToggle()
        column = gtk.TreeViewColumn("Save", rendererToggle, active=COL_HIS_SAVE)
        rendererToggle.connect('toggled', self.__toggle_button_save , self.model_entry_search)
        treeview.append_column(column)
        column = gtk.TreeViewColumn("Expresion", gtk.CellRendererText(), text=COL_HIS_TEXT)
        treeview.append_column(column)

    def __toggle_button_save (self, cell, path, model):
        model[path][COL_HIS_SAVE] = not model[path][COL_HIS_SAVE]
        return


    def __sel_dir (self, button):
        entry = self.xml.get_widget("entry_directory")
        entry.set_text(self.filew.get_filename())
        self.filew.destroy()
        self.filew = None
        
    def on_button_open_file_clicked (self, button):
        self.filew = gtk.FileSelection("File/Dir selection")

        # Connect the ok_button to file_ok_sel method
        self.filew.ok_button.connect("clicked", self.__sel_dir)
    
        # Connect the cancel_button to destroy the widget
        self.filew.cancel_button.connect("clicked",
                                    lambda w: self.filew.destroy())

        self.filew.show()

    def on_entry_size_limit_changed(self, entry):
        text = entry.get_text()
        res = ""
        for i in text:
            if i in "0123456789":
                res += i
        if text != res:
            entry.set_text(res)
        
    def on_entry_size_limit_insert_text(self, entry, text, length, args):
        for i in text:
            if not text in range(10):
                return False

    #options tab

    class ProfilesBox:
        def __init__(self, xml, current, save_options, load_options):
            self.xml       = xml
            self.current   = current
            self.save_options = save_options
            self.load_options = load_options
            
            self.dialog    = self.xml.get_widget("dialog_newprofile") 

            self.model     = gtk.ListStore(gobject.TYPE_STRING)

            self.__init_treeview()
            self.__init_combobox()
            self.__init_combobox_basedon()
            self.__init_signals()

            self.load_options(self.current)

        def __del__(self):
            self.save_options(self.current)
            fd = open (Paths.config_dir("initialconf"), "w+")
            if self.current:
                fd.write(self.current)
            fd.close()

        def __init_signals(self):
            button_new     = self.xml.get_widget("button_optionfile_new")
            button_new.connect("clicked", self.on_button_add)

            button_del     = self.xml.get_widget("button_optionfile_remove")
            button_del.connect("clicked", self.on_button_del)

            #dialog
            dialog_button_add    = self.xml.get_widget("button_profilenew_add")
            dialog_button_add.connect   ("clicked", self.on_button_profilenew_add_pressed)
            
            dialog_button_cancel = self.xml.get_widget("button_profilenew_cancel")
            dialog_button_cancel.connect("clicked", self.on_button_profilenew_cancel_pressed)

            self.combobox.connect("changed", self.on_combobox_profiles_changed)

        def __init_combobox(self):
            cell = gtk.CellRendererText()
            self.combobox = self.xml.get_widget("combobox_profiles")
            self.combobox.pack_start(cell, True)
            self.combobox.add_attribute(cell, 'text', 0)
            self.combobox.set_model(self.model)
            self.combobox.append_text(DEFAULTCONF)

            self.save_profile = True
            #load the current profile from file
            if self.current == None:
                if (os.access(Paths.config_dir("initialconf"), os.R_OK)):
                    fd = open (Paths.config_dir("initialconf"))
                    self.current = fd.readline()
                    fd.close()

            #load posible profiles
            try:
                for name in os.listdir(Paths.config_dir()):
                    if name[-4:] == ".cfg":
                        self.combobox.append_text(name[:-4])
                    if name[:-4] == self.current:
                        self.save_profile = False
                        self.combobox.set_active(len(self.model)-1)
            except:
                try:
                    os.mkdir (Paths.config_dir())
                except:
                    pass

            if self.combobox.get_active() == -1:
                self.combobox.set_active(0)


        def __init_combobox_basedon(self):
            cell = gtk.CellRendererText()
            self.combobox_basedon = self.xml.get_widget("combobox_basedon")
            self.combobox_basedon.pack_start(cell, True)
            self.combobox_basedon.add_attribute(cell, 'text', 0)
            self.combobox_basedon.set_model(self.model)
            self.combobox_basedon.set_active(0)

        def __init_treeview(self):
            self.treeview = self.xml.get_widget("treeview_profiles")
            self.treeview.set_model(self.model)
            column = gtk.TreeViewColumn("Profile Name", gtk.CellRendererText(), text=0)
            self.treeview.append_column(column)

        def on_button_add(self, button):
            self.dialog.show()

        def __delete_profile (self, dialog, value, selection):
            if value == -8:
                selection = self.treeview.get_selection()
                if not selection:
                    Utilities.gtkMessage(None, "Please, select the row to delete."%profilename)
                    return
                model, iter = selection.get_selected()
                profilename = model[iter][0]
                filename = profilename + ".cfg"
                try:
                    os.remove(Paths.config_dir(filename))
                    if self.combobox.get_active_iter() == iter:
                        Utilities.gtkMessage(None, "You cannot delete the selected profile")
                    else:
                        model.remove(iter)
                        Utilities.gtkMessage(None,"The profile '%s' was removed ok."%profilename)
                except:
                    Utilities.gtkMessage(None, "The profile '%s' could not be removed."%profilename)
    
            dialog.destroy()
                

        def on_button_del(self, button):
            selection = self.treeview.get_selection()
            if not selection:
                return
            model, index = selection.get_selected()
            if self.model[index][0] == self.current:
                Utilities.gtkMessage(None,
                                     "You cannot delete the current profile. Please, select another one to delete this")
                return

            dialog = gtk.MessageDialog(None,
                                    gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_INFO,
                                    gtk.BUTTONS_YES_NO,
                                    "The profile %s will be deleted forever. Are you sure?"%self.model[index][0])
            dialog.connect("response", self.__delete_profile, index)
      
            dialog.show()
    
    
        def on_button_profilenew_add_pressed(self, button):
            profile_name = self.xml.get_widget("entry_profilename")
            dialog = self.xml.get_widget("dialog_newprofile")
            if not profile_name.get_text():
                Utilities.gtkMessage(dialog, "The profile must have a name")
                return
    
            valid = True

            for i in profile_name.get_text():
                if not i.upper() in "_-ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890":
                    valid = False
                    break
            if not valid:
                Utilities.gtkMessage(dialog, "The profile name is not valid. Please, use only letters, numbers and symbols '-' and '_'.")
                return
            
            self.combobox.append_text(profile_name.get_text())
    
            self.save_options(self.current)
            self.load_options(self.model[self.combobox_basedon.get_active()][0])
            self.current = profile_name.get_text()
    
            self.combobox.set_active(len(self.model)-1)
            
            dialog.hide()
    
        def on_button_profilenew_cancel_pressed(self, button):
            self.dialog.hide()
            
        def on_combobox_profiles_changed (self, combobox):
            #save old
            optionfile = self.current
            if optionfile and optionfile != DEFAULTCONF and optionfile[:-4] != DEFAULTCONF and self.save_profile:
                self.save_options(self.current)
            self.save_profile = True

            #get new name
            new_option = self.model[combobox.get_active()][0]

            if new_option == DEFAULTCONF:
                self.current = None
            else:
                self.current = new_option

            #load new
            self.load_options(self.current)

    
    #history tab

    def on_treeview_history_row_activated(self, treeview, path, column):
        model, iter = treeview.get_selection().get_selected()
        entry = self.xml.get_widget("entry_search_exp")
        text = model.get_value(iter, COL_HIS_TEXT)
        entry.set_text(text)
        self.search(text)

    #about tab
    
    def on_notebook1_switch_page(self, notebook, gpointer, tab_number):
        NOTIFIES = ["Searchs Pannel", "Directories Selection", "Option Switcher", "Search History", "About Dialog"]
        self.notify_tip (NOTIFIES[tab_number])

    class About:
        def __init__(self):
            logo=gtk.gdk.pixbuf_new_from_file(Paths.glade_dir("logo2.svg"))
            
            about = gtk.AboutDialog()
            about.set_license(LICENSE)
            about.set_copyright(unicode(COPYRIGHT))
            about.set_website(WEBSITE)
            about.set_name("Pygrep " + VERSION)
            about.set_comments("Pygrep is a grep implementation with graphical GUI")
            about.set_authors(
                [u"Miguel Ángel García Martínez <miguelangel.garcia@gmail.com>",
                 "",
                 "CONTRIBUITORS",
                 u"Rubén Martínez",
                 u"Ángel Manuel Carcelén",
                 u"Karl Berry",
                 u"David Villa, for the Debian package"
                 ])
            about.set_artists([u"Sergio Camacho (brue)"])
            about.set_logo(logo)
            about.set_icon(logo)
            about.set_wrap_license(True)
            about.connect ("response", lambda d, r: d.destroy())
            about.connect ("close", self.on_destroy)
            about.connect ("destroy", self.on_destroy)
            about.show()

        def on_destroy(self, about):
            about.hide()
            del (about)
            del (self)
        
    def on_button_about_clicked(self, button):
        self.About()

    def destroy(self):
        self.stop_threads()
        self.profilesbox.__del__()
        gtk.main_quit()

    def __del__(self):
        self.destroy()

    #persistence
    def __options2gtk(self):
        widget = self.xml.get_widget("togglebutton_ignorecase")
        widget.set_active( self.options.get( Options.IGNORECASE, False ) )

        widget = self.xml.get_widget("togglebutton_wholeword")
        widget.set_active( self.options.get( Options.BYWORD, False ) )

        if self.options.has_key( Options.COMMAND ):
            widget = self.xml.get_widget("entry_command")
            widget.set_text(self.options[Options.COMMAND])

        widget = self.xml.get_widget("lines_before_match")
        widget.set_value( float( self.options.get(Options.BEFORECONTEXT, 0)))

        widget = self.xml.get_widget("lines_after_match")
        widget.set_value( float( self.options.get(Options.AFTERCONTEXT, 0)))

        self.table_dirs.setListOfEnabledValues   (self.options.directories)
        self.table_include.setListOfEnabledValues(self.options.get(Options.INCLUDE, []))
        self.table_exclude.setListOfEnabledValues(self.options.get(Options.EXCLUDE, []))

        widget = self.xml.get_widget("checkbutton_minimize")
        widget.set_active( self.options.get(Options.MINIMIZEONLAUNCH, False) )

        if self.options.has_key(Options.HISTORY):
            for item in self.options[Options.HISTORY]:
                self.model_entry_search.append ( [1, item] )


    def __gtk2options(self):
        widget = self.xml.get_widget("togglebutton_ignorecase")
        self.options[Options.IGNORECASE] = widget.get_active()

        widget = self.xml.get_widget("togglebutton_wholeword")
        self.options[Options.BYWORD] = widget.get_active()

        widget = self.xml.get_widget("entry_command")
        self.options[Options.COMMAND] = widget.get_text()

        widget = self.xml.get_widget("lines_before_match")
        self.options[Options.BEFORECONTEXT] = int(widget.get_value())

        widget = self.xml.get_widget("lines_after_match")
        self.options[Options.AFTERCONTEXT] = int(widget.get_value())

        if not self.options.has_key(Options.INCLUDE):
            self.options[Options.INCLUDE] = []
        if not self.options.has_key(Options.EXCLUDE):
            self.options[Options.EXCLUDE] = []
        self.options.directories.extend(self.table_dirs.getAllAsListOfEV())
        self.options[Options.INCLUDE].extend(self.table_include.getAllAsListOfEV())
        self.options[Options.EXCLUDE].extend(self.table_exclude.getAllAsListOfEV())

        widget = self.xml.get_widget("checkbutton_minimize")
        self.options[Options.MINIMIZEONLAUNCH] = widget.get_active()

        if not self.options.has_key(Options.HISTORY):
            self.options[Options.HISTORY] = []
        for row in self.model_entry_search:
            if row[COL_HIS_SAVE]:
                self.options[Options.HISTORY].append ( row[COL_HIS_TEXT] )
        

    def save_options(self, profile):
        self.options.reset()

        self.__gtk2options()

        p = Persistence(self.options)
        p.save_options(profile)
        del(p)

    def load_options(self, profile):
        self.options.reset()
            
        p = Persistence(self.options)
        p.load_options(profile)
        del(p)

        self.__options2gtk()



class Options:
    PROFILE         = "pygrep_profile"
    IGNORECASE      = "ignore_case"
    AFTERCONTEXT    = "after_context"
    BEFORECONTEXT   = "before_context"
    REGEXP          = "basic_expresion"
    ENGINE          = "pygrep_engine"
    INCLUDE         = "pygrep_include"
    EXCLUDE         = "pygrep_exclude"
    INCLUDEDISABLED = "include_disabled"
    EXCLUDEDISABLED = "exclude_disabled"
    COMMAND         = "pygrep_command"
    BYWORD          = "search_by_word"
    MINIMIZEONLAUNCH= "minimize_on_launch"
    HISTORY         = "history"
 
    def __init__(self):
        self.options     = {}
        self.directories = []

        self.__setitem__ = self.options.__setitem__
        self.__getitem__ = self.options.__getitem__
        self.get         = self.options.get
        self.pop         = self.options.pop
        self.has_key     = self.options.has_key

    def reset(self):
        self.options.clear()
        while len(self.directories): self.directories.pop()

    def values2options (self, valuesobj):
        deny = dir(optparse.Values)

        for varname in dir(valuesobj):
            if varname in deny:
                continue
            if varname in [self.INCLUDE, self.EXCLUDE]:
                value = eval("valuesobj."+varname)
                if value:
                    self.options[varname] = EnabledString(value.split(","), True)
                continue
            self.options[varname] = eval("valuesobj."+varname)
            

    def error (self, errstr):
        pos = errstr.rfind('-')
        if pos==-1:
            self.default_error(errstr)
            return
        try:
            val = int(errstr[pos+1:])
            if val:
                self.options[self.AFTERCONTEXT]  = val
                self.options[self.BEFORECONTEXT] = val
        except:
            self.default_error(errstr)
            return
            
    
    def parse_args (self):
        parser = OptionParser(usage="usage: %prog [options] [dir1 dir2 ...] [file1 file2 ...]",
                              version="    %s %s by %s"%("%prog",VERSION, AUTHORS),
                              description="Pygrep is a grep like tool app with GUI.\nBugs, queries and pieces of pizza, refer %s"%WEBSITE
                              )

        self.default_error = parser.error
        parser.error = self.error

        # GENERIC OPTIONS

        parser.add_option ("-i", "--ignore-case",       action="store_true", default=None,
                           help="ignore case distinctions.")
        parser.add_option (      "--pygrep-profile",    action="store",      default=None,
                           help="Selects a profile.")
        parser.add_option (      "--pygrep-include",    action="store",      default=None,
                           help="Comma separated include rules. Usually, file patterns (*.h, *,c, ...).")
        parser.add_option (      "--pygrep-exclude",    action="store",      default=None,
                           help="Comma separated exclude rules. Usually, directory patterns (CVS, .svn, ...).")
        # GREP OPTIONS
        
        grep_options = OptionGroup(parser, "GREP", "Options valid only for grep engine.")
        parser.add_option_group(grep_options)
        grep_options.add_option("-G", "--basic-regexp",
                                help="Interpret the pattern as a basic regular expression")
        grep_options.add_option("-E", "--extended-regexp",
                                help="Interpret the pattern as a extended regular expression")

        # PYGREP OPTIONS
        
        pygrep_options = OptionGroup(parser, "PYGREP", "Options valid only for pygrep engine.")
        parser.add_option_group(pygrep_options)

        # GUI OPTIONS

        gui_options = OptionGroup(parser, "GUI", "Graphical User Interface preferences")
        parser.add_option_group(gui_options)

        gui_options.add_option (      "--pygrep-psyco",      action="store_true", default=None,
                                      help="Use 'psyco' lib (faster)")
        gui_options.add_option (      "--pygrep-engine",     action="store",      default=None,
                                      help="Selects Engine to use (pygrep, grep)")
        gui_options.add_option (      "--pygrep-command",    action="store",      default=None,
                                      help="Command to execute when a file or a line is selected.")

        # PARSE

        options, self.directories = parser.parse_args()

        self.values2options(options)

        del options

    def save (self):
        p = Persistence(self)
        p.save()
        del (p)

    def load (self):
        p = Persistence (self)
        p.load()
        del(p)
    
    def __str__(self):
        return str(self.options)
        return str(self.options) + " - " + reduce (lambda x,y: str(x) + "," + str(y.str), self.directories)
        
if __name__ == "__main__":
    options = Options()
    options.parse_args()

    if False and options.psycolib:
        try:
            import psyco
            #        psyco.log()
            psyco.full()
            #        psyco.profile(0.2, memory=100)
        except ImportError:
            print "Install python-psyco to use this feature."

    PygrepGTK(options)
