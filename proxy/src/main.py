from lib import cefore_manager
from lib.peer import peers_manager
from lib.piece import pieces_manager
import yaml

import logging.config
from logging import getLogger

log_config = 'config.yaml'


def main():
    logger = getLogger('develop')

    peers_m = peers_manager.PeersManager()
    pieces_m = pieces_manager.PiecesManager()
    cefore_m = cefore_manager.CeforeManager()
    logger.info("Processes are created")

    logger.info("Pro cesses start")
    peers_m.start()
    pieces_m.start()
    cefore_m.start()
    logger.debug("Peers Manager PID: {}".format(peers_m.pid))
    logger.debug("Pieces Manager PID: {}".format(pieces_m.pid))
    logger.debug("Cefore Manager PID: {}".format(cefore_m.pid))

    peers_m.pieces_m = pieces_m
    peers_m.cefore_m = cefore_m

    pieces_m.peers_m = peers_m
    pieces_m.cefore_m = cefore_m

    cefore_m.peers_m = peers_m
    cefore_m.piece_m = pieces_m

    try:
        while True:
            pass

    except KeyboardInterrupt:
        peers_m.join()
        pieces_m.join()
        cefore_m.join()

        logger.info("All Process is down")

    logger.info("exit")


if __name__ == '__main__':
    logging.config.dictConfig(yaml.load(open(log_config).read(), Loader=yaml.SafeLoader))
    main()

