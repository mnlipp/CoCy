'''


.. codeauthor:: mnl
'''

from circuits.web.dispatchers.dispatcher import Dispatcher
from circuits.core.handlers import handler
from circuitsx.tools import component_handlers

class ScopeDispatcher(Dispatcher):

    channel = "web"

    def __init__(self, **kwargs):
        super(ScopeDispatcher, self).__init__(**kwargs)

    @handler("registered", target="*", override=True)
    def _on_registered(self, c, m):
        prefix = "/%s" % self.channel
        for h in component_handlers(c):
            if h.target and (h.target == prefix 
                             or h.target.startswith(prefix + "/")):
                self.paths.add(h.target)
                self.addHandler(h, h.channels, target=h.target)

    @handler("unregistered", target="*", override=True)
    def _on_unregistered(self, c, m):
        prefix = "/%s/" % self.channel
        for h in component_handlers(c):
            if h.target and (h.target == prefix 
                             or h.target.startswith(prefix)):
                self.paths.remove(h.target)
                self.removeHandler(h)
