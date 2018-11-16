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
from circuits.core.components import BaseComponent
from circuits_bricks.misc.compquery import Queryable
from uuid import uuid4
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, QName
from circuits_bricks.web.dispatchers.dispatcher import ScopedChannel
from cocy.upnp import SSDP_DEVICE_SCHEMA, SSDP_SCHEMAS, UPNP_EVENT_NS,\
    UPNP_SERVICE_ID_PREFIX, SERVER_HELLO
from circuits.web.controllers import Controller, expose, BaseController
from cocy.misc import parseSoapRequest, splitQTag, buildSoapResponse
from cocy.upnp.device_server import UPnPError
from email.utils import formatdate
from circuits_bricks.core.timers import Timer
from circuits.core.events import Event
from circuits.core.handlers import handler
from inspect import getmembers, ismethod
from circuits_bricks.web.client import Client, request
from cocy.upnp.service import UPnPService
from circuits_bricks.app.logger import log
import logging
from cocy import misc

class UPnPServiceError(Exception):
    
    def __init__(self, code):
        self._code = code
        
    @property
    def code(self):
        return self._code
    

class UPnPDeviceAdapter(BaseComponent, Queryable):
    """
    This class publishes a :class:`cocy.Provider` as a UPnP device.
    
    The class itself holds and provides the basic information that is 
    required to announce the the device using SSDP. The detailed description
    is provided using a child :class:`~.UPnPDeviceController`.
    Actions can be invoked on the provider one or more child
    components of type :class:`~.UPnPServiceController`. 
    """

    channel = "upnp"
    
    class DeviceProperties(object):
        """
        This class simply serves as a container for common information about 
        UPnP device types.
        """
        
        def __init__(self, dev_type, ver, spec_ver_major, spec_ver_minor,
                     services, desc_gen):
            object.__init__(self)
            self.type = dev_type
            self.ver = ver
            self.spec_ver_major = spec_ver_major
            self.spec_ver_minor = spec_ver_minor
            self.services = services
            self.desc_gen = desc_gen

    _service_registry = dict()
    _mapping = dict()
    _props = DeviceProperties("Undefined", 0, 0, 0, [], None)
    """
    This dictionary maps the defined :class:`cocy.providers.Provider`
    classes to UPnP device properties.
    """

    @classmethod
    def add_adapter(cls, provider_class, props):
        # Create and register all known service types
        cls._mapping[provider_class] = props

    def __init__(self, server, provider, config_id, uuid_map, port):
        super(UPnPDeviceAdapter, self).__init__();
        
        # It may turn out that no adapter can be constructed
        self.valid = False
        # Try to find a match UPnP info for the device 
        for itf, props in self._mapping.iteritems():
            if isinstance(provider, itf):
                self.valid = True
                self._props = props
                break;
        if not self.valid:
            return
        # Remember the provider as our "model"
        self._provider = provider
        # Remember port
        self._web_server_port = port
        # Get instance information about the provider
        manifest = provider.provider_manifest
        if manifest.unique_id and uuid_map.has_key(manifest.unique_id):
            self._uuid = uuid_map[manifest.unique_id]
        else:
            self._uuid = str(uuid4())
            uuid_map[manifest.unique_id] = self._uuid
        # Generate a unique path that will be used to access this device
        self._path = "/" + self.uuid
        # Remember the configuration id
        self.config_id = config_id

        # Assemble the services supported by the provider
        self._services = set()
        service_insts = []
        for (service_type, service_id, controller) in self._props.services:
            if not UPnPDeviceAdapter._service_registry.has_key(service_type):
                try:
                    service = UPnPService \
                        (config_id, service_type).register(self) \
                        .register(server)
                except:
                    continue
            else:
                service = UPnPDeviceAdapter._service_registry[service_type]
            self._services.add(service)
            service_insts.append((service, service_id))
            # Create an adapter that links this class's service with the web
            # component interface of circuits
            controller(self, self._path, service, service_id).register(self)

        # Create an adapter that links this class with the web
        # component interface of circuits
        UPnPDeviceController(ScopedChannel("upnp-web", self._path),
                             self, config_id, props, service_insts) \
            .register(self)

    @property
    def provider(self):
        return getattr(self, "_provider", None)

    @property
    def path(self):
        return getattr(self, "_path", None)

    @property
    def web_server_port(self):
        return getattr(self, "_web_server_port", None)

    @property
    def uuid(self):
        return getattr(self, "_uuid", None)

    @property
    def root_device(self):
        return True # TODO:

    @property
    def services(self):
        return getattr(self, "_services", None)

    def __getattr__(self, name):
        if not name.startswith("_") and hasattr(self._props, name):
            return getattr(self._props, name, None)
        raise AttributeError("No " + name + " in " + self.__class__.__name__)

    @property
    def type_ver(self):
        return "%s:%s" % (str(self.type), str(self.ver))


class UPnPDeviceController(Controller):

    def __init__(self, channel, adapter, config_id, props, service_insts):
        super(UPnPDeviceController, self).__init__(channel=channel);
        # Generate a device description for the device
        desc = getattr(self, props.desc_gen)\
            (adapter, config_id, props, service_insts)
        misc.set_ns_prefixes(desc, { "": SSDP_DEVICE_SCHEMA })
        self.description = u"<?xml version='1.0' encoding='utf-8'?>" \
            + ElementTree.tostring(desc, encoding="utf-8").decode("utf-8")
 
    def _common_device_desc(self, adapter, config_id, props, services):
        root = Element("{%s}root" % SSDP_DEVICE_SCHEMA,
                       attrib = {"configId": str(config_id)})
        specVersion = SubElement(root, "{%s}specVersion" % SSDP_DEVICE_SCHEMA)
        SubElement(specVersion, "{%s}major" % SSDP_DEVICE_SCHEMA).text \
            = str(props.spec_ver_major)
        SubElement(specVersion, "{%s}minor" % SSDP_DEVICE_SCHEMA).text \
            = str(props.spec_ver_minor)
        device = SubElement(root, "{%s}device" % SSDP_DEVICE_SCHEMA)
        SubElement(device, "{%s}deviceType" % SSDP_DEVICE_SCHEMA).text \
            = SSDP_SCHEMAS + ":device:" + adapter.type_ver
        manifest = adapter.provider.provider_manifest
        for tag, value in \
            [("friendlyName", manifest.display_name),
             ("manufacturer", manifest.manufacturer or "cocy"),
             ("modelDescription", manifest.description),
             ("modelName", manifest.full_name or manifest.display_name),
             ("modelNumber", manifest.model_number)]:
            if value is not None:
                SubElement(device, "{%s}%s" % (SSDP_DEVICE_SCHEMA, tag)).text \
                    = value
        SubElement(device, "{%s}UDN" % SSDP_DEVICE_SCHEMA).text \
            = "uuid:" + adapter.uuid
        if services and len(services) > 0:
            serviceList = SubElement(device, 
                                     "{%s}serviceList" % SSDP_DEVICE_SCHEMA)
            for service in services:
                self._describeService(adapter, serviceList, service)
        return root
        
    def _describeService(self, adapter, service_list, service_tuple):
        (service_type, service_id) = service_tuple
        service = SubElement(service_list, "{%s}service" % SSDP_DEVICE_SCHEMA)
        SubElement(service, "{%s}serviceType" % SSDP_DEVICE_SCHEMA).text \
            = SSDP_SCHEMAS + ":service:" + service_type.type_ver
        SubElement(service, "{%s}serviceId" % SSDP_DEVICE_SCHEMA).text \
            = UPNP_SERVICE_ID_PREFIX + service_id
        SubElement(service, "{%s}SCPDURL" % SSDP_DEVICE_SCHEMA).text \
            = service_type.description_url
        SubElement(service, "{%s}controlURL" % SSDP_DEVICE_SCHEMA).text \
            = adapter.path + "/" + service_id + "/control"
        SubElement(service, "{%s}eventSubURL" % SSDP_DEVICE_SCHEMA).text \
            = adapter.path + "/" + service_id + "/sub"

    @expose("description.xml")
    def description(self, *args):
        self.response.headers["Content-Type"] = "text/xml"
        return self.description


class upnp_notification(Event):
    pass


class UPnPSubscription(BaseController):
    
    def __init__(self, callbacks, timeout, protocol):
        self._uuid = str(uuid4())
        super(UPnPSubscription, self).__init__(channel="subs:" + self._uuid)
        self._callbacks = callbacks
        self._used_callback = 0
        self._client = Client(self._callbacks[self._used_callback], 
                              self.channel).register(self)
        self._protocol = protocol
        self._seq = 0
        if timeout > 0:
            self._expiry_timer = Timer \
                (timeout, Event.create("upnp_subs_end"), self).register(self)

    @handler("registered")
    def _on_registered(self, component, parent):
        if component != self:
            return
        @handler("upnp_notification", channel=parent.notification_channel)
        def _on_notification_handler(self, state_vars):
            self._on_notification(state_vars)
        self.addHandler(_on_notification_handler)
        state_vars = dict()
        for name, method in getmembers \
            (self.parent, lambda x: ismethod(x) and hasattr(x, "_evented_by")):
            state_vars[name] = method()
        if len(state_vars) > 0:
            self._on_notification(state_vars)
        self.fire(log(logging.DEBUG, "Subscribtion for " + str(self._callbacks)
                      + " on " + self.parent.notification_channel 
                      + " created"), "logger")

    def _on_notification(self, state_vars):
        root = Element(QName(UPNP_EVENT_NS, "propertyset"))
        for name, value in state_vars.items():
            prop = SubElement(root, QName(UPNP_EVENT_NS, "property"))
            val = SubElement(prop, QName(UPNP_EVENT_NS, name))
            if isinstance(value, bool):
                val.text = "1" if value else "0"
            else:
                val.text = unicode(value)
        misc.set_ns_prefixes(root, { "": UPNP_EVENT_NS })
        # Keep body as str for safe request handling
        body = "<?xml version='1.0' encoding='utf-8'?>" \
            + ElementTree.tostring(root, encoding="utf-8")
        self.fire(log(logging.DEBUG, "Notifying " 
                      + self._callbacks[self._used_callback]
                      + " about " + str(state_vars)), "logger")
        self.fire(request("NOTIFY", self._callbacks[self._used_callback], body,
                          { "CONTENT-TYPE": "text/xml; charset=\"utf-8\"",
                            "NT": "upnp:event",
                            "NTS": "upnp:propchange",
                            "SID": self.sid,
                            "SEQ": self._seq }))
        self._seq += 1

    @handler("upnp_subs_end")
    def _on_subs_end(self):
        self.unregister()
        self.fire(log(logging.DEBUG, "Subscribtion for " + str(self._callbacks)
                      + " on " + self.parent.notification_channel
                      + " cancelled"), "logger")

    @handler("upnp_subs_renewal")
    def _on_renewal(self, timeout):
        self._expiry_timer.interval = timeout
        self._expiry_timer.reset()
        self.fire(log(logging.DEBUG, "Subscribtion for " + str(self._callbacks)
                      + " on " + self.parent.notification_channel
                      + " renewed"), "logger")

    @property
    def sid(self):
        return "uuid:" + self._uuid

    @classmethod
    def sid2chan(cls, sid):
        return "subs:" + sid[5:]


class UPnPServiceController(BaseController):

    def __init__ \
        (self, adapter, device_path, service, service_id):
        super(UPnPServiceController, self).__init__ \
            (channel=ScopedChannel("upnp-web", device_path + "/" + service_id));
        self._service = service
        self._notification_channel = adapter.uuid + "/" \
            + service_id + "/notifications"

    @property
    def notification_channel(self):
        return getattr(self, "_notification_channel", None)

    @handler("registered")
    def _on_registered(self, component, parent):
        if component != self:
            return
        @handler("provider_updated", channel=self.parent.provider.channel)
        def _on_provider_updated_handler(self, provider, changed):
            if provider != self.parent.provider:
                return
            self._on_provider_updated(changed)
        self.addHandler(_on_provider_updated_handler)
            
    def _on_provider_updated(self, changed):
        state_vars = dict()
        for name, method in getmembers \
            (self, lambda x: ismethod(x) and hasattr(x, "_evented_by")):
            if method._evented_by is not None:
                state_vars[name] = changed[method._evented_by]
        if len(state_vars) > 0:
            self.fire(upnp_notification(state_vars), self.notification_channel)

    @expose("control")
    def _control(self, *args):
        payload = parseSoapRequest(self.request)[2]
        action_ns, action = splitQTag(payload.tag)
        action_args = dict()
        for node in payload:
            action_args[node.tag] = node.text
        method = getattr(self, action, None)
        if method is None or not getattr(method, "_is_upnp_service", False):
            self.fire(log(logging.INFO, 'Action ' + action 
                          + " not implemented"), "logger")
            return UPnPError(self.request, self.response, 401)
        try:
            out_args = method(**action_args)
        except UPnPServiceError as error:
            return UPnPError(self.request, self.response, error.code)
        result = Element("{%s}%sResponse" % (action_ns, action))
        for name, value in out_args:
            arg = SubElement(result, name)
            arg.text = unicode(value)
        return buildSoapResponse(self.response, result)

    @expose("sub")
    def _sub(self, *args):
        if self.request.method == "SUBSCRIBE":
            timeout = self.request.headers["Timeout"]
            timeout = timeout[len("Second-"):]
            try:
                timeout = int(timeout)
            except ValueError:
                timeout = 1800
            self.response.headers["Date"] = formatdate(usegmt=True)
            self.response.headers["Server"] = SERVER_HELLO
            self.response.headers["Timeout"] = "Second-" + str(timeout)
            if "SID" in self.request.headers:
                # renewal
                sid = self.request.headers["SID"]
                self.response.headers["SID"] = sid
                self.fire(Event.create("upnp_subs_renewal", timeout), 
                          UPnPSubscription.sid2chan(sid))
                return ""
            callbacks = []
            for cb in self.request.headers["CALLBACK"].split("<")[1:]:
                callbacks.append(cb[:cb.rindex(">")])
            subs = UPnPSubscription(callbacks, timeout, 
                                    self.request.protocol).register(self)
            self.response.headers["SID"] = subs.sid
            return ""
        elif self.request.method == "UNSUBSCRIBE":
            sid = self.request.headers["SID"]
            self.fire(Event.create("upnp_subs_end"), 
                      UPnPSubscription.sid2chan(sid))
            return ""


def upnp_service(f):
    setattr(f, "_is_upnp_service", True)
    return f

def upnp_state(*args, **kwargs):
    if len(args) == 0 or not hasattr(args[0], "__call__"):
        # function to be wrapped isn't first parameter, re-wrap
        def wrapper(f):
            setattr(f, "_is_upnp_state", True)
            if "evented_by" in kwargs:
                setattr(f, "_evented_by", kwargs["evented_by"])
            return f
        return wrapper
    else:
        # function to be wrapped is first parameter
        f = args[0]
        setattr(f, "_is_upnp_state", True)
        return f
