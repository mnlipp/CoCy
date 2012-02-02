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
from circuits.core.handlers import handler
from circuits.core.components import BaseComponent
from circuits.core.events import Event
import os
try:
    import ConfigParser
except ImportError:
    import ConfigParser

class ConfigValue(Event):
    """
    This event informs about the change of a configuration value.
    """
    
    channel = "config_value"
    
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
        super(ConfigValue, self).__init__(section, option, value)

class EmitConfig(Event):
    """
    This event causes the ``Configuration`` to emit the configuration
    values.
    """
    
    channel = "emit_config"
    target = "configuration"


class Configuration(BaseComponent):
    """
    This component provides a repository for configuration values.
    
    Configuration values are propagated on the component's channel
    (defaults to "configuration")
    as :class:`util.config.ConfigValue` objects. Every 
    received event is merged with the already existing configuration 
    and saved in an ini-style configuration file.
    
    Components that depend on configuration values define handlers
    for ``ConfigValue`` objects as well 
    and adapt themselves to the values propagated.
    
    During bootstrap, the configuration values have to be restored
    from the values in the configuration file. This cannot be done
    before all components have been created, but must be done before
    the application is actually started. ``Configuration``
    therefore defines a filter for the "started" event with priority 999.
    When the filter is triggered, it postpones the "started" event
    and emits all current configuration values before it.
    
    If your application requires a different behavior, you can also
    fire a :class:`util.config.EmitValues` event or call
    mathod ``emit_values``. This causes the 
    :class:`util.config.Configuration` to emit the configuration values 
    immediately. If this event is received before the "started" event, no
    configurations values will be fired in response to the "started" event.    
    """
    
    channel = "configuration"
    
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
        self._emit_done = False

        self._filename = filename
        self._config = ConfigParser.SafeConfigParser(defaults=defaults)
        self._config.optionxform = str
        if os.path.exists(filename):
            self._config.read(filename)
        modified = False
        for section in initial_config:
            if not self._config.has_section(section):
                self._config.add_section(section)
                for option, value in initial_config[section].items():
                    if not self._config.has_option(section, option):
                        self._config.set(section, option, str(value))
                        modified = True
        if modified:
            with open(filename, "w") as f:
                self._config.write(f)

    def emit_values(self):
        for section in self._config.sections():
            for option in self._config.options(section):
                self.fire(ConfigValue
                          (section, option, self._config.get(section, option)))
        self._emit_done = True

    @handler("emit_config")
    def _on_emit_config(self):
        self.emit_values()

    @handler("started", target="*", filter=True, priority=999)
    def _on_started(self, event, component, mode):
        if not self._emit_done:
            self.emit_values()
            self.fire(event)
            return True

    @handler("config_value")
    def _on_config_value(self, section, option, value):
        if self._config.has_option(section, option):
            if self._config.get(section, option) == str(value):
                return
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, str(value))
        with open(self._filename, "w") as f:
            self._config.write(f)

    def options(self, section):
        return self._config.options(section)

    def get(self, section, option, default=None):
        if self._config.has_option(section, option):
            return self._config.get(section, option)
        else:
            return default
