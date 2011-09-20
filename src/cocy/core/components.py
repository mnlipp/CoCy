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
    __metaclass__ = ABCMeta
    
    """
    All components that want to be advertised in the network as providers of 
    some kind of service must inherited from this class. Note that components
    do not inherit from this class directly. Rather they inherit from
    one of the derived classes that further specify the kind of service
    that a component provides.
    """
    
    def __init__(self, provider_manifest, **kwargs):
        """
        Every instance has to provide a manifest that describes properties
        of the components. This manifest is passed as parameter to the 
        constructor.
        
        :param provider_manifest: the manifest data
        :type provider_manifest: Manifest
        
        :param kwargs: optional keyword arguments that are forwarded to
                       the underlying component class from the circuit 
                       framework
        """
        super(Provider, self).__init__(**kwargs)
        self._provider_manifest = provider_manifest
    
    def provider_manifest(self):
        """
        Return the provider's manifest.
        """
        return self._provider_manifest

    @handler("provider_query")
    def _on_provider_query(self, event):
        """
        Deliver this provider as result to query for providers.
        """
        return self
        
class BinarySwitch(Provider):
    __metaclass__ = ABCMeta
