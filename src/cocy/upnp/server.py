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
from cocy.providers import Provider
import anydbm
import os

class DeviceAvailable(Event):
    channel = "device_available"
    
class DeviceUnavailable(Event):
    channel = "device_unavailable"
    
class UPnPDeviceServer(BaseComponent):
    """
    This component keeps track of the :class:`cocy.providers.Provider` 
    instances and creates or removes the corresponding 
    :class:`cocy.upnp.devices.UPnPDevice` components.
    
    Notifications are sent when a new device is added 
    (:class:`cocy.upnp.server.DeviceAvailable`) or removed
    (:class:`cocy.upnp.server.DeviceUnavailable`)
    """
    channel = "upnp"
    
    def __init__(self, path, channel=channel):
        super(UPnPDeviceServer, self).__init__(channel=channel)
        self._started = False
        
        # Create and register all service components
        self._service_types = {}
        service = UPnPService("SwitchPower", 1).register(self)
        self._service_types[service.type_ver] = service

        # Build a web (HTTP) server for handling requests. This is
        # the server that will be announced by SSDP, so it has
        # no fixed port number.
        self.web_server = BaseServer(("", 0), channel="upnp-web").register(self)
        # All requests to the server will be prefixed with "/upnp-web/".
        ServerScopes(channel="upnp-web").register(self.web_server)
        # Dispatcher for "/upnp-web".
        disp = ScopeDispatcher(channel="upnp-web").register(self.web_server)
        # Dummy root controller prevents requests for nested resources
        # from failing.
        DummyRoot().register(disp)
        
        # SSDP server. Needs to know the port used by the web server
        # for announcements
        SSDPServer(self.web_server.port).register(self)
        
        # Initially empty list of providers
        self._devices = []
        
        # The configuration id, incremented every time the 
        # configuration changes
        self.config_id = 1
        
        # Open the database for uuid persistence 
        self._uuid_db = anydbm.open(os.path.join(path, 'upnp_uuids'), 'c')

    @handler("registered")
    def _on_registered(self, component, manager):
        if not isinstance(component, Provider):
            return
        device = UPnPDevice(component, self.config_id, \
                   self._uuid_db, self._service_types).register(self)
        if not device.valid:
            return
        self._devices.append(device)
        if self._started:
            self.fireEvent(DeviceAvailable(device), target="ssdp")

    @handler("unregister")
    def _on_unregister(self, component, manager):
        if not isinstance(component, Provider):
            return
        

    @handler("started")
    def _on_started (self, component, mode):
        self._started = True
        for device in self._devices:
            self.fireEvent(DeviceAvailable(device), target="ssdp")

    @handler("stopped", target="*", priority=100, filter=True)
    def _on_stopped(self, event, component):
        if not self._started:
            return
        self._started = False
        for device in self._devices:
            self.fireEvent(DeviceUnavailable(device), target="ssdp")
        self._uuid_db.close()
        self.fireEvent(event)
        return True

class DummyRoot(BaseController):
    channel = "/upnp-web"
    
    @expose("index", target = "/upnp-web")
    def index(self):
        return ""
    
