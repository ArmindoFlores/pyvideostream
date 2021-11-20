from __future__ import annotations

import logging
import os
import socket
import struct
import time
from functools import reduce
from typing import Callable, Optional


def ilen(iterable):
    return reduce(lambda s, _: s + 1, iterable, 0)


class Client:
    def __init__(self, host : str = "", port : int = 38080):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._address = host, port
        self._on_recv_callback : Optional[Callable[[bytes], None]] = None
        self._running = False
        self._max_fid = -1
        
    def set_on_receive_callback(self, callback: Optional[Callable[[bytes], None]]):
        self._on_recv_callback = callback
        
    def start(self):
        flag = socket.SO_REUSEADDR if os.name == "nt" else socket.SO_REUSEPORT
        self._socket.setsockopt(socket.SOL_SOCKET, flag, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.bind(self._address)
        
        logging.info("Starting receiver loop")
        
        frames = {}
        self._max_fid = 0
        self._running = True
        while self._running:
            # Receive a subframe
            data, _ = self._socket.recvfrom(2048)
            result = self.parse_frame_data(data, frames)
            if self._on_recv_callback is not None and result is not None:
                # If a frame has been assembled, call the callback function
                self._on_recv_callback(result)
            
            # Check for frames that have been dropped
            t = time.time()
            to_drop = [key for key in frames if t - frames[key]["timestamp"] > 1]
            for key in to_drop:
                del frames[key]
            if len(to_drop): logging.info(f"Dropped {len(to_drop)} frames")
                
        logging.info("Exited receiver loop")
                
    def stop(self):
        self._running = False
        
    def parse_frame_data(self, framedata, frames):
        SIZE = struct.calcsize("!III")
        fid, i, total = struct.unpack("!III", framedata[:SIZE])
        
        # Check the validity of the subframe metadata
        if fid not in frames and fid < self._max_fid:
            return
        if fid > self._max_fid:
            self._max_fid = fid
        if i > total:
            return
        
        if fid not in frames:
            frames[fid] = {
                "timestamp": time.time(),
                "data": [None] * total
            }
            
        if i > len(frames[fid]["data"]):
            return
        
        frames[fid]["data"][i] = framedata[SIZE:]
        if ilen(filter(lambda x: x is None, frames[fid]["data"])) == 0:
            result = b"".join(frames[fid]["data"])
            del frames[fid]
            return result
        return None