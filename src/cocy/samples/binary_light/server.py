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
from circuits.core.manager import Manager
from circuits.core.debugger import Debugger
from circuitsx.web.dispatchers.soap import SOAP
from circuits.core.components import Component
import sys
from circuits.web.events import Request
from circuits.web.controllers import Controller
from circuits.web.servers import BaseServer
from cocy.upnp.server import UPnPDeviceManager
from cocy.samples.binary_light.misc import BinaryLight
import os
from util.application import Application

class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, handler=None):
        sys.exit();

class Root(Controller):

    def index(self):
        return "Hello World!"

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
}


if __name__ == '__main__':

    # Fix circuits problems
    _orig_fireEvent = Manager.fireEvent
    def _fix_fired_request (self, event, channel=None, target=None):
        if isinstance(event, Request) \
            and not getattr(event, "_has_been_fixed", False):
            event.success = "request_success", self.channel
            event.failure = "request_failure", self.channel
            event.filter = "request_filtered", self.channel
            event.start = "request_started", self.channel
            event.end = "request_completed", self.channel
            event._has_been_fixed = True
        return _orig_fireEvent (self, event, channel, target)
    Manager.fireEvent = _fix_fired_request
    Manager.fire = Manager.fireEvent
 
    application = Application("CoCy", CONFIG)
    ErrorHandler().register(application)
    web_server = BaseServer(("", 8000)).register(application)
    #disp = ScopedDispatcher().register(web_server)
    #Root().register(disp)
    
    UPnPDeviceManager(application.app_dir).register(application)
    Debugger().register(application)
    SOAP().register(application)
    
    BinaryLight().register(application)
    
    from circuits.tools import graph
    print graph(application)
    application.run()
