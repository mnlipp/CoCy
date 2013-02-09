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
from cocy.upnp.adapters.adapter import UPnPDeviceAdapter
from cocy.providers import BinarySwitch, MediaPlayer
from cocy.upnp import UPNP_SERVICE_ID_PREFIX
from cocy.upnp.adapters.home_automation import BinarySwitchPowerController
from cocy.upnp.adapters.audio_video import RenderingController,\
    ConnectionManagerController, AVTransportController

UPnPDeviceAdapter.add_adapter \
    (BinarySwitch, UPnPDeviceAdapter.DeviceProperties \
     ("BinaryLight", 0.9, 1, 0,
      [("SwitchPower:1", UPNP_SERVICE_ID_PREFIX + "SwitchPower:1",
       BinarySwitchPowerController)],
      "_common_device_desc"))

UPnPDeviceAdapter.add_adapter \
    (MediaPlayer, UPnPDeviceAdapter.DeviceProperties \
     ("MediaRenderer", 1.0, 1, 0,
      [("RenderingControl:1", UPNP_SERVICE_ID_PREFIX + "RenderingControl:1",
        RenderingController),
       ("ConnectionManager:1", UPNP_SERVICE_ID_PREFIX + "ConnectionManager:1",
        ConnectionManagerController),
       ("AVTransport:1", UPNP_SERVICE_ID_PREFIX + "AVTransport:1",
        AVTransportController)],
      "_common_device_desc"))

#UPnPDeviceAdapter.add_adapter \
#    (MediaPlayer, UPnPDeviceAdapter.DeviceProperties \
#     ("MediaRenderer", 3, 1, 0,
#      [("RenderingControl:3", UPNP_SERVICE_ID_PREFIX + "RenderingControl:3",
#        RenderingController),
#       ("ConnectionManager:3", UPNP_SERVICE_ID_PREFIX + "ConnectionManager:3",
#        ConnectionManagerController),
#       ("AVTransport:3", UPNP_SERVICE_ID_PREFIX + "AVTransport:3",
#        AVTransportController)],
#      "_common_device_desc"))
