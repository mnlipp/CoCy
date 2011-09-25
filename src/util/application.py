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
