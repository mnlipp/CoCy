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
from circuits.core.events import Event
from circuits.core.components import BaseComponent
from circuits.core.handlers import handler

class ComponentQuery(Event):
    
    channel = "component_query"
    
    def __init__(self, query_function, **kwargs):
        super(ComponentQuery, self).__init__()
        self._query_function = query_function

    def decide(self, component):
        try:
            if self._query_function(component):
                return component
            else:
                return None
        except:
            return None

class Queryable(BaseComponent):
    
    @handler("component_query")
    def _on_component_query(self, event):
        return event.decide(self)
