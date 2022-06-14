import sys
import time
from multiprocessing import Process, Event

from logging import getLogger, StreamHandler, Formatter, DEBUG
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TestManager(Process):
    def __init__(self):
        super().__init__()
        self.exit = Event()

    def run(self) -> None:
        logger.info('Process Test Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info("Cefore Manager is down")
            exit()

    def shutdown(self):
        self.exit.set()

    def loop(self):
        logger.info("{}".format(self.pid))
        time.sleep(1)
