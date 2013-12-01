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


import os
import sys
import subprocess
import shlex
import unittest

from pygrep.searchbuffer import Line
from pygrep.searchbuffer import Token
from pygrep.searchbuffer import SearchBuffer

THIS_PATH = os.path.dirname(__file__)


__PATTERN_where_1before__ = [
"""pattern of such abuse occurs in the area of products for individuals to
use, which is precisely [where] it is most unacceptable.  Therefore, we""",
"""    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying [where] to find the""",
"""    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers [where] the object code and Corresponding""",
"""additional terms that apply to those files, or a notice indicating
[where] to find the applicable terms.""",
"""state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to [where] the full notice is found."""
]

__PATTERN_where_1before_2after__ = [
"""pattern of such abuse occurs in the area of products for individuals to
use, which is precisely [where] it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we""",
"""    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying [where] to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is""",
"""    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers [where] the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.""",
"""additional terms that apply to those files, or a notice indicating
[where] to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the""",
"""state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to [where] the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>"""
]


__PATTERN_where__ = [
"""pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we""",
"""    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is""",
"""    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.""",
"""additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the""",
"""state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>"""
]

__PATTERN_additional__ = [
"""    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.""",
"""Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you""",
"""    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further""",
"""  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the""",
"""to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

"""]

__PATTERN_whynot__ = [
"""the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<http://www.gnu.org/philosophy/why-not-lgpl.html>.
"""]


class  TesterSearchbufferTestCase(unittest.TestCase):
    """
    Test class for SearchBuffer
    """
    # def setUp(self):
    #     """Builds the arrays to test. Tests will be made with GPL v3"""

    #def tearDown(self):
    #    self.foo.dispose()
    #    self.foo = None
    TESTING_FILE = os.path.join(THIS_PATH, 'data', 'COPYING')

    def test_token1 (self):
        """ Tests if a token is equal to another """
        self.assertEqual (Token ("token", True), Token ("token", True),
            "Tokens must be equals")
        self.assertEqual (Token ("token", False), Token ("token", False),
            "Tokens must be equals")

        self.assertNotEqual(Token ("token1", True), Token ("token2", True),
            "Tokens must not be equals")
        self.assertNotEqual(Token ("token", True), Token ("token", False),
            "Tokens must not be equals")

    def test_line1 (self):
        """ Test if a line is equal to another """
        line1 = Line (0)
        line2 = Line (0)
        line3 = Line (0)
        line4 = Line (0)

        line1.append (Token ("token", True))
        line2.append (Token ("token", True))
        line3.append (Token ("diferent", True))
        line4.append (Token ("token", True))
        line4.append (Token ("token", True))

        self.assertEqual(line1, line2,
            "Lines must be equal: '%s' => '%s'" % (line1, line2))
        self.assertNotEqual(line1, line3,
            "Lines must not be equal: '%s' => '%s'" % (line1, line3))
        self.assertNotEqual(line2, line3,
            "Lines must not be equal: '%s' => '%s'" % (line2, line3))
        self.assertNotEqual(line1, line4,
            "Lines must not be equal: '%s' => '%s'" % (line1, line4))
        self.assertNotEqual(line2, line4,
            "Lines must not be equal: '%s' => '%s'" % (line2, line4))

    @staticmethod
    def __create_line ( textline, pattern):
        """ Creates a Line object from a string and a pattern. """
        splitted = textline.rstrip().split(pattern)
        line = Line (0)
        for j in range(len (splitted)):
            text = splitted[j]
            line.append (Token (text, False))
            if (j != len(splitted) -1):
                line.append (Token (pattern, True))
        return line

    def __compare_grep_output ( self, pattern):
        """ Searchs for a pattern and compares with "grep" output """
        grep_cmd = 'grep "{pattern}" "{filename}"'.format(
            pattern=pattern.replace (".", "\\."),
            filename=self.TESTING_FILE,
        )
        out, err, rc = self.__execute(grep_cmd)
        result = out.splitlines()
        sbuffer = SearchBuffer ()
        filed = open (self.TESTING_FILE)
        i = 0
        for textline in filed:
            line = self.__create_line(textline, pattern)

            if sbuffer.append (line):
                # all lines in listOfMatchs must be in sbuffer
                for line in sbuffer.get():
                    resultline = self.__create_line ( result[i],
                                                                pattern)
                    self.assertEqual(line, resultline,
                        "Lines must be equal: '%s' => '%s'" %
                        (line, resultline))
                    i += 1


        filed.close ()


    def __execute(self, command):
        p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return (stdout, stderr, p.wait())

    def test_basic1 (self):
        """ Searchs for "software" and compares with "grep" output """
        self.__compare_grep_output("software")

    def test_basic2 (self):
        """ Searchs for "the" and compares with "grep" output """
        self.__compare_grep_output("the")
        
    def test_basic3 (self):
        """ Searchs for " " and compares with "grep" output """
        self.__compare_grep_output(" ")

    def test_before1 ( self ):
        """ Search for "where" in code, but with 1 before """
        sbuffer = SearchBuffer ()
        sbuffer.max_prev = 1
        filed = open (self.TESTING_FILE)
        i = 0
        patterns = __PATTERN_where_1before__
        for textline in filed:
            line = self.__create_line(textline, "where")

            if sbuffer.append (line):
                # all lines in listOfMatchs must be in sb
                resultline = ""
                for token in sbuffer.get():
                    resultline +=  token.__str__() + "\n"
                self.assertEqual(patterns[i], resultline[:-1],
                    "Lines must be equal:\n'%s'\n => \n'%s'" %
                    (patterns[i], resultline[:-1]))
                i += 1
                

        filed.close ()

    def test_before1_after2 ( self ):
        """ Search for "where" in code, but with 1 before and 2 after"""
        sbuffer = SearchBuffer ()
        sbuffer.max_prev = 1
        sbuffer.max_next = 2
        filed = open (self.TESTING_FILE)
        i = 0
        patterns = __PATTERN_where_1before_2after__
        for textline in filed:
            line = self.__create_line(textline, "where")

            if sbuffer.append (line):
                # all lines in listOfMatchs must be in sb
                resultline = ""
                for token in sbuffer.get():
                    resultline +=  token.__str__() + "\n"
                self.assertEqual(patterns[i], resultline[:-1],
                    "Lines must be equal:\n'%s'\n => \n'%s'" %
                    (patterns[i], resultline[:-1]))
                i += 1


        filed.close ()

def suite():
    """ Test Suite """
    tlr = unittest.TestLoader ()
    suitesearchbuffer = tlr.loadTestsFromTestCase (TesterSearchbufferTestCase)

    return unittest.TestSuite ([suitesearchbuffer])


if __name__ == '__main__':
    _runner = unittest.TextTestRunner ()
    _runner.run (suite())
    
    #unittest.main()

