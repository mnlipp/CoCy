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
from circuits_minpor import Portlet
from tenjin.helpers import *
from circuits_minpor.portlet import TemplatePortlet
import os

class UPnPDeviceServerPortlet(TemplatePortlet):

    def __init__(self, device_server):
        super(UPnPDeviceServerPortlet, self) \
            .__init__(os.path.join(os.path.dirname(__file__), "templates"), 
                      "device_server")
        self._device_server = device_server

    def description(self, locales=[]):
        return Portlet.Description\
            (self._handle, self.translation(locales) \
             .ugettext("Published UPnP Devices"))

    def do_render(self, mime_type, mode, window_state, locales, url_generator, 
                  invocation_id, portal, context_exts = {}, globs_exts = {}, **kwargs):
        return super(UPnPDeviceServerPortlet, self)\
            .do_render(mime_type, mode, window_state, locales, url_generator,
                       invocation_id, portal, context_exts =
                       { "device_server": self._device_server })

