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

from circuits.core.debugger import Debugger
from circuits.core.components import Component
import sys
from cocy.upnp import UPnPDeviceServer
import os
from circuits_bricks.app import Application
from media_renderer.renderer import DummyPlayer

CONFIG = {
    "logging": {
        "type": "TimedRotatingFile",
        "file": os.path.join("%(log_dir)s", "application.log"),
        "when": "midnight",
        "backupCount": 7,
        "level": "DEBUG",
    },
    "upnp": {
        "max-age": "1800",
    },
    "ui": {
        "port": "8877",
    },
}

class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, \
                  fevent=None, handler=None):
        sys.exit();

if __name__ == '__main__':

    application = Application("CoCy", CONFIG)
    Debugger().register(application)
    ErrorHandler().register(application)
    
#    # Build a portal as user interface
#    port = int(application.config.get("ui", "port", 0))
#    portal_server = BaseServer(("", port), channel="ui").register(application)
#    portal = Portal(portal_server, title="CoCy").register(application)
#    PortletsFactory().register(application)
#    dev_dir = UPnPDeviceDirectory().register(application)

    # The server    
    upnp_dev_server \
        = UPnPDeviceServer(application.app_dir).register(application)
    media_renderer = DummyPlayer().register(application)
    
    from circuits.tools import graph
    print graph(application)
    application.run()
