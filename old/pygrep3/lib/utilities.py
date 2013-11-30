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

""" Some generic utilities """

import weakref
import os

MAGIC_LOADED = None
try:
    import magic
    MAGIC_LOADED = magic.open ( magic.MAGIC_NONE )
    MAGIC_LOADED.load ()
except ImportError:
    pass


def get_file_type ( filepath ):
    """ Gets the type of a file if possible. Else, returns the extension """
    if MAGIC_LOADED:
        try:
            return MAGIC_LOADED.file ( filepath )
        except IOError:
            pass
        except Exception:
            pass
    return os.path.splitext ( filepath ) [1]




# This class has been originally taken from TwinPanel:
#  http://twinpanel.blogspot.com/
class Singleton(type):
    """ Singleton Pattern """
    def __init__ ( mcs, name, bases, dct ):
        mcs.__instance = None
        type.__init__ ( mcs, name, bases, dct )

    def __call__( mcs, *args, **kw ):
        if mcs.__instance is None:
            mcs.__instance = type.__call__ ( mcs, *args, **kw )
        return weakref.proxy ( mcs.__instance )

    def loaded ( mcs ):
        """ Checks if the class has been loaded """
        return mcs.__instance != None


# This class has been originally taken from TwinPanel:
#http://twinpanel.blogspot.com/
class Observable ( object ):
    """Multi-observable for multi topic observers"""

    class NotSuchTopic(Exception):
        """ Exception when the topic does not exist """
        pass
    class NotSuchObserver(Exception):
        """ Exception when the observer does not exist """
        pass
    class TopicAlreadyExists(Exception):
        """ Exception when the topic already exist """
        pass

    def __init__(self, topics=[] ):
        self._observers = {None:[]}

        assert isinstance(topics, list)
        for i in topics:
            self.add_topic(i)

    def attach(self, obj, topic=None):
        """ Attach an object of a topic """
        try:
            self._observers[topic].append(obj)
        except KeyError:
            raise self.NotSuchTopic(topic)

    def detach(self, obj, topic=None):
        """ Detach an object of a topic """
        try:
            self._observers[topic].remove(obj)
        except KeyError:
            raise self.NotSuchTopic(topic)
        except ValueError:
            raise self.NotSuchObserver(obj)


    def notify(self, val=None, topic=None):
        """ notifies an event to all subscriptors """
        if topic not in self._observers.keys():
            raise self.NotSuchTopic(topic)

        for obj in self._observers[topic]:
            obj (val)


    def add_topic(self, name=None):
        """ Adds a topic """
        if name in self._observers.keys():
            raise self.TopicAlreadyExists(name)

        self._observers[name] = []
