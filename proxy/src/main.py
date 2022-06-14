import logging
import os
import sys
sys.path.append(os.pardir)
from multiprocessing import Event, Queue, Lock

from logging import getLogger, StreamHandler, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

from lib import peers_manager, pieces_manager, cefore_manager


def main():
    peers_m = peers_manager.PeersManager()
    pieces_m = pieces_manager.PiecesManager()
    cefore_m = cefore_manager.CeforeManager()
    logger.info("Processes are created")

    logger.info("Processes start")
    peers_m.start()
    pieces_m.start()
    cefore_m.start()
    logger.debug("Peers Manager PID: {}".format(peers_m.pid))
    logger.debug("Pieces Manager PID: {}".format(pieces_m.pid))
    logger.debug("Cefore Manager PID: {}".format(cefore_m.pid))

    try:
        input('Enterキーを押したら終了します。\n')
        peers_m.shutdown()
        pieces_m.shutdown()
        cefore_m.shutdown()

        peers_m.join()
        pieces_m.join()
        cefore_m.join()

        logger.info("All Process is down")

    except KeyboardInterrupt:
        peers_m.shutdown()
        pieces_m.shutdown()
        cefore_m.shutdown()

        peers_m.join()
        pieces_m.join()
        cefore_m.join()

        exit(0)

    logger.info("exit")


if __name__ == '__main__':
    main()
