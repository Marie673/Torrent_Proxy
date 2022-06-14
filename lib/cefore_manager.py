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


class CeforeManager(Process):
    def __init__(self):
        super().__init__()
        self.piece_m = None
        self.peers_m = None

    def run(self) -> None:
        logger.info('Process Cefore Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            exit()

    def loop(self):
        logger.info('{}'.format(self.pid))
        time.sleep(3)
