import logging
import time
from multiprocessing import Process, Event


class CeforeManager(Process):
    def __init__(self):
        super().__init__()
        self.exit = Event()

    def run(self) -> None:
        while not self.exit.is_set():
            print("test cef")
            time.sleep(2)
        logging.debug("manager is down")

    def shutdown(self):
        self.exit.set()
