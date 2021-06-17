# -*- coding: utf-8 -*-
"""
Control Resolve as a color calibration target
===================

Defines a target 'client' that is actually a server: it feeds Resolve patch requests
once it accepts a connection from Resolve.

"""
import xml.etree.ElementTree as ET
import socket
from time import sleep

from eieio.targets.target_abstractions import TargetBase
from utilities.log import LogEvent
from services.ports import PORT_RESOLVE_TARGET_COLOR_CHANGING

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'ResolveTarget'
]

RESOLVE_PATCH_SETTLE_TIME = 0.5  # seconds


class ResolveTarget(TargetBase):
    def __init__(self, host, _, log, port=PORT_RESOLVE_TARGET_COLOR_CHANGING):
        super(ResolveTarget, self).__init__(host, None, log)
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"Created Resolve target with host {self.host}",
                     'ResolveTarget.__init__')
        self._port = None
        self.port = port
        self._server_socket = None
        self._client_socket = None
        self._address = None

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def server_socket(self):
        return self._server_socket

    @server_socket.setter
    def server_socket(self, value):
        self._server_socket = value

    @property
    def client_socket(self):
        return self._client_socket

    @client_socket.setter
    def client_socket(self, value):
        self._client_socket = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    def await_resolve_offering_patch_drawing(self):
        self.log.add(LogEvent.TARGET_OPTION_SETTING, "about to create internet stream socket")
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"about to bind socket to {socket.gethostname()}:{self.port}")
        self._server_socket.bind(('', self.port))
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"bound socket to {socket.gethostname()}:{self.port}")
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'about to listen to socket (0 backlog)')
        self._server_socket.listen(0)  # no backlog allowed
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'listening to socket')
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"about to wait for incoming connection to port {self.port}")
        self.client_socket, self.address = self._server_socket.accept()
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"accepted connection from host {self.address}")
        return

    def set_target_stimulus(self, _, value, **kwargs):
        """

        Parameters0
        ----------
        _ : str
            normally, name of the patch on the server. Not needed (or provided for) in their protocol
        value : tuple
            triplet of normalized numbers, 0.0 meaning a channel's darkest value, 1.0 the brightest
        log : Log
            EIEIO-style log for tracking activity
        kwargs : dict
            ignored

        """
        calibration = ET.Element('calibration')
        shapes = ET.SubElement(calibration, 'shapes')
        rect = ET.SubElement(shapes, 'rectangle')
        red_rep = f"{round(255 * value[0])}"
        green_rep = f"{round(255 * value[1])}"
        blue_rep = f"{round(255 * value[2])}"
        ET.SubElement(rect, 'color', {'red': red_rep, 'green': green_rep, 'blue': blue_rep})
        ET.SubElement(rect, 'geometry', {'x': '0.0', 'y': '0.0', 'cx': '1.0', 'cy': '1.0'})
        request = ET.tostring(calibration, encoding='utf-8', method='xml')
        # self.log.add(LogEvent.TARGET_OPTION_SETTING, f"request is \n---\n{request}\n---")
        request_len = len(request)
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"Resolve target color request for R={red_rep}, "
                                                     f"G={green_rep}, B={blue_rep} is {request_len} bytes long",
                     'ResolveTarget.set_target_stimulus)')
        request_len_be = request_len.to_bytes(4, "big")
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'sending request length (big-endian / network order)')
        self._client_socket.send(request_len_be)
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'sent target change request length')
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'sending target change request')
        self._client_socket.send(request)
        self.log.add(LogEvent.TARGET_OPTION_SETTING, 'sent target change request')
        self.log.add(LogEvent.TARGET_OPTION_SETTING, f"sleeping {RESOLVE_PATCH_SETTLE_TIME:.2f} seconds to let "
                     'Resolve change the color patch')
        sleep(RESOLVE_PATCH_SETTLE_TIME)  # because there's no end-to-end ack

    def __del__(self):
        if self._client_socket:
            termination_signal = -1
            termination_signal_bytes = termination_signal.to_bytes(4, byteorder='big', signed=True)
            self._client_socket.send(termination_signal_bytes)
