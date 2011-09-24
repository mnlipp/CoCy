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
        log_opts = dict()
        for opt in self._config.options("logging"):
            log_opts[opt] = self._config.get("logging", opt)
        logtype = log_opts.get("type", "stderr")
        loglevel = log_opts.get("level", "INFO")
        loglevel = logging.getLevelName(loglevel)
        logfile = log_opts.get("file", None)
        if logfile and not os.path.abspath(logfile):
            logfile = os.path.join(self._conf_dir, logfile)
        self._log = Logger(logfile, name, logtype, loglevel,
                           handler_args=log_opts).register(self)
        self.fire(Log(logging.INFO, 'Application ' + name + " started"))

    @property
    def config_dir(self):
        return self._conf_dir
