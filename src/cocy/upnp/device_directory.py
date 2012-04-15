"""
..
   This file is part of the CoCy program.
   Copyright (C) 2012 Michael N. Lipp
   
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
from cocy.upnp.ssdp import SSDPTranceiver, UPnPSearchRequest, UPnPDeviceByeBye
from circuits.core.utils import findroot, flatten
from cocy.upnp import UPNP_ROOTDEVICE, SSDP_DEVICE_SCHEMA
from circuits_bricks.web import Client
from circuits.web.client import Request
import httplib
from xml.etree.ElementTree import XML
from circuits.core.timers import Timer

class UPnPDeviceDirectory(BaseComponent):

    channel = "upnp"

    def __init__(self, *args, **kwargs):
        super(UPnPDeviceDirectory, self).__init__(*args, **kwargs)
        self.fire(UPnPSearchRequest(), "ssdp")

    @handler("upnp_device_alive")
    def _on_device_alive \
        (self, location, notification_type, max_age, server, usn):
        if notification_type == UPNP_ROOTDEVICE:
            if not any(map(lambda c: isinstance(c, UPnPRootDevice) \
                           and c.usn == usn, self.components.copy())):
                UPnPRootDevice(location, max_age, usn).register(self)

    def register(self, parent):
        super(UPnPDeviceDirectory, self).register(parent)
        # SSDP transceiver, may exist only once
        if not any([isinstance(c, SSDPTranceiver) \
                    for c in flatten(findroot(self))]):
            SSDPTranceiver().register(self.parent)
        return self

    @property
    def devices(self):
        return filter(lambda c: isinstance(c, UPnPRootDevice) \
                      and c.ready, self.components.copy())


class UPnPRootDevice(BaseComponent):

    def __init__(self, location, max_age, usn):
        super(UPnPRootDevice, self).__init__()
        self._location = location
        self._usn = usn
        self._ready = False
        self._comm_chan = "client." + usn
        self._client = Client(location, channel=self._comm_chan).register(self)
        @handler("response", channel=self._comm_chan)
        def _on_response(self, response):
            if response.status == httplib.OK:
                self._initialize(response.read())
        self.addHandler(_on_response)
        self.fire(Request("GET", location), self._client)
        self._expiry_timer \
            = Timer(max_age, UPnPDeviceByeBye(usn), "upnp").register(self)

    def _initialize(self, xml_src):
        data = XML(xml_src)
        self._friendly_name = data.findtext \
            ("{%s}device/{%s}friendlyName" \
             % (SSDP_DEVICE_SCHEMA, SSDP_DEVICE_SCHEMA))
        self._ready = True

    @handler("upnp_device_alive")
    def _on_device_alive \
        (self, location, notification_type, max_age, server, usn):
        if usn == self._usn:
            self._expiry_timer.interval = max_age
            self._expiry_timer.reset()

    @handler("upnp_device_bye_bye", channel="upnp")
    def _on_device_bye_bye (self, usn):
        if usn == self._usn:
            self.unregister()

    @property
    def usn(self):
        return self._usn
        
    @property
    def location(self):
        return self._location

    @property
    def ready(self):
        return self._ready

    @property
    def friendly_name(self):
        return self._friendly_name
    