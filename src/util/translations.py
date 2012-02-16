"""
..
   This file is part of the CoCy program.
   Copyright (C) 2012 Michael N. Lipp
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. codeauthor:: mnl
"""

class Translations(object):

    def __init__(self, fp):
        self._translations = self._parse(fp)
        
    def _parse(self, fp):
        res = dict()
        key = ""
        value = ""
        escaped = False
        have_key = False
        skip_ws = True
        pending_ws = ""
        ignore_comment = False
        while True:
            line = fp.readline()
            if line == "": # EOF
                if key != "": # Save pending key/value
                    res[key] = value
                break;
            skip_ws = True # Always skip ws at beginning of line
            for c in line:
                if c == '\t' or c == '\f': # Map to white space
                    c = ' '
                if skip_ws:
                    if c == ' ':
                        continue
                    else:
                        skip_ws = False # Found first non ws character
                        if not ignore_comment: # i.e. continuation
                            if c == '#' or c == '!':
                                break
                    ignore_comment = False
                if c == '\r':
                    continue
                if escaped:
                    escaped = False
                    if c == '\n':
                        ignore_comment = True
                        continue
                else:
                    if c == " ":
                        pending_ws += " "
                        continue
                    if c == '\\':
                        escaped = True
                        continue
                    if c == ':' or c == "=":
                        have_key = True
                        pending_ws = ""
                        skip_ws = True
                        continue
                    if c == '\n':
                        if key != "":
                            res[key] = value
                            key = ""
                            value = ""
                            have_key = False
                        break
                if not have_key:
                    key += (pending_ws + c)
                else:
                    value += (pending_ws + c)
                pending_ws = ""

        return res
