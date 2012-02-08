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
from abc import ABCMeta, abstractmethod

class Portlet(BaseComponent):
    
    __metaclass__ = ABCMeta
    
    class RenderMode(object):
        View = 1
        Edit = 2
        Help = 3
        Preview = 4
        
    class WindowState(object):
        Normal = 1
        Minimized = 2
        Maximized = 3
        Solo = 4

    class MarkupType(object):

        def __init__(self, modes = None, states = None):
            self._modes = modes or [Portlet.RenderMode.View]
            self._states = states or [Portlet.WindowState.Normal]
        
        @property
        def render_modes(self):
            return self._modes
        
        @property
        def window_states(self):
            return self.states

    class Description(object):
        def __init__(self, title, markup_types=None, locale = "en-US"):
            self._title = title
            self._markup_types = markup_types \
                or dict({ "text/html": Portlet.MarkupType()})
            self._locale = locale

        @property
        def title(self):
            return self._title
        
        @property
        def markup_types(self):
            return self._markup_types

        @property
        def locale(self):
            return self._locale

    def description(self, locales=[]):
        return Portlet.Description("Base Portlet")
    
    def render(self, mode=RenderMode.View,
               window_state=WindowState.Normal, locales=[]):
        return "<div class=\"portlet-msg-error\">" \
                + "Portlet not implemented yet</div>"
