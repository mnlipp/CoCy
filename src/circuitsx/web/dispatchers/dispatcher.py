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
from circuits.web.dispatchers.dispatcher import Dispatcher
from circuits.core.handlers import handler
from circuitsx.tools import component_handlers
from circuits.web.utils import parseQueryString
from circuits.web.controllers import BaseController

class ScopedChannel(object):
    """
    This class provides a combination of a request scope and
    a path for sending web requests to channels.
    
    The default request handling used in circuits matches the
    path of a request against a list of paths assembled from the
    :class:`circuits.web.controllers.BaseController`'s channels.
    This class allows you to specify an additional criterion for matching,
    the scope. The value of the scope must match the channel used by the
    server that received the request.
    
    Note that scoped channels only work in combination with
    :class:`circuitsx.web.ScopeDispatcher`.
    """
    
    def __init__(self, scope="web", path="/"):
        self._scope = scope
        self._path = path
    
    def __eq__(self, other):
        if isinstance(other, ScopedChannel):
            return self._scope == other._scope and self._path == other._path
        return NotImplemented
    
    def __hash__(self):
        return self._scope.__hash__() ^ self._path.__hash__()
    
    def __repr__(self):
        return "ScopedChannel(\"" + self._scope + "\", \"" + self._path + "\")"

    @property
    def scope(self):
        return self._scope
    
    @property
    def path(self):
        return self._path


class ScopeDispatcher(Dispatcher):
    """
    This component provides a dispatcher for requests that are received on
    a specific channel.
    
    The dispatcher forwards requests only to controllers with a 
    :class:`circuitsx.web.ScopedChannel` as channel. The scoped
    channel's scope property must match the channel assigned to the
    ``ScopeDispatcher``.
    
    In contrast to the standard :class:`circuits.web.Dispatcher`
    a class doesn't necessarily have to inherit from
    :class:`circuits.web.controllers.BaseController`.
    It may also expose request handling methods using the
    ``@expose`` annotation with keyword parameter `target` set
    to a scoped channel. Of course, you cannot use the prepared
    response methods that you usually inherit from ``BaseController``
    if you use that mechanism.     
    
    Also note that this dispatcher will not modify the component hierarchy
    as :class:`circuits.web.Dispatcher` does. Any registered controller's
    parent will remain unchanged.
    
    The scope dispatcher does not override the behavior of a standard
    dispatcher, it complements it. If a standard dispatcher component
    is registered in your component hierarchy, it will still grab and
    register the controller components.
    """

    channel = "web"

    def __init__(self, **kwargs):
        """
        The constructor creates a new dispatcher using the given
        parameters. The keyword parameter "channel" should be
        provided.
        """
        super(ScopeDispatcher, self).__init__(**kwargs)

    @handler("registered", target="*", override=True)
    def _on_registered(self, c, m):
        if not isinstance(c, BaseController):
            return
        for h in component_handlers(c):
            scoped_channel = h.target or c.channel
            if scoped_channel and isinstance(scoped_channel, ScopedChannel) \
                and scoped_channel.scope == self.channel:
                self.paths.add(scoped_channel.path)
                self.addHandler(h, h.channels, target=scoped_channel.path)

    @handler("unregistered", target="*", override=True)
    def _on_unregistered(self, c, m):
        if not isinstance(c, BaseController):
            return
        for h in component_handlers(c):
            scoped_channel = h.target or c.channel
            if scoped_channel and isinstance(scoped_channel, ScopedChannel) \
                and scoped_channel.scope == self.channel:
                self.paths.remove(scoped_channel.path)
                self.removeHandler(h)

    @handler("request", filter=True, priority=0.1, override=True)
    def _on_request(self, event, request, response, peer_cert=None):
        req = event
        if peer_cert:
            req.peer_cert = peer_cert

        channel, target, vpath = self._getChannel(request)

        if channel and target:
            req.kwargs = parseQueryString(request.qs)
            v = self._parseBody(request, response, req.kwargs)
            if not v:
                return v  # MaxSizeExceeded (return the HTTPError)

            if vpath:
                req.args += tuple(vpath)

            return self.push(req, channel, ScopedChannel(self.channel, target))
