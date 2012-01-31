# This file is part of the CoCy program.
# Copyright (C) 2011 Michael N. Lipp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from circuitsx.web.dispatchers.dispatcher import ScopeDispatcher, ScopedChannel
from circuits.web.servers import BaseServer
from circuitsx import fix_circuits
"""
.. codeauthor:: mnl
"""

from circuits import Debugger
from circuits.web.controllers import BaseController, expose, Controller
from circuits.core.manager import Manager

class Root1(BaseController):

    @expose("index", target = ScopedChannel("site1", "/"))
    def index(self):
        return "Hello from site 1"

class Root2(Controller):

    channel = ScopedChannel("site2", "/")

    def index(self):
        return "Hello from site 2!"

if __name__ == '__main__':
    fix_circuits()
    manager = Manager()
    Debugger().register(manager)
    
    server1 = BaseServer(("localhost", 8000), channel="site1") 
    server1.register(manager);
    ScopeDispatcher(channel="site1").register(server1)
    Root1().register(manager)
    
    server2 = BaseServer(("localhost", 8001), channel="site2") 
    server2.register(manager);
    ScopeDispatcher(channel="site2").register(server2)
    Root2().register(manager)
    
    
    #SOAP().register(manager)
    from circuits.tools import graph
    print graph(manager)
    # (server + Debugger() + Root() + SubDir() + SayHello()).run()
    manager.run()
    pass