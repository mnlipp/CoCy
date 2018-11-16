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
    upnp_state, upnp_notification, UPnPServiceError
from circuits_bricks.app.logger import log
import logging
from circuits_bricks.core.timers import Timer
from circuits.core.events import Event
from circuits.core.handlers import handler
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, QName, SubElement
from cocy.upnp import UPNP_AVT_EVENT_NS, UPNP_RCS_EVENT_NS
from cocy import misc
from cocy.misc import duration_to_secs, secs_to_duration

class UPnPCombinedEventsServiceController(UPnPServiceController):
    
    def __init__(self, adapter, device_path, service, service_id, event_ns):
        super(UPnPCombinedEventsServiceController, self).__init__\
            (adapter, device_path, service, service_id)
        self._event_ns = event_ns
        self._changes = dict()
        self._updates_locked = False
        
    @upnp_state(evented_by=None)
    def LastChange(self):
        root = Element(QName(self._event_ns, "Event"))
        inst = SubElement(root, QName(self._event_ns, "InstanceID"), 
                                      { "val": "0" })
        for name, value in self._changes.items():
            SubElement(inst, QName(self._event_ns, name), { "val": value })
        misc.set_ns_prefixes(root, { "": self._event_ns })
        return ElementTree.tostring(root, encoding="utf-8").decode("utf-8")

    def addChange(self, variable, value, auto_flush=True):
        self._changes[variable] = unicode(value)
        if auto_flush:
            self.flushChanges()

    def flushChanges(self):
        if self._updates_locked or len(self._changes) == 0:
            return
        self._updates_locked = True
        self.fire(upnp_notification({ "LastChange": self.LastChange() }),
                  self.notification_channel)
        self._changes.clear()
        Timer(0.2, Event.create("unlock_updates"), self).register(self)

    @handler("unlock_updates")
    def _on_unlock_updates(self, *args):
        self._updates_locked = False
        self.flushChanges()


class RenderingController(UPnPCombinedEventsServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(RenderingController, self).__init__\
            (adapter, device_path, service, service_id, UPNP_RCS_EVENT_NS)
        self._provider = adapter.provider
        self._target = None
        @handler("provider_updated", channel=self._provider.channel)
        def _on_provider_updated_handler(self, provider, changed):
            if provider != self._provider:
                return
            self._map_changes(changed)
        self.addHandler(_on_provider_updated_handler)

    def _map_changes(self, changed):
        for name, value in changed.items():
            if name == "volume":
                self.addChange("Volume", str(int(value*100)))
                continue
        
    @upnp_service
    def GetVolume(self, **kwargs):
        self.fire(log(logging.DEBUG, "GetVolume called"), "logger")
        return [("CurrentVolume", str(int(self._provider.volume * 100)))]

    @upnp_service
    def SetVolume(self, **kwargs):
        self.fire(log(logging.DEBUG, 'SetVolume to '
                      + kwargs["DesiredVolume"]), "logger")
        self.fire(Event.create("set_volume", 
                               int(kwargs["DesiredVolume"]) / 100.0),
                  self.parent.provider.channel)
        return []

    @upnp_service
    def GetVolumeDBRange(self, **kwargs):
        return [("MinValue", -85*256), ("MaxValue", 0)]

class ConnectionManagerController(UPnPServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(ConnectionManagerController, self).__init__\
            (adapter, device_path, service, service_id)
        self._target = None

    @upnp_state
    def CurrentConnectionIDs(self):
        return 0

    @upnp_service
    def GetProtocolInfo(self, **kwargs):
        self.fire(log(logging.DEBUG, "GetProtocolInfo called"), "logger")
        types = self.parent._provider.supportedMediaTypes()
        return [("Source", ""),
                ("Sink", ",".join(types))]

    @upnp_service
    def GetCurrentConnectionIDs(self, **kwargs):
        self.fire(log(logging.DEBUG, "GetCurrentConnectionIDs called"),
                  "logger")
        return [("GetCurrentConnectionIDs", self.CurrentConnectionIDs())]


class AVTransportController(UPnPCombinedEventsServiceController):
    
    def __init__(self, adapter, device_path, service, service_id):
        super(AVTransportController, self).__init__\
            (adapter, device_path, service, service_id, UPNP_AVT_EVENT_NS)
        self._provider = adapter.provider
        self._target = None
        self._transport_state = "STOPPED"
        @handler("provider_updated", channel=self._provider.channel)
        def _on_provider_updated_handler(self, provider, changed):
            if provider != self._provider:
                return
            self._map_changes(changed)
        self.addHandler(_on_provider_updated_handler)
        # @handler("end_of_media", channel=self._provider.channel)

    def _map_changes(self, changed):
        for name, value in changed.items():
            if name == "source":
                self.addChange("AVTransportURI", value, auto_flush=False)
                self.addChange("CurrentTrackURI", value, auto_flush=False)
                continue
            if name == "source_meta_data":
                self.addChange("AVTransportURIMetaData", value, 
                               auto_flush=False)
                self.addChange("CurrentTrackMetaData", value, auto_flush=False)
                continue
            if name == "next_source":
                self.addChange("NextAVTransportURI", value, auto_flush=False)
                continue
            if name == "next_source_meta_data":
                self.addChange("NextAVTransportURIMetaData", value, 
                               auto_flush=False)
                continue
            if name == "current_track_duration":
                self.addChange("CurrentTrackDuration", 
                               "NOT_IMPLEMENTED" if value is None \
                               else secs_to_duration(value), 
                               auto_flush=False)
                self.addChange("CurrentMediaDuration", 
                               "NOT_IMPLEMENTED" if value is None \
                               else secs_to_duration(value), 
                               auto_flush=False)
                continue
            if name == "state":
                if value == "PLAYING":
                    self._transport_state = "PLAYING"
                    self.addChange("TransportState", self._transport_state, 
                                   auto_flush=False)
                elif value == "IDLE":
                    self._transport_state = "STOPPED"
                    self.addChange("TransportState", self._transport_state, 
                                   auto_flush=False)
                elif value == "PAUSED":
                    self._transport_state = "PAUSED_PLAYBACK"
                    self.addChange("TransportState", self._transport_state, 
                                   auto_flush=False)
                elif value == "TRANSITIONING":
                    self._transport_state = "TRANSITIONING"
                    self.addChange("TransportState", self._transport_state, 
                                   auto_flush=False)
                continue
        self.flushChanges()
        
    @upnp_service
    def GetTransportInfo(self, **kwargs):
        self.fire(log(logging.DEBUG, "GetTransportInfo called"), "logger")
        return [("CurrentTransportState", self._transport_state),
                ("CurrentTransportStatus", "OK"),
                ("CurrentSpeed", "1")]

    @upnp_service
    def GetMediaInfo(self, **kwargs):
        self.fire(log(logging.DEBUG, "GetMediaInfo called"), "logger")
        return [("NrTracks", self._provider.tracks),
                ("MediaDuration", "NOT_IMPLEMENTED" \
                 if self._provider.current_track_duration is None \
                 else secs_to_duration \
                    (self._provider.current_track_duration)),
                ("CurrentURI", self._provider.source),
                ("CurrentURIMetaData", "NOT_IMPLEMENTED" \
                 if self._provider.source_meta_data is None \
                 else self._provider.source_meta_data),
                ("NextURI", self._provider.next_source),
                ("NextURIMetaData", "NOT_IMPLEMENTED" \
                 if self._provider.next_source_meta_data is None \
                 else self._provider.next_source_meta_data),
                ("PlayMedium", "NONE"),
                ("RecordMedium", "NOT_IMPLEMENTED"),
                ("WriteStatus", "NOT_IMPLEMENTED")]

    @upnp_service
    def GetPositionInfo(self, **kwargs):
        rel_pos = self._provider.current_position()
        self.fire(log(logging.DEBUG, "GetPositionInfo called"), "logger")
        info = [("Track", self._provider.current_track),
                ("TrackDuration", "NOT_IMPLEMENTED" \
                 if self._provider.current_track_duration is None \
                 else secs_to_duration \
                    (self._provider.current_track_duration)),
                ("TrackMetaData", "NOT_IMPLEMENTED" \
                 if self._provider.source_meta_data is None \
                 else self._provider.source_meta_data),
                ("TrackURI", self._provider.source),
                ("RelTime", "NOT_IMPLEMENTED" if rel_pos is None \
                 else secs_to_duration(rel_pos)),
                ("AbsTime", "NOT_IMPLEMENTED" if rel_pos is None \
                 else secs_to_duration(rel_pos)),
                ("RelCount", 2147483647 if rel_pos is None else rel_pos),
                ("AbsCount", 2147483647 if rel_pos is None else rel_pos)]
        return info

    @upnp_service
    def SetAVTransportURI(self, **kwargs):
        self.fire(log(logging.DEBUG, 'AV Transport URI set to '
                      + kwargs["CurrentURI"]), "logger")
        self.fire(Event.create("load", kwargs["CurrentURI"], 
                               kwargs["CurrentURIMetaData"]),
                  self.parent.provider.channel)
        return []
    
    @upnp_service
    def SetNextAVTransportURI(self, **kwargs):
        self.fire(log(logging.DEBUG, 'Next AV Transport URI set to '
                      + kwargs["NextURI"]), "logger")
        self.fire(Event.create("prepare_next", kwargs["NextURI"], 
                               kwargs["NextURIMetaData"]),
                  self.parent.provider.channel)
        return []
    
    @upnp_service
    def Play(self, **kwargs):
        self.fire(log(logging.DEBUG, "Play called"), "logger")
        self.fire(Event.create("play"),
                  self.parent.provider.channel)
        return []
    
    @upnp_service
    def Pause(self, **kwargs):
        self.fire(log(logging.DEBUG, "Pause called"), "logger")
        self.fire(Event.create("pause"),
                  self.parent.provider.channel)
        return []
    
    @upnp_service
    def Stop(self, **kwargs):
        self.fire(log(logging.DEBUG, "Stop called"), "logger")
        self.fire(Event.create("stop"),
                  self.parent.provider.channel)
        return []
    
    @upnp_service
    def Seek(self, **kwargs):
        if not (self._transport_state == "PLAYING" 
                or self._transport_state == "STOPPED"):
            raise UPnPServiceError(701) 
        unit = kwargs["Unit"]
        if unit != "REL_TIME" and unit != "ABS_TIME":
            self.fire(log(logging.DEBUG, "Seek called"), "logger")
            raise UPnPServiceError(710)
        target = kwargs["Target"]
        self.fire(log(logging.DEBUG, "Seek to " + target + " called"), "logger")
        target = duration_to_secs(target)
        self.fire(Event.create("seek", target),
                  self.parent.provider.channel)
        return []
    
