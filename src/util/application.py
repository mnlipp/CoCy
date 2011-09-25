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
"""
.. codeauthor:: mnl
"""
from circuits.core.components import BaseComponent
import os
from util.config import Configuration
from util.logger import Logger, Log
import logging

DEFAULT_CONFIG = {
    "logging": {
        "type": "file",
        "file": os.path.join("%(log_dir)s", "application.log"),
        "level": "DEBUG",
    }
}

class Application(BaseComponent):
    """
    The application component is intended to be used as root component
    of an application. It creates a :class:`util.config.Configuration`
    and a :class:`util.logger.Logger` child component.
    
    The ``Application`` component creates an application directory 
    (as hidden directory
    in the user's home directory, using the provided application name).
    The configuration is stored as file ``config`` in that directory.
    
    The ``Logger`` is configured as specified by the configuration.
    The default configuration specifies a logger that logs to a 
    file ``application.log`` in the application directory. 
    """
    
    channel="application"

    def __init__(self, name, initial_config=None, defaults=None):
        super(Application, self).__init__()
        self._app_name = name
        self._app_dir = os.path.expanduser('~/.%s' % name)
        self._config_dir = self._app_dir
        self._log_dir = self._app_dir
        
        if not defaults:
            defaults = dict()
        if not defaults.has_key('app_dir'):
            defaults['app_dir'] = self._app_dir
        if not defaults.has_key('config_dir'):
            defaults['config_dir'] = self._config_dir
        if not defaults.has_key('log_dir'):
            defaults['log_dir'] = self._log_dir

        if not initial_config:
            initial_config = DEFAULT_CONFIG

        if not os.path.exists(self._config_dir):
            os.makedirs(self._config_dir)
        self._config = Configuration \
            (os.path.join(self._config_dir, 'config'),
             initial_config, defaults).register(self);

        # Create Logger Component using the values from the configuration
        log_opts = dict()
        for opt in self._config.options("logging"):
            log_opts[opt] = self._config.get("logging", opt)
        logtype = log_opts.get("type", "stderr")
        loglevel = log_opts.get("level", "INFO")
        loglevel = logging.getLevelName(loglevel)
        logfile = log_opts.get("file", None)
        if logfile and not os.path.abspath(logfile):
            logfile = os.path.join(self._config_dir, logfile)
        self._log = Logger(logfile, name, logtype, loglevel,
                           handler_args=log_opts).register(self)
        self.fire(Log(logging.INFO, 'Application ' + name + " started"))

    @property
    def app_dir(self):
        return self._config_dir
