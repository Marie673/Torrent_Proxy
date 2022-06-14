import sys
import time
from multiprocessing import Process, Event

from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False


class CeforeManager(Process):
    def __init__(self):
        super().__init__()
        self.exit = Event()

    def run(self) -> None:
        while not self.exit.is_set():
            print("test cef")
            time.sleep(2)
        logger.info("Cefore Manager is down")
        logger.debug("PID: {}".format(self.pid))

        sys.exit()

    def shutdown(self):
        self.exit.set()
