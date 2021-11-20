import logging
import math
import os
import queue
import socket
import struct


class Server:
    def __init__(self, port: int = 38080):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._port = port
        self._frames: queue.Queue[bytes] = queue.Queue()
        self._running = False
        self._fid = 0
        
    def add_frame(self, frame: bytes):
        self._frames.put(frame)
        
    def start(self):
        # Allow other sockets to share the same port
        flag = socket.SO_REUSEADDR if os.name == "nt" else socket.SO_REUSEPORT
        self._socket.setsockopt(socket.SOL_SOCKET, flag, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        logging.info("Starting sender loop")
        
        self._running = True        
        while self._running:
            try:
                # Timeout after 1 second to make sure the loop exit condition is checked
                frame = self._frames.get(timeout=1)
                self.send_frame(frame)
                self._fid += 1
            except queue.Empty:
                pass
            
        logging.info("Exited sender loop")
            
    def stop(self):
        self._running = False
        
    def send_frame(self, frame: bytes):
        frame_size = len(frame)
        total_subframes = math.ceil(frame_size/1024)
        for i in range(total_subframes):
            identifier = struct.pack("!III", self._fid, i, total_subframes)
            self._socket.sendto(identifier + frame[i*1024:(i+1)*1024], ("<broadcast>", self._port))
