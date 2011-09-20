"""
.. codeauthor:: mnl
"""
from circuits.core.handlers import handler
from cocy.core.events import ProviderQuery, ProviderList
from circuits.core.components import BaseComponent

class ConfigurationMonitor(BaseComponent):

    def __init__(self):
        super(ConfigurationMonitor, self).__init__()
        self._config_id = 0
    
    @handler("started")
    def _on_started (self, component, mode):
        self.fireEvent(ProviderQuery())

    @handler("provider_query", filter=True, priority=-999)
    def _after_provider_query(self, event):
        providers = event.value.value
        if not isinstance(providers, list):
            providers = [providers]
        self._config_id += 1
        self.fireEvent(ProviderList(self._config_id, providers))
