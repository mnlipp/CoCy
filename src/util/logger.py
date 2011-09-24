"""
.. codeauthor: mnl
"""
from circuits.core.events import Event
from circuits.core.components import BaseComponent
import logging
import sys
from circuits.core.handlers import handler
import socket
from logging import FileHandler, StreamHandler
from logging.handlers import WatchedFileHandler, RotatingFileHandler,\
    TimedRotatingFileHandler, NTEventLogHandler, SysLogHandler

class Log(Event):
    """
    This class represents a log message that is to be written to the log.
    """

    channel = "log"
    target = "logger"

    def __init__(self, level, message):
        """
        The constructor creates a new event that writes the message with
        the given level to the log.
        
        :param level: the level
        :type level: a level as defined in module ``logging``
        
        :param message: the message to be written
        :type message: string
        """
        super(Log, self).__init__(level, message)
        # Find the stack frame of the caller so that we can note the source
        # file name, line number and function name.
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

class LogSupport:
    """
    While using ``Log`` events fits nicely in the event based framework, it 
    has the drawback of delaying log messages. As the log events are appended
    at the end of the event queue, quite a lot of things may be executed
    before the log event is eventually handled.

    If more immediate logging is needed, the ``logging.Logger`` used by 
    the ``Logger`` component can be provided to other components. 
    Any component that inherits from ``LogSupport`` can access the 
    basic logger as instance variable ``logger``.
    
    Note that in order for the instance variable ``logger`` to be 
    initialized properly, the ``Logger`` component must have been
    created first.
    
    :ivar logger: the provided logger
    """
    logger = logging.getLogger()

class Logger(BaseComponent):
    """
    The ``Logger`` component is a wrapper around a standard python
    logger that is allocated once and used throughout the whole
    application. This is different from the usual usage pattern 
    of the python logging package where a logger is allocated for 
    each module.
    
    In order to write a message to the log, a :class:`util.logger.Log` 
    event must be fired.
    """

    channel = "logger"

    def __init__(self, filename, name, type, level,
                 handler_args = dict(), format=None, channel=channel):
        """
        The constructor initializes the logger component according
        to the given parameters.
        
        :param filename: the name of the log file (or None if not logging
                             to a file)
        :type filename: string
        
        :param name: the name of the logger, inserted in the log messages
        :type name: string
        
        :param type: the type of logger to be used
        :type type: string, one of "file", "watchedFile", "rotatingFile",
                    "timedRotatingFile", "NTEventLog", "syslog", "stderr"
                    
        :param level: the debug level to log
        :type level: integer, see predefined levels in module ``logging``
        
        :param handler_args: keyword arguments passed to the logging handler
                             constructor
        :type handler_args: dict
        
        :param format: the format for the log messages
        :type format: string
        
        :param channel: the channel
        """
        super(Logger, self).__init__(channel=channel)

        self._logger = logging.getLogger(name)

        type = type.lower()
        
        known_dict = {"file": ["mode", "encoding", "delay"],
                      "watchedfile": ["mode", "encoding", "delay"],
                      "rotatingfile": ["mode", "maxBytes", "backupCount",
                                       "encoding", "delay"],
                      "timedrotatingfile": ["when", "interval", "backupCount",
                                            "encoding", "delay", "utc"],
                      "nteventlog": ["dllname", "logtype"],
                      "syslog": ["address", "facility", "socktype"],
                      "stderr": []}
        if not known_dict.has_key(type):
            raise ValueError
        known_args = known_dict[type]
        kwargs = dict()
        for arg in handler_args.keys():
            if arg in known_args:
                if arg in ["delay", "utc"]:
                    kwargs[arg] = (handler_args[arg] == "True")
                elif arg in ["maxBytes", "backupCount", "interval", "port"]:
                    kwargs[arg] = int(handler_args[arg])
                else:
                    kwargs[arg] = handler_args[arg]
        
        if type == "file":
            hdlr = FileHandler(filename, **kwargs)
        elif type in ["watchedfile"]:
            def h(mode = 'a', encoding = None, delay = False):
                return WatchedFileHandler \
                    (filename, mode, encoding, delay)
            hdlr = h(**kwargs)
        elif type in ["rotatingfile"]:
            hdlr = RotatingFileHandler(filename, **kwargs)
        elif type in ["timedrotatingfile"]:
            hdlr = TimedRotatingFileHandler(filename, **kwargs)
        elif type in ["nteventlog"]:
            # Requires win32 extensions
            hdlr = NTEventLogHandler(filename, **kwargs)
        elif type in ["syslog"]:
            if kwargs.has_key("address"):
                address = kwargs.get("address")
                hp = address.split(":", 2)
                if len(hp) > 1:
                    kwargs["address"] = (hp[0], int(hp[1]))
            else:
                kwargs["address"] = "/dev/log"
            if kwargs.has_key("socktype"):
                if kwargs["socktype"].lower() == "tcp":
                    kwargs["socktype"] = socket.SOCK_STREAM
                else:
                    kwargs["socktype"] = socket.SOCK_DGRAM
            hdlr = SysLogHandler(**kwargs)
        elif type in ["stderr"]:
            hdlr = StreamHandler(sys.stderr, **kwargs)
        else:
            raise ValueError
        
        self._logger.setLevel(level)
        if not format:
            format = name + "[%(module)s] %(levelname)s: %(message)s"
            if type in ["file", "watchedfile", 
                        "rotatingfile", "timedrotatingfile"]:
                format = "%(asctime)s " + format

        formatter = logging.Formatter(format)
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

    @handler("registered", target="*")
    def _on_registered(self, component, manager):
        if isinstance(component, LogSupport):
            component.logger = self._logger
