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

class DummyPlayer(providers.MediaPlayer):
    '''
    classdocs
    '''

    manifest = Manifest("Dummy Player", "CoCy Dummy Media Player")

    def __init__(self):
        super(DummyPlayer, self).__init__(self.manifest)
        self._timer = None

    @handler("provider_updated")
    def _on_provider_updated_handler(self, provider, changed):
        if "state" in changed:
            state = changed["state"]
            if state == "PLAYING":
                self.current_track_duration = 60
                if self._timer:
                    self._timer.unregister()
                self._timer = Timer(self.current_track_duration, 
                                    MediaPlayer.EndOfMedia()).register(self)
            elif state == "IDLE":
                if self._timer:
                    self._timer.unregister()

    def current_position(self):
        if self._timer is None:
            return None
        return self._current_track_duration - (self._timer.expiry - time.time())
