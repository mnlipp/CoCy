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
from circuits.core.handlers import handler
from circuits.web.servers import BaseServer
from circuits_bricks.web import ScopeDispatcher, ScopedChannel
from circuits.web.controllers import BaseController, expose
from circuits.core.events import Event
from circuits.core.utils import findroot, flatten
from cocy.upnp.ssdp import SSDPTranceiver
from cocy.providers import Provider
import anydbm
import os
from xml.etree.ElementTree import Element, QName, SubElement
from cocy.upnp import UPNP_CONTROL_NS
from circuits.web.errors import httperror
from cocy.soaplib import ns_soap_env
from cocy.misc import buildSoapResponse
import logging
from circuits_bricks.app.logger import log


class device_available(Event):
    pass
    

class device_unavailable(Event):
    pass


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

        # Build a web (HTTP) server for handling requests. This is
        # the server that will be announced by SSDP, so it has
        # no fixed port number.
        self.web_server = BaseServer(("", 0), channel="upnp-web").register(self)
        # Dispatcher for "/upnp-web".
        disp = ScopeDispatcher(channel="upnp-web").register(self.web_server)
        # Dummy root controller prevents requests for nested resources
        # from failing.
        DummyRoot().register(disp)
        
        # Initially empty list of providers
        self._devices = []
        
        # The configuration id, incremented every time the 
        # configuration changes
        self.config_id = 1
        
        # Open the database for uuid persistence 
        try:
            # Some people encounter problems on some boxes when opening 
            # the db file
            self._uuid_db = anydbm.open(os.path.join(path, 'upnp_uuids'), 'c')
        except:
            self.fire(log(logging.WARN, "Could not determine type db type of "
                          + os.path.join(path, 'upnp_uuids')))
            try:
                os.remove(os.path.join(path, 'upnp_uuids'))
                self._uuid_db = anydbm.open \
                    (os.path.join(path, 'upnp_uuids'), 'c')
            except:
                self.fire(log(logging.WARN, "Giving up on "
                          + os.path.join(path, 'upnp_uuids')))
                

    def register(self, parent):
        super(UPnPDeviceServer, self).register(parent)
        # SSDP transceiver, may exist only once
        if not any([isinstance(c, SSDPTranceiver) \
                    for c in flatten(findroot(self))]):
            SSDPTranceiver().register(self.parent)
        return self

    @handler("registered", channel="*")
    def _on_registered(self, component, manager):
        if not isinstance(component, Provider):
            return
        from cocy.upnp.adapters.adapter import UPnPDeviceAdapter
        device = UPnPDeviceAdapter(self, component, self.config_id, \
                                   self._uuid_db, self.web_server.port)
        if not device.valid:
            return
        device.register(self)
        self._devices.append(device)
        if self._started:
            self.fireEvent(device_available(device))

    @handler("unregister")
    def _on_unregister(self, component, manager):
        if not isinstance(component, Provider):
            return
        

    @handler("started", channel="application")
    def _on_started (self, component):
        self._started = True
        for device in self._devices:
            self.fireEvent(device_available(device))

    @handler("stopped", channel="*", priority=100, filter=True)
    def _on_stopped(self, event, component):
        if not self._started:
            return
        self._started = False
        for device in self._devices:
            self.fireEvent(device_unavailable(device))
        self._uuid_db.close()
        self.fireEvent(event)
        return True

    @property
    def providers(self):
        return [device.provider for device in getattr(self, "_devices", [])]


class UPnPError(httperror):

    _error_descs = { 401: "Invalid Action",
                     402: "Invalid Args",
                     501: "Action Failed",
                     600: "Argument Value Invalid",
                     601: "Argument Value Out of Range",
                     602: "Optional Action Not Implemented",
                     603: "Out of Memory",
                     604: "Human Intervention Required",
                     605: "String Argument Too Long"}
    
    def __init__(self, request, response, error_code, error_desc = None):
        super(UPnPError, self).__init__(request, response, 500)
        if error_desc is None:
            error_desc = self._error_descs.get(error_code, "Unknown")
        result = Element(QName(ns_soap_env, "Fault"))
        SubElement(result, QName(ns_soap_env, "faultcode")).text \
            = str(QName(ns_soap_env, "Client"))
        SubElement(result, QName(ns_soap_env, "faultstring")).text \
            = "UPnPError"
        detail = SubElement(result, "detail")
        upnp_error = SubElement(detail, QName(UPNP_CONTROL_NS, "UPnPError"))
        SubElement(upnp_error, QName(UPNP_CONTROL_NS, "errorCode")).text \
            = str(error_code)
        SubElement(upnp_error, QName(UPNP_CONTROL_NS, "errorDescription")) \
            .text = error_desc
        self._fault = buildSoapResponse(self.response, result)
    
    def __str__(self):
        return self._fault 


class DummyRoot(BaseController):
    
    channel = ScopedChannel("upnp-web", "/")
    
    @expose("f3c3G5")
    def index(self):
        return "Hello"
    

