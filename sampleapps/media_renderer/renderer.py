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
from cocy.providers import Manifest
from cocy import providers
from circuits.core.handlers import handler
import time
from circuits_bricks.core.timers import Timer
from circuits.core.events import Event

class DummyPlayer(providers.MediaPlayer):
    '''
    classdocs
    '''

    manifest = Manifest("Dummy Player", "CoCy Dummy Media Player")

    def __init__(self):
        super(DummyPlayer, self).__init__(self.manifest)
        self._timer = None

    @handler("play", override=True)
    def _on_play(self):
        super(DummyPlayer, self)._on_play()
        if self._source is None:
            return
        self.current_track_duration = 60
        self._timer = Timer(self._current_track_duration, 
                            Event.create("Stop")).register(self)

    @handler("stop", override=True)
    def _on_stop(self):
        super(DummyPlayer, self)._on_stop()
        if self._timer is not None:
            self._timer.unregister()
            self._timer = None

    def current_position(self):
        if self._timer is None:
            return None
        return self._current_track_duration - (self._timer.expiry - time.time())
