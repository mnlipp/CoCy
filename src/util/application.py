"""
.. codeauthor: mnl
"""
from circuits.core.components import BaseComponent
import os
from util.config import Configuration
from util.logger import Logger, Log
import logging

class Application(BaseComponent):

    channel="application"

    def __init__(self, name, initial_config=None, defaults=None):
        super(Application, self).__init__()
        self._app_name = name
        self._conf_dir = os.path.expanduser('~/.%s' % name)
        if not os.path.exists(self._conf_dir):
            os.makedirs(self._conf_dir)
        if not defaults:
            defaults = dict()
        defaults['config_dir'] = self._conf_dir
        self._config = Configuration \
            (os.path.join(self._conf_dir, 'config'), 
             initial_config = initial_config,
             defaults = defaults).register(self);
        # Create Logger Component using the values from the configuration
        logtype = self._config.get("logging", "type", "stderr")
        loglevel = self._config.get("logging", "level", "INFO")
        loglevel = logging.getLevelName(loglevel)
        logfile = self._config.get("logging", "file", "/dev/null")
        if not os.path.abspath(logfile):
            logfile = os.path.join(self._conf_dir, logfile)
        self._log = Logger(logfile, name, logtype, loglevel).register(self)
        self.fire(Log(logging.INFO, 'Application ' + name + " started"))
    