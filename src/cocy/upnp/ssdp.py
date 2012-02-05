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
from circuitsx.net.sockets import UDPMCastServer
import os
from circuits.io.events import Write
import platform
from socket import gethostname, gethostbyname
import time
from circuits.core.timers import Timer
from cocy.upnp import SSDP_ADDR, SSDP_PORT, SSDP_SCHEMAS
import datetime
from util.compquery import ComponentQuery
from circuits.core.events import Event
from circuits.web.controllers import Controller

class SSDPTranceiver(BaseComponent):
    '''The SSDP protocol server component
    '''

    channel = "ssdp"

    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        kwargs.setdefault("channel", self.channel)
        super(SSDPTranceiver, self).__init__(**kwargs)

        # The underlying network connection, used by both the sender
        # and the receiver 
        self._server = UDPMCastServer((SSDP_ADDR, SSDP_PORT),
                                     **kwargs).register(self)
        self._server.setTTL(2)

        # Our associated SSDP message sender
        SSDPSender().register(self)
        
        # Our associated SSDP message receiver
        SSDPReceiver().register(self)



class SSDPSender(BaseComponent):
    '''The SSDP Protocol sender component
    '''

    channel = "ssdp"
    _template_dir = os.path.join(os.path.dirname(__file__), "templates")
    _template_cache = {}
    _message_env = {}
    _message_expiry = 1800
    _boot_id = int(time.time())
    _timers = dict()

    def __init__(self, channel=channel):
        '''
        Constructor
        '''
        super(SSDPSender, self).__init__(channel=channel)

        # Setup the common entries in the dictionary that will be usd to
        # fill the UPnP templates.
        self._message_env['BOOTID'] = self._boot_id
        self._message_env['SERVER'] \
            = (platform.system() + '/' + platform.release()
               + " UPnP/1.1 CoCy/0.1")
        self.hostaddr = gethostbyname(gethostname())
        if self.hostaddr.startswith("127.") and not "." in gethostname():
            try:
                self.hostaddr = gethostbyname(gethostname() + ".")
            except:
                pass

    @handler("config_value", channel="configuration")
    def _on_config_value(self, section, option, value):
        if not section == "upnp":
            return
        if option == "max-age":
            self._message_expiry = int(value)

    @handler("mgmt_controller_query")
    def _on_controller_query(self):
        return Controller()

    @handler("device_available", channel="upnp")
    def _on_device_available(self, event, upnp_device):
        self._update_message_env(upnp_device)
        self._send_device_messages(upnp_device, "available")
        # Service announcements
        for service in upnp_device.services:
            self._send_service_message(upnp_device, service, "available")
        # Handle repeats
        if getattr(event, 'times_sent', 0) < 3:
            self._timers[upnp_device.uuid] \
                = Timer(0.25, event, event.channel[1]).register(self)
            event.times_sent = getattr(event, 'times_sent', 0) + 1
        else:
            self._timers[upnp_device.uuid] \
                = Timer(self._message_expiry / 4,
                        event, event.channel[1]).register(self)
   
    @handler("device_unavailable", channel="upnp")
    def _on_device_unavailable(self, event, upnp_device):
        if self._timers.has_key(upnp_device.uuid):
            self._timers[upnp_device.uuid].unregister()
            del self._timers[upnp_device.uuid]
        self._update_message_env(upnp_device)
        self._send_device_messages(upnp_device, "unavailable")
        # Service announcements
        for service in upnp_device.services:
            self._send_service_message(upnp_device, service, "unavailable")
   
    @handler("device_match")
    def _on_device_match(self, upnp_device, inquirer, search_target):
        if search_target == "ssdp:all":
            self._update_message_env(upnp_device)
            self._send_device_messages(upnp_device, "result", inquirer)
        else:
            self._update_message_env(upnp_device)
            if search_target == "upnp:rootdevice":
                self._send_root_message(upnp_device, "notify-result", inquirer)
            elif search_target.startswith("uuid:"):
                self._send_uuid_message(upnp_device, "notify-result", inquirer)
            elif search_target.startswith("urn:"):
                self._send_type_message(upnp_device, "notify-result", inquirer)
            
    def _update_message_env(self, upnp_device):
        self._message_env['CACHE-CONTROL'] = self._message_expiry
        self._message_env['CONFIGID'] = upnp_device.config_id
        self._message_env['DATE'] \
            = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        self._message_env['LOCATION'] = "http://" + self.hostaddr + ":" \
            + str(upnp_device.web_server_port) + "/" + upnp_device.uuid \
            + "/description.xml"
        
    def _send_device_messages(self, upnp_device, type, 
                              to=(SSDP_ADDR, SSDP_PORT)):
        template = "notify-%s" % type
        # There is an extra announcement for root devices
        if upnp_device.root_device:
            self._send_root_message(upnp_device, template, to)
        # Device UUID announcement
        self._send_uuid_message(upnp_device, template, to)
        # Device type announcement
        self._send_type_message(upnp_device, template, to)
        
    def _send_root_message(self, upnp_device, template, 
                           to=(SSDP_ADDR, SSDP_PORT)):
        self._message_env['NT'] = 'upnp:rootdevice'
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + '::upnp:rootdevice'
        self._send_template(template, self._message_env, to)

    def _send_uuid_message(self, upnp_device, template, 
                           to=(SSDP_ADDR, SSDP_PORT)):
        self._message_env['NT'] = 'uuid:' + upnp_device.uuid
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid
        self._send_template(template, self._message_env, to)

    def _send_type_message(self, upnp_device, template, 
                           to=(SSDP_ADDR, SSDP_PORT)):
        self._message_env['NT'] = SSDP_SCHEMAS + ":device:" \
            + upnp_device.type_ver
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + "::" + self._message_env['NT']
        self._send_template(template, self._message_env, to)

    def _send_service_message(self, upnp_device, service, type, \
                              to=(SSDP_ADDR, SSDP_PORT)):
        template = "notify-%s" % type
        self._message_env['NT'] = SSDP_SCHEMAS + ":service:" \
            + service.type_ver
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + "::" + self._message_env['NT']
        self._send_template(template, self._message_env, to)
        
    def _send_template(self, templateName, data, to=(SSDP_ADDR, SSDP_PORT)):
        template = self._get_template(templateName)
        message = template % data
        headers = ""
        for line in message.splitlines():
            headers = headers + line + "\r\n"
        headers = headers + "\r\n"
        self.fireEvent(Write(to, headers))
                    
    def _get_template(self, name):
        if self._template_cache.has_key(name):
            return self._template_cache[name]
        file = open(os.path.join(self._template_dir, name))
        template = file.read()
        self._template_cache[name] = template
        return template


class DeviceAvailable(Event):
    name = "device_available"
    

class DeviceUnavailable(Event):
    name = "device_unavailable"
    

class UPnPDeviceMatch(Event):
    name = "device_match"
    
    def __init__(self, component, inquirer, search_target):
        super(UPnPDeviceMatch, self)\
            .__init__(component, inquirer, search_target)


class UPnPDeviceQuery(ComponentQuery):
    
    def __init__(self, query_function, inquirer, search_target):
        super(UPnPDeviceQuery, self).__init__(query_function)
        self.name = super(UPnPDeviceQuery, self).name
        self._inquirer = inquirer
        self._search_target = search_target

    def decide(self, component):
        res = super(UPnPDeviceQuery, self).decide(component)
        if res != None:
            component.fire(UPnPDeviceMatch(component, self._inquirer, \
                                           self._search_target), "ssdp")

class UPnPDeviceNotification(Event):
    
    channel = "device_notification"
    
    def __init__(self, location, notification_type, max_age, server, usn):
        super(UPnPDeviceNotification, self).__init__()
        self.location = location
        self.type = notification_type
        self.max_age = max_age
        self.server = server
        self.usn = usn

class SSDPReceiver(BaseComponent):

    channel = "ssdp"

    def __init__(self, channel = channel):
        super(SSDPReceiver, self).__init__(channel=channel)

    @handler("read")
    def _on_read(self, address, data):
        lines = data.splitlines()
        if lines[0].startswith("M-SEARCH "):
            search_target = None
            for line in lines[1:len(lines)-1]:
                if not line.startswith("ST:"):
                    continue
                search_target = line.split(':', 1)[1].strip()
                f = lambda dev: True
                # TODO: add criteria
                if search_target == "upnp:rootdevice":
                    f = lambda dev: dev.root_device
                self.fire(UPnPDeviceQuery(f, address, search_target), "upnp")                        
                return
        elif lines[0].startswith("NOTIFY "):
            location = None
            max_age = None
            notification_type = None
            server = None
            usn = None
            for line in lines[1:]:
                if line.startswith("CACHE-CONTROL:"):
                    s = line.split(":", 1)[1].strip()
                    max_age = s.split("=", 1)[1].strip()
                elif line.startswith("LOCATION:"):
                    location = line.split(":", 1)[1].strip()
                elif line.startswith("NT:"):
                    notification_type = line.split(":", 1)[1].strip()
                elif line.startswith("SERVER:"):
                    server = line.split(":", 1)[1].strip()
                elif line.startswith("USN:"):
                    usn = line.split(":", 1)[1].strip()
            self.fire(UPnPDeviceNotification(location, notification_type, 
                                             max_age, server, usn), "upnp")
