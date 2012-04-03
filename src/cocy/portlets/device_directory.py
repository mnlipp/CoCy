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
from cocy.portlets.base import CoCyPortlet
from circuits_minpor import Portlet
from tenjin.helpers import *

class UPnPDirectoryPortlet(CoCyPortlet):

    def __init__(self):
        super(UPnPDirectoryPortlet, self).__init__()

    def description(self, locales=[]):
        return Portlet.Description(self._handle, "UPnP Devices")
    
    def render(self, mode=Portlet.RenderMode.View,
               window_state=Portlet.WindowState.Normal, locales=[]):
        if window_state == Portlet.WindowState.Solo:
            return self._engine.render("device_directory_solo.pyhtml", {})
        else:
            return self._engine.render("device_directory.pyhtml", {})
