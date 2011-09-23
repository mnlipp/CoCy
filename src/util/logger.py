"""
.. codeauthor: mnl

Based on the Logger component from app/log.
"""
from circuits.core.events import Event
from circuits.core.components import BaseComponent
import logging
import sys
from circuits.core.handlers import handler
import os

class Log(Event):
    """Log Event"""

    channel = "log"
    target = "logger"

    def __init__(self, *args, **kwargs):
        super(Log, self).__init__(*args, **kwargs)
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        self.file_name, self.line_number, self.func \
            = "(unknown file)", 0, "(unknown function)"
        # want to use loggig.currentframe(), but this expects one
        # call level more
        def cf():
            return logging.currentframe()
        try:
            frame = cf()
            co = frame.f_code
            self.file_name, self.line_number, self.func \
                = (co.co_filename, frame.f_lineno, co.co_name)
        except ValueError:
            pass

class Logger(BaseComponent):

    channel = "logger"

    def __init__(self, filename, name, type, level,
                 format=None, channel=channel):
        super(Logger, self).__init__(channel=channel)

        self._logger = logging.getLogger(name)

        type = type.lower()
        if type == "file":
            hdlr = logging.FileHandler(filename)
        elif type in ["winlog", "eventlog", "nteventlog"]:
            # Requires win32 extensions
            hdlr = logging.handlers.NTEventLogHandler(name, type="Application")
        elif type in ["syslog", "unix"]:
            hdlr = logging.handlers.SysLogHandler("/dev/log")
        elif type in ["stderr"]:
            hdlr = logging.StreamHandler(sys.stderr)
        else:
            raise ValueError

        format = name + "[%(module)s] %(levelname)s: %(message)s"
        dateFormat = ""
        self._logger.setLevel(level)
        if type == "file":
            format = "%(asctime)s " + format
            dateFormat = "%X"

        formatter = logging.Formatter(format,dateFormat)
        hdlr.setFormatter(formatter)
        self._logger.addHandler(hdlr)

    @handler("log")
    def _on_log(self, event, level, msg, *args, **kwargs):
        if not self._logger.isEnabledFor(level):
            return
        record = self._logger.makeRecord \
            (self.name, level, event.file_name, event.line_number,
             msg, args, None, event.func)
        self._logger.handle(record)
