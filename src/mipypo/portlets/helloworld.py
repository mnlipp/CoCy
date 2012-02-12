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
from mipypo.core.portlet import Portlet

class HelloWorldPortlet(Portlet):

    def description(self, locales=[]):
        return Portlet.Description(self._handle, "Hello World Portlet")
    
    def render(self, mode=Portlet.RenderMode.View,
               window_state=Portlet.WindowState.Normal, locales=[]):
        if window_state == Portlet.WindowState.Solo:
            return "<div style=\"padding: 1em; font-size: 400%\">Hello World!</div>"
        else:
            return "<div style=\"padding: 1em;\">Hello World!</div>"
