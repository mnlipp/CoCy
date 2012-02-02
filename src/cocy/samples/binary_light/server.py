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
from circuits.core.debugger import Debugger
from circuits.core.components import Component
import sys
from circuits.web.controllers import Controller
from circuits.web.servers import BaseServer
from cocy.upnp import UPnPDeviceServer
from cocy.samples.binary_light.misc import BinaryLight
import os
from util.application import Application
from circuitsx.web.dispatchers.dispatcher import ScopeDispatcher, ScopedChannel
from circuitsx import fix_circuits
from util.mgmtui import MgmtControllerQuery
from circuits.core.handlers import handler

CONFIG = {
    "logging": {
        "type": "TimedRotatingFile",
        "file": os.path.join("%(log_dir)s", "application.log"),
        "when": "midnight",
        "backupCount": 7,
        "level": "DEBUG",
    },
    "upnp": {
        "max-age": "1800",
    },
    "ui": {
        "port": "8877",
    },
}

class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, handler=None):
        sys.exit();

class UI(BaseServer):

    class Root(Controller):

        channel = ScopedChannel("ui", "/")

        def index(self):
            return "Hello World!"

    def __init__(self, port):
        super(UI, self).__init__(("", port), channel="ui")
        # Dispatcher for "/ui".
        ScopeDispatcher(channel="ui").register(self)
        # Root page
        UI.Root().register(self);
        self.fireEvent(MgmtControllerQuery())
        
    @handler("mgmt_controller_query", priority=-999)
    def _on_controllers(self, event):
        result = event.value.value 
        if result == None:
            return
        if not isinstance(result, list):
            result = [result]
        pass

if __name__ == '__main__':

    fix_circuits()
 
    application = Application("CoCy", CONFIG)
    ErrorHandler().register(application)
    # Build a web (HTTP) server for handling user interface requests.
    port = int(application.config.get("ui", "port", 0))
    UI(port).register(application)
    
    upnp_dev_server \
        = UPnPDeviceServer(application.app_dir).register(application)
    Debugger().register(application)
    # SOAP().register(application)
    
    BinaryLight().register(application)
    
    from circuits.tools import graph
    print graph(application)
    application.run()
