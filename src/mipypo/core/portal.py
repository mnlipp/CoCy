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
from circuits.web import expose
from circuits.web.controllers import BaseController
from circuits.core.components import BaseComponent
from circuits.web.servers import BaseServer
from circuitsx.web.dispatchers.dispatcher import ScopeDispatcher, ScopedChannel
import os
from util.web import BaseControllerExt
from mipypo.portlets.helloworld import HelloWorldPortlet
from circuits.core.handlers import handler
from mipypo.core.portlet import Portlet
import tenjin
from copy import copy
import uuid

class Portal(BaseComponent):

    channel = "mipypo"

    def __init__(self, server=None, prefix=None, 
                 portal_title=None, templates_dir=None, **kwargs):
        super(Portal, self).__init__(**kwargs)
        self._portlets = []
        if server is None:
            server = BaseServer(("", 4444), channel=self.channel)
        else:
            self.channel = server.channel
        self.server = server
        dispatcher = ScopeDispatcher(channel = server.channel).register(server)
        _Root(self,
              channel=ScopedChannel(server.channel, prefix if prefix else "/"),
              portal_title=portal_title,
              templates_dir=templates_dir) \
              .register(dispatcher)
            
        hwp1 = HelloWorldPortlet(channel=self.channel).register(self)
        hwp2 = HelloWorldPortlet(channel=self.channel).register(self)
        self._tabs = [_TabInfo("Overview", "_dashboard", selected=True)]
        
    @handler("registered")
    def _on_registered(self, c, m):
        if not isinstance(c, Portlet):
            return
        if not c in self._portlets:
            self._portlets.append(c)

    @handler("unregistered")
    def _on_unregistered(self, c, m):
        if not isinstance(c, Portlet):
            return
        if c in self._portlets:
            self._portlets.remove(c)

    @property
    def portlets(self):
        return copy(self._portlets)
    
    @property
    def tabs(self):
        return copy(self._tabs)

    def select_tab(self, tab_id):
        for i, tab in enumerate(self._tabs):
            tab._selected = (id(tab) == tab_id)

    def close_tab(self, tab_id):
        tabs = filter(lambda x: id(x) == tab_id, self._tabs)
        if len(tabs) == 0:
            return
        closed = tabs[0]
        closed_idx = self._tabs.index(closed)
        del self._tabs[closed_idx]
        if closed._selected:
            if len(self._tabs) > closed_idx:
                self._tabs[closed_idx]._selected = True
            else:
                self._tabs[0]._selected = True

    def add_solo(self, portlet_handle):
        for portlet in self._portlets:
            portlet_desc = portlet.description()
            if portlet_desc.handle == portlet_handle:
                break
            else:
                portlet_desc = None
        if not portlet_desc:
            return
        solo_tabs = filter(lambda x: x.portlet == portlet, self._tabs)
        if len(solo_tabs) > 0:
            self.select_tab(id(solo_tabs[0]))
            return
        tab = _TabInfo(portlet_desc.short_title, "_solo", closeable=True,
                       portlet=portlet)
        self._tabs.append(tab)
        self.select_tab(id(tab))

class _TabInfo(object):
    
    def __init__(self, label, renderer, selected = False, closeable=False,
                 portlet=None):
        self._label = label
        self._content_renderer = renderer
        self._selected = selected
        self._closeable = closeable
        self._portlet = portlet

    @property
    def label(self):
        return self._label
    
    @property
    def content_renderer(self):
        return self._content_renderer
        
    @property
    def selected(self):
        return self._selected
    
    @property
    def closeable(self):
        return self._closeable

    @property
    def portlet(self):
        return self._portlet

class _Root(BaseControllerExt):
    
    docroot = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           "../templates"))

    def __init__(self, portal, **kwargs):
        super(_Root, self).__init__(**kwargs)
        self._portal = portal
        path=[self.docroot]
        self._templates_override = kwargs.get("templates_dir", None)
        if self._templates_override:
            path.append(self._templates_override)
        self.engine = tenjin.Engine(path=path)
    
    @expose("index")
    def index(self, *args, **kwargs):
        if len(args) > 0:
            return
        if kwargs.get("action") == "select":
            self._portal.select_tab(int(kwargs.get("tab")))
        elif kwargs.get("action") == "close":
            self._portal.close_tab(int(kwargs.get("tab")))
        elif kwargs.get("action") == "solo":
            self._portal.add_solo(uuid.UUID(kwargs.get("portlet")))
        context = {}
        context["portlets"] = self._portal.portlets
        context["tabs"] = self._portal.tabs
        context["locales"] = ["en_US"]
        return self.serve_tenjin \
            (self.request, self.response, "portal.pyhtml", context,
             engine=self.engine, type="text/html")

    @expose("theme-resource")
    def theme_resource(self, resource):
        if self._templates_override:
            f = os.path.join(self._templates_override, 
                             "themes/default", resource)
            if os.access(f, os.R_OK):
                return self.serve_file (f)
        f = os.path.join(self.docroot, "themes/default", resource)
        return self.serve_file (f)

