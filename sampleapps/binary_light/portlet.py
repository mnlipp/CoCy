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

class BinaryLightPortlet(TemplatePortlet):

    def __init__(self, binary_light):
        super(BinaryLightPortlet, self) \
            .__init__(os.path.dirname(__file__), "binary_light", weight=1)
        self._binary_light = binary_light

    def description(self, locales=[]):
        return Portlet.Description\
            (self._handle, self.translation(locales) \
             .ugettext("Binary Light"))

    def do_render(self, mime_type, mode, window_state, locales, url_generator, 
                  invocation_id, context_exts = {}, globs_exts = {}, **kwargs):
        return super(BinaryLightPortlet, self)\
            .do_render(mime_type, mode, window_state, locales, url_generator,
                       invocation_id, context_exts =
                       { "binary_light": self._binary_light })

