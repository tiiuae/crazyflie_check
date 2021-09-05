# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2021 Bitcraze AB
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
import struct
import time

import numpy as np

import cflib.crtp
from cflib.crtp.crtpstack import CRTPPacket
from cflib.crtp.crtpstack import CRTPPort

def latency(uri, packet_size=8, count=500):
    link = cflib.crtp.get_link_driver(uri)
    # # wait until no more packets in queue
    # while True:
    #     pk = link.receive_packet(0.5)
    #     print(pk)
    #     if not pk or pk.header == 0xFF:
    #         break

    pk = CRTPPacket()
    pk.set_header(CRTPPort.LINKCTRL, 0)  # Echo channel

    latencies = []
    for i in range(count):
        pk.data = build_data(i, packet_size)

        start_time = time.time()
        link.send_packet(pk)
        while True:
            pk_ack = link.receive_packet(-1)
            if pk_ack.port == CRTPPort.LINKCTRL and pk_ack.channel == 0:
                break
        end_time = time.time()

        # make sure we actually received the expected value
        i_recv, = struct.unpack('<I', pk_ack.data[0:4])
        assert(i == i_recv)
        latencies.append((end_time - start_time) * 1000)
    link.close()
    result = np.average(latencies)
    #print('Latency for {} (packet size {} B): {:.2f} ms'.format(uri, packet_size, result))
    return result

def build_data(i, packet_size):
    assert(packet_size % 4 == 0)
    repeats = packet_size // 4
    return struct.pack('<' + 'I'*repeats, *[i]*repeats)
