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

class MgmtControllerQuery(Event):
    """
    This event is issued when a web based management user interface
    for an application is build. Every component that wants to contribute
    to such an interface listens for this event and returns a new
    object of type :class:`circuits.web.controllers.BaseController`.
    
    The controller returned should produce output that is based on
    the style-sheet that is passed as the first parameter of this
    event.  
    """

    target = "*"
    channel = "mgmt_controller_query"
