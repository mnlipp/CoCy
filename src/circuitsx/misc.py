"""
.. codeauthor: mnl
"""
#from circuits.core.manager import Manager
#from circuits.web.events import Request
#
## Fix circuits problems
#def fix_circuits():
#    _orig_fireEvent = Manager.fireEvent
#    def _fix_fired_request (self, event, channel=None):
#        if isinstance(event, Request) \
#            and not getattr(event, "_has_been_fixed", False):
#            event.success = "request_success", self.channel
#            event.failure = "request_failure", self.channel
#            event.filter = "request_filtered", self.channel
#            event.start = "request_started", self.channel
#            event.end = "request_completed", self.channel
#            event._has_been_fixed = True
#        return _orig_fireEvent (self, event, channel, target)
#    Manager.fireEvent = _fix_fired_request
#    Manager.fire = Manager.fireEvent
