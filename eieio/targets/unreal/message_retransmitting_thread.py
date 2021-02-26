import socket
import queue
from threading import Thread

LIVE_LINK_LENS_HOST = '192.168.1.157'
LIVE_LINK_LENS_METADATA_PORT = 40123
QUEUE_PEEK_INTERVAL = 3


class MessageRetransmitter(Thread):
    def __init__(self, host, port, message_queue, poke_seconds=3.0, initial_message=None):
        super().__init__()
        self.message_queue = message_queue
        self.message = initial_message if initial_message else ''
        self.interval = poke_seconds
        self.host = host
        self.port = port
        self.transmission_thread = None

    def server_address(self):
        return self.host, self.port

    def loop_transmitting_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as local_socket:
            local_socket.settimeout(3.0)
            while True:
                print("in thread, in loop")
                print(f"thread sent {self.message}")
                bytes_sent = local_socket.sendto(self.message.encode(), self.server_address())
                print(f"{bytes_sent} bytes sent by thread")
                try:
                    self.message = self.message_queue.get(timeout=self.interval)
                    if self.message == 'exit':
                        break
                except queue.Empty:
                    print("nothing new for thread to do")

    def run(self):
        print("pre-run, maini thread")
        self.transmission_thread = Thread(target=self.loop_transmitting_message)
        self.transmission_thread.start()
        self.transmission_thread.join()
        print("main thread, post-run")


if __name__ == '__main__':
    our_queue = queue.Queue(10)
    mrt = MessageRetransmitter(LIVE_LINK_LENS_HOST, LIVE_LINK_LENS_METADATA_PORT, our_queue,
                               poke_seconds=QUEUE_PEEK_INTERVAL)
    mrt.message = 'B,0.2,F,0.8,T,0.0'
    mrt.start()

