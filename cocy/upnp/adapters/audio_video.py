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
"""
from cocy.upnp.adapters.adapter import upnp_service, UPnPServiceController,\
    upnp_state, Notification
from circuits_bricks.app.logger import Log
import logging
from time import time
from circuits_bricks.core.timers import Timer
from circuits.core.events import Event
from circuits.core.handlers import handler
from StringIO import StringIO
from xml.etree.ElementTree import Element, QName, ElementTree, SubElement
from cocy.upnp import UPNP_AVT_EVENT_NS

class UPnPCombinedEventsServiceController(UPnPServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(UPnPCombinedEventsServiceController, self).__init__\
            (adapter, device_path, service, service_id)
        self._changes = dict()
        self._updates_locked = False
        
    @upnp_state(evented_by="*")
    def LastChange(self):
        writer = StringIO()
        root = Element(QName(UPNP_AVT_EVENT_NS, "Event"))
        inst = SubElement(root, QName(UPNP_AVT_EVENT_NS, "InstanceID"), 
                                      { "val": "0" })
        for name, value in self._changes.items():
            SubElement(inst, QName(UPNP_AVT_EVENT_NS, name), { "val": value })
        ElementTree(root).write(writer, encoding="utf-8")
        return writer.getvalue()

    def addChange(self, variable, value):
        self._changes[variable] = value
        if not self._updates_locked:
            self._send_changes()

    def _send_changes(self):
        if len(self._changes) == 0:
            return
        self.fire(Notification({ "LastChange": self.LastChange() }),
                  self.notification_channel)
        self._changes.clear()
        Timer(0.2, Event.create("UnlockUpdates"), self).register(self)
        self._updates_locked = True

    @handler("unlock_updates")
    def _on_unlock_updates(self, *args):
        self._updates_locked = False
        self._send_changes()


class RenderingController(UPnPServiceController):
    
    volume = 25
    
    def __init__(self, adapter, device_path, service, service_id):
        super(RenderingController, self).__init__\
            (adapter, device_path, service, service_id)
        self._target = None

    @upnp_service
    def GetVolume(self, **kwargs):
        self.fire(Log(logging.DEBUG, "GetVolume called"), "logger")
        return [("CurrentVolume", str(self.volume))]

class ConnectionManagerController(UPnPServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(ConnectionManagerController, self).__init__\
            (adapter, device_path, service, service_id)
        self._target = None

    @upnp_service
    def GetProtocolInfo(self, **kwargs):
        self.fire(Log(logging.DEBUG, "GetProtocolInfo called"), "logger")
        return [("Source", ""),
                ("Sink", "http-get:*:audio/mpeg:*")]


class AVTransportController(UPnPCombinedEventsServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(AVTransportController, self).__init__\
            (adapter, device_path, service, service_id)
        self._target = None
        self._transport_state = "STOPPED"

    @upnp_service
    def GetTransportInfo(self, **kwargs):
        self.fire(Log(logging.DEBUG, "GetTransportInfo called"), "logger")
        return [("CurrentTransportState", self._transport_state),
                ("CurrentTransportStatus", "OK"),
                ("CurrentSpeed", "1")]

    @upnp_service
    def GetMediaInfo(self, **kwargs):
        self.fire(Log(logging.DEBUG, "GetMediaInfo called"), "logger")
        return [("NrTracks", "0"),
                ("MediaDuration", "0:00:00"),
                ("CurrentURI", ""),
                ("CurrentURIMetaData", ""),
                ("NextURI", "NOT_IMPLEMENTED"),
                ("NextURIMetaData", "NOT_IMPLEMENTED"),
                ("PlayMedium", "NONE"),
                ("RecordMedium", "NOT_IMPLEMENTED"),
                ("WriteStatus", "NOT_IMPLEMENTED")]

    @upnp_service
    def SetAVTransportURI(self, **kwargs):
        self.fire(Log(logging.DEBUG, 'AV Transport URI set to '
                      + kwargs["CurrentURI"]), "logger")
        self.addChange("AVTransportURI", kwargs["CurrentURI"])
        return []
    
    @upnp_service
    def Play(self, **kwargs):
        self.fire(Log(logging.DEBUG, "Play called"), "logger")
        self._transport_state = "PLAYING"
        self.addChange("TransportState", self._transport_state)
        return []
    
    @upnp_service
    def Stop(self, **kwargs):
        self.fire(Log(logging.DEBUG, "Stop called"), "logger")
        self._transport_state = "STOPPED"
        self.addChange("TransportState", self._transport_state)
        return []
    
    