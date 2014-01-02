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
"""
import platform

SSDP_PORT = 1900
SSDP_ADDR = '239.255.255.250'

SSDP_SCHEMAS = "urn:schemas-upnp-org"
SSDP_DEVICE_SCHEMA = "urn:schemas-upnp-org:device-1-0"
UPNP_SERVICE_SCHEMA = "urn:schemas-upnp-org:service-1-0"
UPNP_ROOTDEVICE = "upnp:rootdevice"
UPNP_SERVICE_ID_PREFIX = "urn:upnp-org:serviceId:"
UPNP_CONTROL_NS = "urn:schemas-upnp-org:control-1-0"
UPNP_EVENT_NS = "urn:schemas-upnp-org:event-1-0"
UPNP_METADATA_NS = "urn:schemas-upnp-org:metadata-1-0/upnp/"
UPNP_AVT_EVENT_NS = "urn:schemas-upnp-org:metadata-1-0/AVT/"
UPNP_RCS_EVENT_NS = "urn:schemas-upnp-org:metadata-1-0/RCS/"
DIDL_LITE_NS = "urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"

COCY_SERVICE_EXT = "urn:cocy-service-ext"

SERVER_HELLO = (platform.system() + '/' + platform.release()
                + " UPnP/1.1 CoCy/0.1")

from .device_server import UPnPDeviceServer
from .adapters.adapter import UPnPDeviceAdapter
from .ssdp import SSDPTranceiver

__all__ = ["SSDP_PORT", "SSDP_ADDR", "SSDP_SCHEMAS",
           "SSDP_DEVICE_SCHEMA", "UPNP_SERVICE_ID_PREFIX", 
           "UPnPDeviceServer", "SSDPTranceiver"
]
