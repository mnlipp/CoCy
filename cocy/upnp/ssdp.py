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
from circuits_bricks.net.sockets import UDPMCastServer
import os
from circuits.io.events import write
from socket import gethostname, gethostbyname
import time
from circuits_bricks.core.timers import Timer
from cocy.upnp import SSDP_ADDR, SSDP_PORT, SSDP_SCHEMAS, UPNP_ROOTDEVICE,\
    SERVER_HELLO
from circuits_bricks.misc import component_query
from circuits.core.events import Event
from circuits.web.controllers import Controller
from email.utils import formatdate
from circuits_bricks.app.logger import log
import logging


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
        self._message_env['SERVER'] = SERVER_HELLO
        try:
            self.hostaddr = gethostbyname(gethostname())
            if self.hostaddr.startswith("127.") and not "." in gethostname():
                try:
                    self.hostaddr = gethostbyname(gethostname() + ".")
                except:
                    pass
        except Exception as e:
            self.fire(log(logging.ERROR, "Failed to get host address: %s(%s)" \
                          % (type(e), str(e))),
                      "logger")
            

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
                = Timer(0.25, event, *event.channels).register(self)
            event.times_sent = getattr(event, 'times_sent', 0) + 1
        else:
            self._timers[upnp_device.uuid] \
                = Timer(self._message_expiry / 4,
                        event, *event.channels).register(self)
   
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
   
    @handler("upnp_device_match")
    def _on_device_match(self, upnp_device, inquirer, search_target):
        self._update_message_env(upnp_device)
        if search_target == "ssdp:all":
            self._send_device_messages(upnp_device, "result", inquirer)
        else:
            if search_target == "upnp:rootdevice":
                self._send_root_message(upnp_device, "notify-result", inquirer)
            elif search_target.startswith("uuid:"):
                self._send_uuid_message(upnp_device, "notify-result", inquirer)
            elif search_target.startswith(SSDP_SCHEMAS + ":device:"):
                self._send_device_message \
                    (upnp_device, "notify-result", inquirer)
            elif search_target.startswith(SSDP_SCHEMAS + ":service:"):
                for service in upnp_device.services:
                    if not search_target.startswith \
                        (SSDP_SCHEMAS + ":service:" + service.type + ":"):
                        continue
                    self._send_service_message \
                        (upnp_device, service, "result", inquirer)
            
    @handler("upnp_search_request")
    def _on_search_request(self, event, search_target=UPNP_ROOTDEVICE, mx=1):
        self._send_template("m-search-request", 
                            { "ST": search_target, "MX": mx })
        # Handle repeats
        if getattr(event, 'times_sent', 0) < 3:
            Timer(mx, event, *event.channels).register(self)
            event.times_sent = getattr(event, 'times_sent', 0) + 1
            
    def _update_message_env(self, upnp_device):
        self._message_env['CACHE-CONTROL'] = self._message_expiry
        self._message_env['CONFIGID'] = upnp_device.config_id
        self._message_env['DATE'] = formatdate(usegmt=True)
        self._message_env['LOCATION'] = "http://" + self.hostaddr + ":" \
            + str(upnp_device.web_server_port) + "/" + upnp_device.uuid \
            + "/description.xml"
        
    def _send_device_messages(self, upnp_device, msg_type, 
                              to=(SSDP_ADDR, SSDP_PORT)):
        template = "notify-%s" % msg_type
        # There is an extra announcement for root devices
        if upnp_device.root_device:
            self._send_root_message(upnp_device, template, to)
        # Device UUID announcement
        self._send_uuid_message(upnp_device, template, to)
        # Device type announcement
        self._send_device_message(upnp_device, template, to)
        
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

    def _send_device_message(self, upnp_device, template, 
                           to=(SSDP_ADDR, SSDP_PORT)):
        self._message_env['NT'] = SSDP_SCHEMAS + ":device:" \
            + upnp_device.type_ver
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + "::" + self._message_env['NT']
        self._send_template(template, self._message_env, to)

    def _send_service_message(self, upnp_device, service, msg_type, \
                              to=(SSDP_ADDR, SSDP_PORT)):
        template = "notify-%s" % msg_type
        self._message_env['NT'] = SSDP_SCHEMAS + ":service:" \
            + service.type_ver
        self._message_env['USN'] = 'uuid:' + upnp_device.uuid \
            + "::" + self._message_env['NT']
        self._send_template(template, self._message_env, to)
        
    def _send_template(self, template_name, data, to=(SSDP_ADDR, SSDP_PORT)):
        template = self._get_template(template_name)
        message = template % data
        headers = ""
        for line in message.splitlines():
            headers = headers + line + "\r\n"
        headers += "\r\n"
        self.fireEvent(write(to, headers))
                    
    def _get_template(self, name):
        if self._template_cache.has_key(name):
            return self._template_cache[name]
        template_file = open(os.path.join(self._template_dir, name))
        template = template_file.read()
        self._template_cache[name] = template
        return template


class upnp_device_match(Event):
    
    def __init__(self, component, inquirer, search_target):
        super(upnp_device_match, self)\
            .__init__(component, inquirer, search_target)


class upnp_device_query(component_query):
    
    def __init__(self, query_function, inquirer, search_target):
        super(upnp_device_query, self).__init__(query_function)
        self.name = super(upnp_device_query, self).name
        self._inquirer = inquirer
        self._search_target = search_target

    def decide(self, component):
        res = super(upnp_device_query, self).decide(component)
        if res != None:
            component.fire(upnp_device_match(component, self._inquirer, \
                                           self._search_target), "ssdp")

class upnp_device_alive(Event):
    
    def __init__(self, location, notification_type, max_age, server, usn):
        super(upnp_device_alive, self).__init__ \
            (location, notification_type, max_age, server, usn)
        self.channels = (usn,)


class upnp_device_bye_bye(Event):
    
    def __init__(self, usn):
        super(upnp_device_bye_bye, self).__init__(usn)
        self.channels = (usn,)


class upnp_search_request(Event):
    
    def __init__(self, search_target=UPNP_ROOTDEVICE, mx=1, **kwargs):
        super(upnp_search_request, self).__init__(search_target, mx, **kwargs)


class SSDPReceiver(BaseComponent):

    channel = "ssdp"

    def __init__(self, channel = channel):
        super(SSDPReceiver, self).__init__(channel=channel)

    @handler("read")
    def _on_read(self, address, data):
        
        def istartswith(line, prefix):
            return line[0:len(prefix)].upper() == prefix

        def parse_lines(lines):
            ''' Helper function that parses the information and puts it in an
                anonymous type.'''
            res = type("", (), {})()
            for line in lines:
                if istartswith(line, "CACHE-CONTROL:"):
                    s = line.split(":", 1)[1].strip()
                    setattr(res, "max_age", int(s.split("=", 1)[1].strip()))
                elif istartswith(line, "LOCATION:"):
                    setattr(res, "location", line.split(":", 1)[1].strip())
                elif istartswith(line, "NT:"):
                    setattr(res, "notification_type", 
                            line.split(":", 1)[1].strip())
                elif istartswith(line, "ST:"):
                    # Handle search responses like alive messages
                    setattr(res, "notification_type", 
                            line.split(":", 1)[1].strip())
                elif istartswith(line, "NTS:"):
                    setattr(res, "sub_type", line.split(":", 1)[1].strip())
                elif istartswith(line, "SERVER:"):
                    setattr(res, "server", line.split(":", 1)[1].strip())
                elif istartswith(line, "USN:"):
                    setattr(res, "usn", line.split(":", 1)[1].strip())
            return res
        
        lines = data.splitlines()
        if istartswith(lines[0], "M-SEARCH "):
            # This is a search. It's up to us to repond if we have
            # matching devices
            search_target = None
            for line in lines[1:len(lines)-1]:
                if not line.upper().startswith("ST:"):
                    continue
                search_target = line.split(':', 1)[1].strip()
                f = lambda dev: True
                # TODO: add criteria
                if search_target == "upnp:rootdevice":
                    f = lambda dev: dev.root_device
                self.fire(upnp_device_query(f, address, search_target), "upnp")                        
                return
        elif istartswith(lines[0], "NOTIFY "):
            # A status change (or confirmation notification. Translate into
            # an event to inform however is interested in this.
            data = parse_lines(lines[1:])
            if data.sub_type == "ssdp:alive":
                self.fire(upnp_device_alive\
                          (data.location, data.notification_type, 
                           data.max_age, data.server, data.usn))
            elif data.sub_type == "ssdp:byebye":
                self.fire(upnp_device_bye_bye(data.usn))
        elif istartswith(lines[0], "HTTP/1.1 200 OK"):
            # A response to our own M-SEARCH. This is handled like a 
            # status change/confirmation (can only be an alive notification,
            # of course).
            data = parse_lines(lines[1:])
            self.fire(upnp_device_alive\
                      (data.location, data.notification_type, 
                       data.max_age, data.server, data.usn))
