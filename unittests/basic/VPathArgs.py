"""
..
   This file is part of the CoCy program.
   Copyright (C) 2011 Michael N. Lipp
   
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
from circuits.web.servers import BaseServer
from circuits import Debugger
from circuits.web import Dispatcher
from circuits.web.controllers import BaseController, expose
from circuits.core.manager import Manager
from unittest import TestCase
from urllib2 import urlopen

class Root(BaseController):

    @expose("test.txt")
    def index(self):
        return "Hello world!"

class Leaf(BaseController):

    channel = "/test"

    @expose("test.txt")
    def index(self, vpath = None):
        if vpath == None:
            return "Hello world!"
        else:
            return "Hello world! " + vpath

class TestVPathArgs(TestCase):

    def test_access(self):
        self.manager = Manager()
        Debugger().register(self.manager)
    
        self.server = BaseServer(("localhost", 8000)) 
        self.server.register(self.manager);
        Dispatcher().register(self.server)
        Root().register(self.manager)
        Leaf().register(self.manager)
    
        self.manager.start()

        f = urlopen(self.server.base + "/test.txt")
        s = f.read()
        self.assertEqual(s, b"Hello world!")

        f = urlopen(self.server.base + "/test/test.txt")
        s = f.read()
        self.assertEqual(s, b"Hello world!")

        self.manager.stop()
