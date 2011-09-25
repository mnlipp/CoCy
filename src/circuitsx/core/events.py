# This file is part of the CoCy program.
# Copyright (C) 2011 Michael N. Lipp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''


.. codeauthor:: mnl
'''
#from circuits.core.events import Event
#
#class RetargetingEventMeta(type):
#    """
#    This is the meta class for RetargetingEvent. It makes sure that the
#    "channel" property of the RetargetingEvent is not overwritten by
#    a derived class. If the derived class defines a "channel" attribute,
#    it is mapped to "_channel" (which is checked by RetargetingEvent when
#    trying to get the event's channel.
#    """
#    def __new__(self, name, bases, dict):
#        if name != "RetargetingEvent" and dict.has_key("channel"):
#            channel = dict["channel"]
#            del dict["channel"]
#            dict["_channel"] = channel
#        return type.__new__(self, name, bases, dict)
#
#class RetargetingEvent(Event):
#    """
#    This subclass of Event clarifies the semantics of the "accompanying"
#    events specified with attributes "success", "failure", "filter", 
#    "start" and "end". 
#    
#    When an ordinary Event is fired, its target will be set as 
#    described in the documentation of Event. This "re-targeting" 
#    applies to the fired event only, not to the accompanying events.
#    
#    This class uses the target set when firing an event to adapt 
#    the targets of the accompanying events as well, if those targets 
#    are initially None. (An accompanying event's target will be
#    left as is if it is explicitly specified.)
#    """
#
#    __metaclass__ = RetargetingEventMeta
#    
#    _channel = None
#
#    def __init__(self, *args, **kwargs):
#        "See Event.__doc__ for signature."
#
#        super(RetargetingEvent, self).__init__(*args, **kwargs)
#        
#    def get_channel(self):
#        return self._channel or super(RetargetingEvent, self).channel
#    
#    def set_channel(self, channel):
#        self._channel = channel
#        if not isinstance(channel, tuple):
#            return
#        new_target = channel[0]
#        for attr_name in ["success", "failure", "filter", "start", "end"]:
#            cur_channel = self.__dict__.get(attr_name, None) \
#                or self.__class__.__dict__.get(attr_name, None)
#            if cur_channel == None:
#                continue
#            cur_target = None
#            if isinstance(cur_channel, tuple):
#                cur_channel, cur_target = cur_channel
#            if cur_target == None:
#                self.__dict__[attr_name] = (cur_channel, new_target)
#
#    channel = property(get_channel, set_channel)
