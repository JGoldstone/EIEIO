from time import sleep

from utilities.log import LogEvent
from eieio.targets.unreal.live_link_message_retransmitting_thread import MessageRetransmitter

LIVE_LINK_TARGET_SETTLE_SECONDS = 3


class UnrealLiveLinkTarget(object):
    def __init__(self, host, port, queue, queue_wait_timeout=3):
        self._queue = queue
        self._retransmitting_thread = MessageRetransmitter(host, port, queue)
        self._retransmitting_thread.start()
        self.set_target_stimulus("deviceRGB", [0.0, 0.0, 0.0])

    def __del__(self):
        print('queued exit')
        self._queue.put('exit')

    def message_for_rgb(self, red, green, blue):
        return f"B,{red},F,{green},B,{blue}\r\n"

    def set_target_stimulus(self, colorspace, values, log=None):
        if colorspace.lower() == 'devicergb':
            if len(values) == 3:
                red, green, blue = values
                if log:
                    log.add(LogEvent.METER_OPTION_SETTING,
                            f"about to queue RGB of {red:.3f}, {green:.3f} {blue:.3f} for live link target")
                self._queue.put(self.message_for_rgb(red, green, blue))
                if log:
                    log.add(LogEvent.METER_OPTION_SETTING,
                            f"queued RGB of {red:.3f}, {green:.3f} {blue:.3f} for live link target")
                print("waiting for target to settle...", end='', flush=True)
                sleep(LIVE_LINK_TARGET_SETTLE_SECONDS)
                print("assuming target has settled", flush=True)
            else:
                raise RuntimeError(f"expected 3 values setting target RGB stimulus, but saw{len(values)}")
        else:
            raise RuntimeError(f"unhandled colorspace {colorspace} requested of Unreal Live Link target")
