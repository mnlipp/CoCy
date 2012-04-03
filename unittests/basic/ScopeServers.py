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
from circuits_bricks.web import ScopeDispatcher, ScopedChannel
from circuits.web.servers import BaseServer
from circuits import Debugger
from circuits.web.controllers import BaseController, expose, Controller
from circuits.core.manager import Manager
from unittest import TestCase
from urllib2 import urlopen

class Root1(BaseController):

    @expose("index", channel = ScopedChannel("site1", "/"))
    def index(self):
        return "Hello from site 1!"

class Root2(Controller):

    channel = ScopedChannel("site2", "/")

    def index(self):
        return "Hello from site 2!"

class TestScopedServers(TestCase):
    
    def setUp(self):
        self.manager = Manager()
        # Debugger().register(self.manager)
    
        self.server1 = BaseServer(("localhost", 8000), channel="site1") 
        self.server1.register(self.manager);
        ScopeDispatcher(channel="site1").register(self.server1)
        Root1().register(self.manager)
    
        self.server2 = BaseServer(("localhost", 8001), channel="site2") 
        self.server2.register(self.manager);
        ScopeDispatcher(channel="site2").register(self.server2)
        Root2().register(self.manager)
    
        self.manager.start()

    def tearDown(self):
        self.manager.stop()

    def test_access(self):
        f = urlopen(self.server1.base)
        s = f.read()
        self.assertEqual(s, b"Hello from site 1!")

        f = urlopen(self.server2.base)
        s = f.read()
        self.assertEqual(s, b"Hello from site 2!")
