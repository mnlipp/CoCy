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
from cocy.core.configuration import ConfigurationMonitor
from cocy.samples.binary_light.misc import BinaryLight

class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, handler=None):
        sys.exit();

class Root(Controller):

    def index(self):
        return "Hello World!"


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
 
    manager = Manager()
    ErrorHandler().register(manager)
    ConfigurationMonitor().register(manager)
    web_server = BaseServer(("", 8000)).register(manager)
    #disp = ScopedDispatcher().register(web_server)
    #Root().register(disp)
    UPnPDeviceServer().register(manager)
    Debugger().register(manager)
    SOAP().register(manager)
    
    BinaryLight().register(manager)
    
    from circuits.tools import graph
    print graph(manager)
    manager.run()
