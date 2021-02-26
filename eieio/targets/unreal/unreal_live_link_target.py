from eieio.targets.unreal.message_retransmitting_thread import MessageRetransmitter

class UnrealLiveLinkTarget(object):
    def __init__(self, host, port, queue, queue_wait_timeout=3):
        self._queue = queue
        self._retransmitting_thread = MessageRetransmitter(host, port, queue)
        self._retransmitting_thread.start()

    def __del__(self):
        print('queued exit')
        self._queue.put('exit')

    def message_for_rgb(self, red, green, blue):
        return f"B,{red},F,{green},B,{blue}\r\n"

    def set_target_stimulus(self, colorspace, values):
        if colorspace.lower() == 'devicergb':
            if len(values) == 3:
                red, green, blue = values
                self._queue.put(self.message_for_rgb(red, green, blue))
            else:
                raise RuntimeError(f"expected 3 values setting target RGB stimulus, but saw{len(values)}")
        else:
            raise RuntimeError(f"unhandled colorspace {colorspace} requested of Unreal Live Link target")
