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
from circuits.core.components import BaseComponent
from circuits.core.handlers import handler
from circuitsx.net.sockets import UDPMCastServer
import os
from circuits.io.events import Write
import platform
from socket import gethostname, gethostbyname
import time
from circuits.core.timers import Timer

SSDP_PORT = 1900
SSDP_ADDR = '239.255.255.250'

SSDP_SCHEMAS = "urn:schemas-upnp-org"
SSDP_DEVICE_SCHEMA = "urn:schemas-upnp-org:device-1-0"

class SSDPServer(BaseComponent):
    '''The SSDP protocol server component
    '''

    channel = "ssdp"

    def __init__(self, web_server_port, **kwargs):
        '''
        Constructor
        '''
        kwargs.setdefault("channel", self.channel)
        super(SSDPServer, self).__init__(**kwargs)

        self._config_id = None
 
        # Our associated SSDP message sender
        SSDPSender(web_server_port).register(self)
        
        # 
        self._server = UDPMCastServer((SSDP_ADDR, SSDP_PORT),
                                     **kwargs).register(self)
        self._server.setTTL(2)


class SSDPSender(BaseComponent):
    '''The SSDP Protocol sender component
    '''

    channel = "ssdp"
    _template_dir = os.path.join(os.path.dirname(__file__), "templates")
    _template_cache = {}
    _message_env = {}
    _message_expiry = 1800
    _boot_id = int(time.time())

    def __init__(self, web_server_port, channel=channel):
        '''
        Constructor
        '''
        super(SSDPSender, self).__init__(channel=channel)
        self.web_server_port = web_server_port

        # Setup the common entries in the dictionary that will be usd to
        # fill the UPnP templates.
        self._message_env['BOOTID'] = self._boot_id
        self._message_env['SERVER'] \
            = (platform.system() + '/' + platform.release()
               + " UPnP/1.1 cocy/0.1")
        self._message_env['CACHE-CONTROL'] = self._message_expiry
        self.hostaddr = gethostbyname(gethostname())
        if self.hostaddr.startswith("127.") and not "." in gethostname():
            try:
                self.hostaddr = gethostbyname(gethostname() + ".")
            except:
                pass
        
    def _get_template(self, name):
        if self._template_cache.has_key(name):
            return self._template_cache[name]
        file = open(os.path.join(self._template_dir, name))
        template = file.read()
        self._template_cache[name] = template
        return template

    @handler("device_available")
    def _on_device_available(self, event, upnp_device):
        self._message_env['CONFIGID'] = upnp_device.config_id
        self._send_notify(upnp_device, "available", root_device=True)
        event.times_sent = getattr(event, 'times_sent', 0) + 1
        if event.times_sent < 3:
            Timer(0.25, event, event.channel[1]).register(self)
   
    @handler("device_unavailable")
    def _on_device_unavailable(self, event, upnp_device):
        self._message_env['CONFIGID'] = upnp_device.config_id
        self._send_notify(upnp_device, "unavailable", root_device=True)
   
    def _send_notify(self, upnp_device, type,
                     root_device = False, embedded_device = False):
        self._message_env['LOCATION'] = "http://" + self.hostaddr + ":" \
            + str(self.web_server_port) + "/" + upnp_device.uuid \
            + "/description.xml"
        template = "notify-%s" % type
        # There is an extra announcement for root devices
        if root_device:
            self._message_env['NT'] = 'upnp:rootdevice'
            self._message_env['USN'] \
                = 'uuid:' + upnp_device.uuid + '::upnp:rootdevice'
            self._send_template(template, self._message_env)
        # Ordinary device announcement
        if root_device or embedded_device:
            self._message_env['NT'] = 'uuid:' + upnp_device.uuid
            self._message_env['USN'] = 'uuid:' + upnp_device.uuid
            self._send_template(template, self._message_env)
        # Common announcement
        self._message_env['NT'] \
            = SSDP_SCHEMAS + ":device:" + upnp_device.type_ver
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + "::" + self._message_env['NT']
        self._send_template(template, self._message_env)
        
    def _send_template(self, templateName, data):
        template = self._get_template(templateName)
        message = template % data
        headers = ""
        for line in message.splitlines():
            headers = headers + line + "\r\n"
        headers = headers + "\r\n"
        self.fireEvent(Write((SSDP_ADDR, SSDP_PORT), headers))

