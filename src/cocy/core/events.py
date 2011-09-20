"""
.. codeauthor:: mnl
"""
from circuits.core.events import Event

class ProviderQuery(Event):
    '''This event is sent in order to collect all
    components that want to advertise their capabilities. A component
    must return self as result of the handler. 
    '''

    channel = "provider_query"

class ProviderList(Event):
    """Informs about the configured providers. 

    args: configuration id, list of tuples (BaseComponent, ManifestObject)
    """
    
    channel = "provider_list"
    