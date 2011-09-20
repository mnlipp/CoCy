'''


.. codeauthor:: mnl
'''
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, ElementTree
from cocy.upnp import SSDP_DEVICE_SCHEMA, SSDP_SCHEMAS
from circuitsx.tools import replace_targets
from circuits.web.controllers import expose, BaseController
from cocy.core.components import BinarySwitch

class UPnPDevice(BaseController):

    channel = "ssdp"
    
    class Properties(object):
        def __init__(self, type, ver, spec_ver_major, spec_ver_minor,
                     services):
            object.__init__(self)
            self.type = type
            self.ver = ver
            self.spec_ver_major = spec_ver_major
            self.spec_ver_minor = spec_ver_minor
            self.services = services

    _mapping = {
        # "BasicDevice": Properties("Basic", 1, 1, 0, []),
        BinarySwitch: Properties("BinaryLight", 0.9, 1, 0,
                                 [("SwitchPower:1", "SwitchPower:1")])
    }

    def __init__(self, provider, config_id, service_map):
        self.valid = False
        for key, props in self._mapping.iteritems():
            if isinstance(provider, key):
                self.valid = True
                self._props = props
            break;
        self._uuid = str(uuid4())
        self._path = "/" + self.uuid
        replace_targets(self, {"#me": "/upnp-web" + self._path})
        super(UPnPDevice, self).__init__();
        self.config_id = config_id
        manifest = provider.provider_manifest()
        self.friendly_name = manifest.display_name
        self.manufacturer = manifest.manufacturer or "cocy"
        self.model_description = manifest.description
        self.model_name = manifest.full_name or manifest.display_name
        self.model_number = manifest.model_number

        services = []
        for (service_type, service_id) in self._props.services:
            if not service_map.has_key(service_type):
                continue
            services.append((service_map[service_type], service_id))

        desc = self._desc_funcs[self.type_ver](self, config_id, services)
        class Writer(object):
            result = ""
            def write(self, str):
                self.result += str
        writer = Writer()
        ElementTree(desc).write(writer, xml_declaration=True,
                                method="xml", encoding="utf-8")
        self.description = writer.result

    @property
    def uuid(self):
        return self._uuid

    def __getattr__(self, name):
        if not name.startswith("_") and hasattr(self._props, name):
            return getattr(self._props, name, None)
        raise AttributeError

    @property
    def type_ver(self):
        return "%s:%s" % (self._props.type, str(self._props.ver))

    def _common_device_desc(self, config_id, services):
        root = Element("{%s}root" % SSDP_DEVICE_SCHEMA,
                       attrib = {"configId": str(config_id)})
        specVersion = SubElement(root, "{%s}specVersion" % SSDP_DEVICE_SCHEMA)
        SubElement(specVersion, "{%s}major" % SSDP_DEVICE_SCHEMA).text \
            = str(self.spec_ver_major)
        SubElement(specVersion, "{%s}minor" % SSDP_DEVICE_SCHEMA).text \
            = str(self.spec_ver_minor)
        device = SubElement(root, "{%s}device" % SSDP_DEVICE_SCHEMA)
        SubElement(device, "{%s}deviceType" % SSDP_DEVICE_SCHEMA).text \
            = SSDP_SCHEMAS + ":device:" + self.type_ver
        for tag, attrib in [("friendlyName", "friendly_name"),
                            ("manufacturer", "manufacturer"),
                            ("modelDescription", "model_description"),
                            ("modelName", "model_name"),
                            ("modelNumber", "model_number")]:
            if getattr(self, attrib, None):
                SubElement(device, "{%s}%s" % (SSDP_DEVICE_SCHEMA, tag)).text \
                    = getattr(self, attrib, None)
        SubElement(device, "{%s}UDN" % SSDP_DEVICE_SCHEMA).text \
            = "uuid:" + self.uuid
        if services and len(services) > 0:
            serviceList = SubElement(device, 
                                     "{%s}serviceList" % SSDP_DEVICE_SCHEMA)
            for service in services:
                self._addService(serviceList, service)
        return root
        
    _desc_funcs = {
        "BinaryLight:0.9": _common_device_desc,
        "Basic:1": _common_device_desc
    }

    def _addService(self, service_list, service_tuple):
        (service_type, service_id) = service_tuple
        service = SubElement(service_list, "{%s}service" % SSDP_DEVICE_SCHEMA)
        SubElement(service, "{%s}serviceType" % SSDP_DEVICE_SCHEMA).text \
            = SSDP_SCHEMAS + ":service:" + service_type.type_ver
        SubElement(service, "{%s}serviceId" % SSDP_DEVICE_SCHEMA).text \
            = service_id
        SubElement(service, "{%s}SCPDURL" % SSDP_DEVICE_SCHEMA).text \
            = service_type.description_url
        SubElement(service, "{%s}controlURL" % SSDP_DEVICE_SCHEMA).text \
            = self._path + "/control"
        SubElement(service, "{%s}eventSubURL" % SSDP_DEVICE_SCHEMA).text \
            = self._path + "/sub"
        
    @expose("control", target="#me")
    def _on_control(self):
        self.response.headers["Content-Type"] = "text/xml"
        return "control"

    @expose("sub", target="#me")
    def _on_sub(self):
        self.response.headers["Content-Type"] = "text/xml"
        return "sub"
    
    @expose("description.xml", target="#me")
    def _on_description(self):
        self.response.headers["Content-Type"] = "text/xml"
        return self.description
