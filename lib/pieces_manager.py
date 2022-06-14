import logging
import time
from multiprocessing import Process, Event


class PiecesManager(Process):
    def __init__(self):
        super().__init__()
        self.exit = Event()

    def run(self) -> None:
        while not self.exit.is_set():
            print("test piece")
            time.sleep(2)
        logging.debug("manager is down")

    def shutdown(self):
        self.exit.set()
