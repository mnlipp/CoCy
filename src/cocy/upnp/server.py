"""
.. codeauthor:: mnl
"""
from circuits.core.components import BaseComponent
from cocy.upnp.services import UPnPService
from cocy.upnp.devices import UPnPDevice
from circuits.core.handlers import handler
from circuits.core.events import Event
from circuits.web.servers import BaseServer
from circuitsx.web.dispatchers.dispatcher import ScopeDispatcher
from circuitsx.web.dispatchers.serverscopes import ServerScopes
from circuits.web.controllers import BaseController, expose
from cocy.upnp.ssdp import SSDPServer

class DeviceAlive(Event):
    channel = "device-alive"

class UPnPDeviceServer(BaseComponent):
    """
    The component that implements the UPnP device server.
    """
    channel = "upnp"
    
    def __init__(self, channel=channel):
        '''
        Constructor
        '''
        super(UPnPDeviceServer, self).__init__(channel=channel)
        
        # Create and register all service components
        self._service_types = {}
        service = UPnPService("SwitchPower", 1).register(self)
        self._service_types[service.type_ver] = service

        # Build a web (HTTP) server for handling requests. This is
        # the server that will be used in announcements, so it has
        # no fixed port number.
        self.web_server = BaseServer(("", 0), channel="upnp-web").register(self)
        # All requests will be prefixed with "/upnp-web/".
        ServerScopes(channel="upnp-web").register(self.web_server)
        # Dispatcher for "/upnp-web".
        disp = ScopeDispatcher(channel="upnp-web").register(self.web_server)
        # Dummy root controller
        DummyRoot().register(disp)
        
        # SSDP server. Needs to know the port used by the web server
        SSDPServer(self.web_server.port).register(self)

    @handler("provider_list")
    def _on_provider_list(self, config_id, providers):
        for provider in providers:
            upnp_device = None
            new_device = False
            for c in provider.components:
                if isinstance(c, UPnPDevice):
                    upnp_device = c
            if not upnp_device:
                upnp_device = UPnPDevice(provider, config_id, \
                    self._service_types).register(provider)
                new_device = True
            if not upnp_device.valid:
                return
            if new_device:
                self.fireEvent(DeviceAlive(upnp_device), target="ssdp")


class DummyRoot(BaseController):
    channel = "/upnp-web"
    
    @expose("index", target = "/upnp-web")
    def index(self):
        return ""
    
