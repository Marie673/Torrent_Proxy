import time
from multiprocessing import Process

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


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
            return

    def loop(self):
        logger.info('{}'.format(self.pid))
        time.sleep(3)
