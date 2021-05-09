# Things on top of that which should be in a spectral_measurement file
# spectral_measurement start time
# spectral_measurement end time
# user running spectral_measurement
# spectral_measurement app name
# spectral_measurement app version
# - and shared library or extension versions
from datetime import datetime
from enum import IntFlag


class LogEvent(IntFlag):
    # n.b. these must be kept in sync with LogOptions in i1ProAdapterUtils.h
    # generic events
    NOTHING = 0
    EXTERNAL_API_ENTRY = (1 << 0)
    INTERNAL_API_ENTRY = (1 << 1)
    RESOURCE_ADDITIONS = (1 << 2)
    RESOURCE_DELETIONS = (1 << 3)
    GRPC_ACTIVITY = (1 << 4)
    LOW_LEVEL_ERRORS = (1 << 5)
    # meter-related events
    METER_OPTION_SETTING = (1 << 10)
    METER_OPTION_RETRIEVAL = (1 << 11)
    METER_STATUS = (1 << 12)
    METER_CALIBRATION = (1 << 13)
    METER_CONFIGURATION = (1 << 14)
    METER_TRIGGER = (1 << 15)
    METER_SPECTRAL_RETRIEVAL = (1 << 16)
    METER_COLORIMETRIC_RETRIEVAL = (1 << 17)
    # target-related events
    TARGET_OPTION_SETTING = (1 << 20)


class Log(object):
    def __init__(self):
        self._event_mask = LogEvent.NOTHING

    @staticmethod
    def timestamp():
        return datetime.now().strftime('%a %H:%M:%S.%f')

    @property
    def event_mask(self):
        return self._event_mask

    @event_mask.setter
    def event_mask(self, value):
        self._event_mask = value

    def add(self, event_mask, what, where=None, context=None):
        if event_mask & self.event_mask:
            padded_where = f" {where}" if where else ''
            padded_context = f" ({context})" if context else ''
            print(f"[{Log.timestamp()}{padded_where}] {what}{padded_context}", flush=True)
