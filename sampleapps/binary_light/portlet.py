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
from circuits.core.handlers import handler
from circuits_minpor.portal import portal_update

class BinaryLightPortlet(TemplatePortlet):

    def __init__(self, binary_light):
        super(BinaryLightPortlet, self) \
            .__init__(os.path.dirname(__file__), "binary_light", weight=1)
        self._binary_light = binary_light
        self._sessions = []
        @handler("provider_updated", channel=binary_light.channel)
        def _on_provider_updated(self, provider, changed):
            self._on_updated(self._sessions, provider, changed)
        self.addHandler(_on_provider_updated)

    def description(self, locales=[]):
        return Portlet.Description\
            (self._handle, self.translation(locales) \
             .ugettext("Binary Light"))

    def do_render(self, mime_type, mode, window_state, locales, url_generator, 
                  invocation_id, portal, context_exts = {}, globs_exts = {}, **kwargs):
        return super(BinaryLightPortlet, self)\
            .do_render(mime_type, mode, window_state, locales, url_generator,
                       invocation_id, portal, context_exts =
                       { "binary_light": self._binary_light })

    @handler("portlet_added")
    def _on_portlet_added(self, portal, portlet):
        self._portal_channel = portal.channel
        @handler("portal_client_connect", channel=portal.channel)
        def _on_client_connect(self, session):
            self._sessions.append(session)
            self._on_updated([session], self._binary_light, None)
        self.addHandler(_on_client_connect)
        @handler("portal_client_disconnect", channel=portal.channel)
        def _on_client_disconnect(self, session, sock):
            self._sessions.remove(session)
        self.addHandler(_on_client_disconnect)

    def _on_updated(self, sessions, provider, changed):
        if provider != self._binary_light:
            return
        for session in sessions:
            self.fire(portal_update(self, session, "new_state", self._binary_light.state),
                      self._portal_channel)
