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
from circuitsx.tools import replace_targets
from circuits.web.controllers import BaseController, expose
import os
from circuitsx.web.dispatchers.dispatcher import ScopedChannel


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

    channel = None
    _template_dir = os.path.join(os.path.dirname(__file__), "templates")

    def __init__(self, type, ver):
        """
        Instances of this component are created from a service
        description that is selected by the given type and version.        
        The service description is looked up in a directory
        where it is stored as a file named ``type_ver.xml``.
        
        :param type: the service type
        :param ver: the service version
        """
        self._type = type
        self._ver = ver
        self._path = "/%s_%s" % (self._type, self._ver)
        self.channel = ScopedChannel("upnp-web", self._path)
        # Now call super as only now the channel is known and this classes
        # handlers will be registered properly
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

    @expose("service.xml")
    def _on_description(self):
        self.response.headers["Content-Type"] = "text/xml"
        return self._description
