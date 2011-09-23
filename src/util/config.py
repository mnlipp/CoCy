"""
.. codeauthor: mnl
"""
from circuits.core.components import BaseComponent
from circuits.core.events import Event
import os
try:
    import ConfigParser
except ImportError:
    import ConfigParser

class ConfigurationEvent(Event):
    """
    This event informs about the change of a configuration value.
    """
    def __init__(self, section, option, value):
        """
        The constructor initializes a new instance with the given
        parameters
        
        :param section: the section the configuration value belongs to
        :type section: string
        :param option: the name of the configuration value that has changed
        :type option: string
        :param value: the new value
        :type value: string 
        """
        super(ConfigurationEvent, self).__init__(section, option, value)


class Configuration(BaseComponent):
    """
    This component provides a repository for configuration values.
    
    Configuration values are propagated on the component's channel
    (defaults to "config")
    as :class:`util.config.ConfigurationEvent` objects. Every 
    received event is merged with the already existing configuration 
    and saved in an ini-style configuration file.
    
    Components that depend on configuration values define handlers
    for ``ConfigurationEvent`` objects as well 
    and adapt themselves to the values propagated.
    
    During bootstrap, the configuration values have to be restored
    from the values in the configuration file. This cannot be done
    before all components have been created, but must be done before
    the application is actually started. ``Configuration``
    therefore defines a filter for the "started" event with priority 999.
    When the filter is triggered, it postpones the "started" event
    and emits all current configuration values before it.
    
    If your application requires a different behavior, you can also
    fire a :class:`util.config.EmitConfiguration` event. This causes the 
    :class:`util.config.Configuration` to emit the configuration values 
    immediately. If this event is received before the "started" event, no
    configurations values will be fired in response to the "startup" event.    
    """
    
    channel = "config"
    
    def __init__(self, filename, initial_config=None, 
                 defaults=None, channel=channel):
        """
        The constructor creates a new configuration using the given
        parameters.
        
        :param filename: the name of the file that is used to store the
                         configuration. If the file does not exist
                         it will be created.
        :type filename: string
        :param initial_config: a dict of name/section pairs, each section being
                               a dict of option/value pairs that is used
                               to initialize the configuration if no existing
                               configuration file is found
        :type initial_config: dict of dicts
        :param defaults: defaults passed to to the ConfigParser
        :param channel: the channel to be used by this ``Configuration``
                        (defaults to "config")
        """
        super(Configuration, self).__init__(channel=channel)

        self._filename = filename
        self._config = ConfigParser.SafeConfigParser(defaults=defaults)
        if os.path.exists(filename):
            self._config.read(filename)
        else:
            for section in initial_config:
                if not self._config.has_section(section):
                    self._config.add_section(section)
                    for option, value in initial_config[section].items():
                        self._config.set(section, option, value)
            with open(filename, "w") as f:
                self._config.write(f)

    def get(self, section, option, default=None):
        if self._config.has_option(section, option):
            return self._config.get(section, option)
        else:
            return default
