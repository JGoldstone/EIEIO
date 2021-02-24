import socket
import queue
from threading import Thread

LIVE_LINK_LENS_METADATA_PORT = 40123
QUEUE_PEEK_INTERVAL = 3


class MessageRetransmitter(Thread):
    def __init__(self, message_queue):
        super().__init__()
        self.message_queue = message_queue
        self.message = ''
        self.interval = 3  # seconds
        self.host = '192.168.1.157'
        self.port = LIVE_LINK_LENS_METADATA_PORT
        self.transmission_thread = None

    def server_address(self):
        return self.host, self.port

    def loop_transmitting_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as local_socket:
            local_socket.settimeout(3.0)
            while True:
                print("in thread, in loop")
                terminated_message = f"{self.message}\r\n"
                print(f"thread sent {self.message}")
                bytes_sent = local_socket.sendto(terminated_message.encode(), self.server_address())
                print(f"{bytes_sent} bytes sent by thread")
                try:
                    self.message = self.message_queue.get(timeout=QUEUE_PEEK_INTERVAL)
                    if self.message == "exit":
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
    mrt = MessageRetransmitter(our_queue)
    mrt.message = 'B0.2F0.8T0.0'
    mrt.start()

