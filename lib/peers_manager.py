import time
from multiprocessing import Process

from logging import getLogger, StreamHandler, Formatter, DEBUG
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class PeersManager(Process):
    def __init__(self):
        super().__init__()
        self.pieces_m = None
        self.cefore_m = None

    def run(self) -> None:
        logger.info('Process Peers Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            exit()

    def loop(self):
        logger.info('{}'.format(self.pid))
        time.sleep(3)
