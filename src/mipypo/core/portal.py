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

class Portal(BaseComponent):

    channel = "mipypo"

    def __init__(self, server=None, prefix=None, **kwargs):
        super(Portal, self).__init__(**kwargs)
        self._portlets = []
        if server is None:
            server = BaseServer(("", 4444), channel=self.channel)
        else:
            self.channel = server.channel
        self.server = server
        dispatcher = ScopeDispatcher(channel = server.channel).register(server)
        Root(self,
             channel=ScopedChannel(server.channel, prefix if prefix else "/")) \
            .register(dispatcher)
            
        HelloWorldPortlet(channel=self.channel).register(self)
        
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
        return list(self._portlets)

class Root(BaseControllerExt):
    
    docroot = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           "../templates"))

    def __init__(self, portal, **kwargs):
        super(Root, self).__init__(**kwargs)
        self._portal = portal
        self.engine = tenjin.Engine(path=[self.docroot])
    
    @expose("index")
    def index(self):
        context = {}
        context["portlets"] = self._portal.portlets
        context["locales"] = ["en_US"]
        return self.serve_tenjin \
            (self.request, self.response, "index.pyhtml", context,
             engine=self.engine, type="text/html")

    @expose("stylesheet.css")
    def stylesheet(self):
        return self.serve_file(os.path.join(self.docroot,
                                            "themes/default/mipypo.css"))

