'''
.. codeauthor:: mnl
'''
from circuitsx.tools import replace_targets
from circuits.web.controllers import BaseController, expose
import os


class UPnPService(BaseController):
    """
    A ``UPnPService`` component provides HTTP access to a UPnP service
    description.
    
    As specified in the UPnP architecture, services are
    identified by a type and a version. The service descriptions are made
    available to the clients via HTTP GET requests to specific URLs 
    that return the description as XML text.    
    The URL for accessing a device's service description is part of the
    information provided for the device.
    """

    _template_dir = os.path.join(os.path.dirname(__file__), "templates")

    def __init__(self, type, ver):
        """
        Instances of this component are created from a
        given type and version of a service.        
        The actual service description is looked up in a directory
        where it is stored as a file named ``type_ver.xml``.
        
        :param type: the service type
        :param ver: the service version
        """
        self._type = type
        self._ver = ver
        self._path = "/%s_%s" % (self._type, self._ver)
        replace_targets(self, {"#me": "/upnp-web" + self._path})
        super(UPnPService, self).__init__();
        file = open(os.path.join(self._template_dir, 
                                 "%s_%s.xml" % (self._type, self._ver)))
        self._description = file.read()

    @property
    def type_ver(self):
        return "%s:%s" % (self._type, str(self._ver))

    @property
    def description_url(self):
        return self._path + "/service.xml" 

    @expose("service.xml", target="#me")
    def _on_description(self):
        self.response.headers["Content-Type"] = "text/xml"
        return self._description
