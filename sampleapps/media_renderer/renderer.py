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
from cocy.providers import Manifest, MediaPlayer
from cocy import providers
from circuits.core.handlers import handler
from circuits_bricks.core.timers import Timer
import time
from circuits.core.events import Event
from xml import etree
from xml.etree.ElementTree import QName
from cocy.misc import duration_to_secs

class end_reached(Event):
    pass

class DummyPlayer(providers.MediaPlayer):
    '''
    classdocs
    '''

    manifest = Manifest("Dummy Player", "CoCy Dummy Media Player")

    def __init__(self):
        super(DummyPlayer, self).__init__(self.manifest)
        self._timer = None

    def supportedMediaTypes(self):
        return ["http-get:*:audio/mpeg:*", "http-get:*:audio/ogg:*",
                "http-get:*:audio/3gpp:*", "http-get:*:video/3gpp:*",
                "http-get:*:audio/3gpp2:*", "http-get:*:video/3gpp2:*"]
    
    @handler("provider_updated")
    def _on_provider_updated_handler(self, provider, changed):
        if "state" in changed:
            state = changed["state"]
            if state == "PLAYING":
                if self._timer:
                    self._timer.unregister()
                self._timer = Timer(self.current_track_duration, 
                                    end_reached()).register(self)
            elif state == "IDLE":
                if self._timer:
                    self._timer.unregister()

    @handler("play", override=True)
    def _on_play(self):
        if self.source is None:
            return
        desc = etree.ElementTree.fromstring(self.source_meta_data)
        from cocy.upnp import DIDL_LITE_NS
        duration = desc.find(str(QName(DIDL_LITE_NS, "item")) + "/"
                                 + str(QName(DIDL_LITE_NS, "res"))) \
                                 .get("duration")
        self.current_track_duration = duration_to_secs(duration)
        self.state = "PLAYING"

    @handler("end_reached")
    def _on_end_reached(self, event):
        if self._timer:
            self._timer.unregister()
            self._timer = None
        self.fire(MediaPlayer.end_of_media())

    def current_position(self):
        if self._timer is None:
            return None
        return self._current_track_duration - (self._timer.expiry - time.time())
