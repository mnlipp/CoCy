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
from cocy.upnp.server import UPnPDeviceServer
from cocy.samples.binary_light.misc import BinaryLight
import os
from util.config import Configuration
from util.application import Application

class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, handler=None):
        sys.exit();

class Root(Controller):

    def index(self):
        return "Hello World!"

CONFIG = {
    "logging": {
        "type": "file",
        "file": os.path.join("%(config_dir)s", "application.log"),
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
    
    UPnPDeviceServer(application.config_dir).register(application)
    Debugger().register(application)
    SOAP().register(application)
    
    BinaryLight().register(application)
    
    from circuits.tools import graph
    print graph(application)
    application.run()
