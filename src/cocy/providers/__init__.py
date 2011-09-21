"""
.. codeauthor: mnl
"""
from circuits.core.components import BaseComponent
from abc import ABCMeta
from circuits.core.handlers import handler

class Manifest(object):
    """
    This class holds descriptive data about a provider, i.e. a 
    device or service that is to be made available in the network.
    
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
    def __init__(self, display_name, full_name = None,
                 manufacturer=None, model_number=None, description=None):
        self.display_name = display_name
        self.full_name = full_name
        self.manufacturer = manufacturer
        self.model_number = model_number
        self.description = description

    
class Provider(BaseComponent):
    """
    All components that want to be advertised in the network as providers of 
    some kind of service must inherited from this class. Note that components
    do not inherit from this class directly. Rather they inherit from
    one of the derived classes that further specify the kind of service
    that a component provides.
    """    
    __metaclass__ = ABCMeta
    
    def __init__(self, provider_manifest, **kwargs):
        """
        The constructor initializes a new instance with the manifest that
        is passed as parameter.
        
        :param provider_manifest: the manifest data
        :type provider_manifest: :class:`Manifest`
        
        :param kwargs: optional keyword arguments that are forwarded to
                       the underlying component class from the circuit 
                       framework
        """
        super(Provider, self).__init__(**kwargs)
        self._provider_manifest = provider_manifest
    
    def provider_manifest(self):
        """
        Return the provider's manifest.
        
        :rtype: :class:`Manifest`
        """
        return self._provider_manifest

    @handler("provider_query")
    def _on_provider_query(self, event):
        """
        Deliver this provider as result to query for providers.
        """
        return self
        
class BinarySwitch(Provider):
    """
    A :class:`BinarySwitch` represents anything that has an on and
    an off state that is to be controlled remotely.
    """
    __metaclass__ = ABCMeta
