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
from circuits.core.components import BaseComponent
from cocy.upnp.service import UPnPService
from cocy.upnp.device import UPnPDeviceAdapter
from cocy.upnp.ssdp import DeviceAvailable, DeviceUnavailable
from circuits.core.handlers import handler
from circuits.web.servers import BaseServer
from circuitsx.web.dispatchers.dispatcher import ScopeDispatcher, ScopedChannel
from circuits.web.controllers import BaseController, expose, Controller
from cocy.upnp.ssdp import SSDPTranceiver
from cocy.providers import Provider
import anydbm
import os

class UPnPDeviceServer(BaseComponent):
    """
    This component keeps track of the :class:`cocy.providers.Provider` 
    instances and creates or removes the corresponding 
    :class:`cocy.upnp.device.UPnPDeviceAdapter` components.
    
    Notifications are sent when a new device is added 
    (:class:`cocy.upnp.ssdp.DeviceAvailable`) or removed
    (:class:`cocy.upnp.ssdp.DeviceUnavailable`)
    """
    channel = "upnp"
    
    def __init__(self, path, channel=channel):
        super(UPnPDeviceServer, self).__init__(channel=channel)
        self._started = False

        # Create and register all known service component types
        self._service_types = {}
        service = UPnPService("SwitchPower", 1).register(self)
        self._service_types[service.type_ver] = service

        # Build a web (HTTP) server for handling requests. This is
        # the server that will be announced by SSDP, so it has
        # no fixed port number.
        self.web_server = BaseServer(("", 0), channel="upnp-web").register(self)
        # Dispatcher for "/upnp-web".
        disp = ScopeDispatcher(channel="upnp-web").register(self.web_server)
        # Dummy root controller prevents requests for nested resources
        # from failing.
        DummyRoot().register(disp)
        
        # SSDP server. Needs to know the port used by the web server
        # for announcements
        SSDPTranceiver().register(self)
        
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
        device = UPnPDeviceAdapter(component, self.config_id, \
                   self._uuid_db, self._service_types, \
                   self.web_server.port).register(self)
        if not device.valid:
            return
        self._devices.append(device)
        if self._started:
            self.fireEvent(DeviceAvailable(device))

    @handler("unregister")
    def _on_unregister(self, component, manager):
        if not isinstance(component, Provider):
            return
        

    @handler("started", channel="application")
    def _on_started (self, component):
        self._started = True
        for device in self._devices:
            self.fireEvent(DeviceAvailable(device))

    @handler("stopped", channel="*", priority=100, filter=True)
    def _on_stopped(self, event, component):
        if not self._started:
            return
        self._started = False
        for device in self._devices:
            self.fireEvent(DeviceUnavailable(device))
        self._uuid_db.close()
        self.fireEvent(event)
        return True

class DummyRoot(Controller):
    
    channel = ScopedChannel("upnp-web", "/")
    
    def index(self):
        return ""
    
