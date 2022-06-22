from multiprocessing import Process

from piece

import yaml
import logging.config
from logging import getLogger
log_config = 'config.yaml'
logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
logger = getLogger('develop')


class PiecesManager(Process):
    def __init__(self):
        super().__init__()
        self.peers_m = None
        self.cefore_m = None

    def run(self) -> None:
        logger.info('Process Pieces Manager is start')

        try:
            while True:
                self.loop()
        except KeyboardInterrupt:
            logger.info('Exit Process')
            return

    def loop(self):
        pass


