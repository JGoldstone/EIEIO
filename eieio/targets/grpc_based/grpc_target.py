# -*- coding: utf-8 -*-
"""
Targets controlled using grpc and protobuf messages
===================

Defines an abstract generic meter_desc base class and then a spectroradiometer subclass (but still abstract)

"""

import grpc
from services.target.nuke.target_pb2 import ChangeTargetColorRequest
from services.target.nuke.target_pb2_grpc import TargetColorChangingStub
from services.ports import PORT_GRPC_TARGET_COLOR_CHANGING

from eieio.targets.target_abstractions import TargetBase
from utilities.log import Log, LogEvent

__author__ = 'Joseph Goldstone'
__copyright__ = 'Copyright (C) 2021 Arnold & Richter Cine Technik GmbH & Co. Betriebs KG'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Joseph Goldstone'
__email__ = 'jgoldstone@arri.com'
__status__ = 'Experimental'

__all__ = [
    'GrpcControlledTarget'
]


class GrpcControlledTarget(TargetBase):
    def __init__(self, host, patch_name, log: Log, **kwargs):
        super(GrpcControlledTarget, self).__init__(host, patch_name, log, **kwargs)

    def set_target_stimulus(self, name, value, **kwargs):
        """Set the target's named stimulus (e.g. 'Constant1' for Nuke) to the RGB in value"""
        self.log.add(LogEvent.GRPC_ACTIVITY,
                     f"setting target stimulus `{name}' at "
                     f"{self.host}:{PORT_GRPC_TARGET_COLOR_CHANGING} to `{value}'",
                     'GrpcControlledTarget')
        with grpc.insecure_channel(f"{self.host}:{PORT_GRPC_TARGET_COLOR_CHANGING}") as channel:
            client = TargetColorChangingStub(channel)
            red, green, blue = value
            request = ChangeTargetColorRequest(patch_name=self.patch_name, red=red, green=green, blue=blue)
            response = client.ChangeTargetColor(request)
            details = f": {response.details}" if response.details else ''
            if response.changedOK:
                self.log.add(LogEvent.METER_OPTION_SETTING,
                             f"successfully set target color stimulus `{name}'{details}",
                             'GrpcControlledTarget')
            else:
                self.log.add(LogEvent.METER_OPTION_SETTING,
                             f"failed to set target color stimulus `{name}'{details}")
