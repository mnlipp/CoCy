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
from abc import ABCMeta
from circuits.core.handlers import handler
from circuits.core.events import Event

class Manifest(object):
    """
    This class holds descriptive data about a provider, i.e. a 
    device or service that is to be made available in the network.

    :param unique_id: every provider should provide a unique id
                      that persists across program restarts. If the
                      provider has no means to provide this id, it may
                      also be ``None``. However, in case of improper 
                      server shutdown, clients may then end up with 
                      seemingly knowing several instances of the provider.
    :type unique_id: string
    
    :param display_name: a user friendly name for the provider
    :type  display_name: string

    :param full_name: the full name of the component
    :type  full_name: string

    :param manufacturer: the manufacturer of the component
    :type  manufacturer: string

    :param model_number: the number of this particular model of the device
                         if several devices with the same full name exist
    :type  model_number: string

    :param description: a description of the device
    :type  description: string

    """
    def __init__(self, unique_id, display_name, full_name = None,
                 manufacturer=None, model_number=None, description=None):
        self._unique_id = unique_id
        self._display_name = display_name
        self._full_name = full_name
        self._manufacturer = manufacturer
        self._model_number = model_number
        self._description = description

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def display_name(self):
        return self._display_name

    @property
    def full_name(self):
        return self._full_name

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def model_number(self):
        return self._model_number

    @property
    def description(self):
        return self._description

    
class ProviderUpdated(Event):
    pass

    
class Provider(BaseComponent):
    """
    All components that want to be advertised in the network as providers of 
    some kind of service must inherited from this class. The class fulfills
    two tasks:
    
    - provide a manifest
    
    - respond to ``provider_query`` events that are used to detect
      providers
    """    
    __metaclass__ = ABCMeta
    
    def __init__(self, provider_manifest, **kwargs):
        """
        The constructor initializes a new instance with the manifest that
        is passed as parameter.
        
        :param provider_manifest: the manifest data
        :type provider_manifest: :class:`cocy.providers.Manifest`
        
        :param kwargs: optional keyword arguments that are forwarded to
                       the underlying component class from the circuit 
                       framework
        """
        super(Provider, self).__init__(**kwargs)
        self._provider_manifest = provider_manifest
        self._provider_state = dict()
        self._provider_changed = dict()
    
    @property
    def provider_manifest(self):
        """
        Return the provider's manifest.
        
        :rtype: :class:`cocy.providers.Manifest`
        """
        return self._provider_manifest

    @handler("provider_query")
    def _on_provider_query(self, event):
        """
        A handler for event ``provider_query`` that returns
        this provider.
        """
        return self
    
    def _publish_updates(self):
        if len(self._provider_changed) > 0:
            self.fire(ProviderUpdated(self, self._provider_changed))
        self._provider_changed = dict()


def evented(*args, **kwargs):

    def do_f(f, self, new_value, auto_publish=False):
        if not f.__name__ in self._provider_state \
            or self._provider_state[f.__name__] != new_value:
            self._provider_changed[f.__name__] = new_value
        self._provider_state[f.__name__] = new_value
        result = f(self, new_value)
        if auto_publish:
            self._publish_updates()
        return result
    
    if len(args) == 0 or not hasattr(args[0], "__call__"):
        # function to be wrapped isn't first parameter, re-wrap
        def wrapper(f):
            def decorator(self, new_value):
                do_f(f, self, new_value, *args, **kwargs)
            return decorator
        return wrapper
    else:
        # function to be wrapped is first parameter
        def decorator(self, new_value):
            do_f(args[0], self, new_value, **kwargs)
        return decorator
        

class BinarySwitch(Provider):
    """
    This class represents anything that has an on and
    an off state that is to be controlled remotely.
    """
    __metaclass__ = ABCMeta
    
    channel = "binary_switch"
    
    _state = False

    @property
    def state(self):
        return self._state

    @state.setter
    @evented(auto_publish=True)
    def state(self, state):
        self._state = state


class MediaPlayer(Provider):
    __metaclass__ = ABCMeta
    
    channel = "media_player"
    
    _state = "IDLE"
    _source = None
    
    @property
    def state(self):
        return self._state

    @state.setter
    @evented(auto_publish=True)
    def state(self, state):
        self._state = state

    @property
    def source(self):
        return self._source

    @source.setter
    @evented(auto_publish=True)
    def source(self, uri):
        self._source = uri

    @handler("load")
    def _on_load(self, uri):
        self.source = uri

    @handler("play")
    def _on_play(self):
        if self._source is None:
            return
        self.state = "PLAYING"
        
    @handler("stop")
    def _on_stop(self):
        self.state = "IDLE"
