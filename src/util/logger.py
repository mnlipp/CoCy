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
    the ``Logger`` component is made available to components that inherit
    from ``LogSupport`` as a property.
    
    :ivar logger: the ``logging.Logger`` injected into the component
                  that inherits from ``LogSupport``
    
    Note that the ``logger`` property is set by the ``Logger``
    component when a new component is registered. In order to benefit
    from ``LogSupport`` the ``Logger`` component must therefore have
    been created and registered first. Also, the ``logger`` property
    is only available after the component that inherits from
    ``LogSupport`` has been registered; it can therefore not be used
    e.g. in the constructor.
    """
    logger = logging.getLogger()
    _logger_channel_selection = "logger"
    
    def __init__(self, logger_channel = "logger"):
        """
        ``LogSupport`` serves mainly as a marker interface. In environments
        where multiple ``Logger`` components exist, however, the question
        arises which ``Logger`` assigns its ``logging.Logger`` to the
        component. The constructor therefore supports the specification
        of a selection property. A ``Logger`` component assigns its
        ``logging.Logger`` only if that property matches its channel 
        property.
        """
        self._logger_channel_selection = logger_channel

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
                 format=None, handler_args = dict(), 
                 handler=None, channel=channel):
        """
        The constructor initializes the logger component according
        to the given parameters.
        
        :param filename: the name of the log file (or ``None`` if not logging
                             to a file)
        :type filename: string
        
        :param name: the name of the logger, inserted in the log messages
                     (usually the application's name)
        :type name: string
        
        :param type: the type of handler to be used
        :type type: string, one of "file", "WatchedFile", "RotatingFile",
                    "TimedRotatingFile", "NTEventLog", "Syslog", "Stderr"
                    
        :param level: the debug level to log
        :type level: integer, see predefined levels in module ``logging``
        
        :param format: the format for the log messages
        :type format: string
        
        :param handler_args: keyword arguments passed to the logging handler
                             constructor
        :type handler_args: dict

        :param handler: a ``logging.Handler`` that is to
            be used by the component instead of creating its own based
            on ``type`` and ``handler_args``
        :type handler: ``logging.Handler``
        
        :param channel: the channel
        """
        super(Logger, self).__init__(channel=channel)

        self._logger = logging.getLogger(name)

        if not handler:
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
                handler = FileHandler(filename, **kwargs)
            elif type in ["watchedfile"]:
                def h(mode = 'a', encoding = None, delay = False):
                    return WatchedFileHandler \
                        (filename, mode, encoding, delay)
                handler = h(**kwargs)
            elif type in ["rotatingfile"]:
                handler = RotatingFileHandler(filename, **kwargs)
            elif type in ["timedrotatingfile"]:
                handler = TimedRotatingFileHandler(filename, **kwargs)
            elif type in ["nteventlog"]:
                # Requires win32 extensions
                handler = NTEventLogHandler(filename, **kwargs)
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
                handler = SysLogHandler(**kwargs)
            elif type in ["stderr"]:
                handler = StreamHandler(sys.stderr, **kwargs)
            else:
                raise ValueError
        
        self._logger.setLevel(level)
        if not format:
            format = name + "[%(module)s] %(levelname)s: %(message)s"
            if type in ["file", "watchedfile", 
                        "rotatingfile", "timedrotatingfile"]:
                format = "%(asctime)s " + format

        formatter = logging.Formatter(format)
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

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
        if isinstance(component, LogSupport) \
            and component._logger_channel_selection == self.channel:
            component.logger = self._logger
