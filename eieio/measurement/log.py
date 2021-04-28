# Things on top of that which should be in a spectral_measurement file
# spectral_measurement start time
# spectral_measurement end time
# user running spectral_measurement
# spectral_measurement app name
# spectral_measurement app version
# - and shared library or extension versions
from datetime import datetime
from enum import Flag, auto


class LogEvent(Flag):
    NOTHING = auto()
    EXTERNAL_API_ENTRY = auto()
    INTERNAL_API_ENTRY = auto()
    REGISTRY_ACTIVITY = auto()
    OPTION_SETTING = auto()
    OPTION_RETRIEVAL = auto()
    TRIGGER = auto()
    SPECTRAL_RETRIEVAL = auto()
    COLORIMETRY_RETRIEVAL = auto()
    RESOURCE_ADDITIONS = auto()
    RESOURCE_DELETIONS = auto()


class MeasurementLog(object):
    def __init__(self):
        self._event_mask = LogEvent.NOTHING

    @property
    def event_mask(self):
        return self._event_mask

    @event_mask.setter
    def event_mask(self, value):
        self._event_mask = value

    def add(self, event_mask, what, where=None, context=None):
        if event_mask & self.event_mask:
            timestamp = datetime.now().strftime('%a %H:%M:%S.%f')
            padded_where = f" {where}" if where else ''
            padded_context = f" ({context})" if context else ''
            print(f"[{timestamp}{padded_where}] {what}{padded_context}", flush=True)
