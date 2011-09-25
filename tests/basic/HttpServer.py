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
"""
.. codeauthor:: mnl
"""

from circuits import Debugger
from circuits.web import Server, Controller
from circuits.core.handlers import handler
from circuits.core.manager import Manager
from circuitsx.web.dispatchers.soap import SOAP

class SayHello(Controller):
    
    channel = "/SayHello"

    def index(self):
        self.response.headers['Content-Type'] = 'text/xml'
        body = self.request.body.read()
        from soaplib.soap import from_soap
        payload, header = from_soap(body, 'ascii')
        return "Du"

class SubDir(Controller):
    
    channel = "/hallo"
    
    def du(self):
        request = self.request
        return "Du"

    def da(self):
        return "da"

class Root(Controller):

    def index(self):
        return "Hello World!"

if __name__ == '__main__':
    manager = Manager()
    server = Server(("localhost", 8000), ssl=False, certfile="cert.pem") 
    server.register(manager);
    Debugger().register(manager)
    Root().register(manager)
    SubDir().register(manager)
    SayHello().register(manager)
    #SOAP().register(manager)
    from circuits.tools import graph
    print graph(manager)
    # (server + Debugger() + Root() + SubDir() + SayHello()).run()
    manager.run()
    pass