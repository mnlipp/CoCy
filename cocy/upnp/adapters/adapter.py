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
from xml.etree.ElementTree import ElementTree, Element, SubElement
from circuits_bricks.web.dispatchers.dispatcher import ScopedChannel
from cocy.upnp import SSDP_DEVICE_SCHEMA, SSDP_SCHEMAS
from circuits.web.controllers import Controller, expose, BaseController
from util.misc import parseSoapRequest, splitQTag, buildSoapResponse
from cocy.upnp.device_server import UPnPError


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

    _mapping = dict()
    """
    This dictionary maps the defined :class:`cocy.providers.Provider`
    classes to UPnP device properties.
    """

    @classmethod
    def add_adapter(cls, provider_class, props):
        cls._mapping[provider_class] = props

    def __init__(self, provider, config_id, uuid_map, service_map, port):
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

        # Assemble the services provided for the provider
        self._services = set()
        service_insts = []
        for (service_type, service_id, controller) in self._props.services:
            if not service_map.has_key(service_type):
                continue
            service = service_map[service_type]
            self._services.add(service)
            service_insts.append((service, service_id))
            # Create an adapter that links this class's service with the web
            # component interface of circuits
            controller(self._path, service, service_id).register(self)

        # Create an adapter that links this class with the web
        # component interface of circuits
        UPnPDeviceController(ScopedChannel("upnp-web", self._path),
                             self, config_id, props, service_insts) \
            .register(self)

    @property
    def provider(self):
        return self._provider

    @property
    def path(self):
        return self._path

    @property
    def web_server_port(self):
        return self._web_server_port

    @property
    def uuid(self):
        return self._uuid

    @property
    def root_device(self):
        return True # TODO:

    @property
    def services(self):
        return self._services

    def __getattr__(self, name):
        if not name.startswith("_") and hasattr(self._props, name):
            return getattr(self._props, name, None)
        raise AttributeError

    @property
    def type_ver(self):
        return "%s:%s" % (self._props.type, str(self._props.ver))


class UPnPDeviceController(Controller):

    def __init__(self, channel, adapter, config_id, props, service_insts):
        super(UPnPDeviceController, self).__init__(channel=channel);
        # Generate a device description for the device
        desc = getattr(self, props.desc_gen)\
            (adapter, config_id, props, service_insts)
        class Writer(object):
            result = ""
            def write(self, value):
                self.result += value
        writer = Writer()
        writer.write("<?xml version='1.0' encoding='utf-8'?>\n")
        ElementTree(desc).write(writer, encoding="utf-8")
        self.description = writer.result

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
            = service_id
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


class UPnPServiceController(BaseController):

    def __init__ \
        (self, device_path, service, service_id):
        super(UPnPServiceController, self).__init__ \
            (channel=ScopedChannel("upnp-web", device_path + "/" + service_id));
        self._service = service

    @expose("control")
    def _control(self, *args):
        payload = parseSoapRequest(self.request)[2]
        action_ns, action = splitQTag(payload.tag)
        action_args = dict()
        for node in payload:
            action_args[node.tag] = node.text
        method = getattr(self, action, None)
        if method is None or not getattr(method, "is_upnp_service", False):
            return UPnPError(self.request, self.response, 401)
        out_args = method(**action_args)
        result = Element("{%s}%sResponse" % (action_ns, action))
        for name, value in out_args:
            arg = SubElement(result, name)
            arg.text = value
        return buildSoapResponse(self.response, result)

    @expose("sub")
    def _sub(self, *args):
        self.response.headers["Content-Type"] = "text/xml"
        return "sub"

def upnp_service(f):
    setattr(f, "is_upnp_service", True)
    return f
