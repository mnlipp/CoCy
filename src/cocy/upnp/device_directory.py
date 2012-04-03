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
from cocy.upnp.ssdp import SSDPTranceiver
from circuits.core.utils import findroot, flatten

class UPnPDeviceDirectory(BaseComponent):

    channel = "upnp"

    def __init__(self, *args, **kwargs):
        super(UPnPDeviceDirectory, self).__init__(*args, **kwargs)
        self._devices = {}
        
    @handler("upnp_device_notification")
    def device_notification \
        (self, location, notification_type, max_age, server, usn):
        if not self._devices.has_key(location):
            self._devices[location] = UPnPRootDevice(location)

    def register(self, parent):
        super(UPnPDeviceDirectory, self).register(parent)
        # SSDP transceiver, may exist only once
        if not any([isinstance(c, SSDPTranceiver) \
                    for c in flatten(findroot(self))]):
            SSDPTranceiver().register(self.parent)
        return self


class UPnPRootDevice(BaseComponent):

    def __init__(self, location):
        super(UPnPRootDevice, self).__init__()
        self._location = location
        
    @property
    def location(self):
        return self._location

