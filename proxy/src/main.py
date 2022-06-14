from lib import peers_manager, pieces_manager, cefore_manager

from logging import getLogger, StreamHandler, Formatter, DEBUG
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    peers_m = peers_manager.PeersManager()
    pieces_m = pieces_manager.PiecesManager()
    cefore_m = cefore_manager.CeforeManager()
    logger.info("Processes are created")

    peers_m.pieces_m = pieces_m
    peers_m.cefore_m = cefore_m

    pieces_m.peers_m = peers_m
    pieces_m.cefore_m = cefore_m

    cefore_m.peers_m = peers_m
    cefore_m.piece_m = pieces_m

    logger.info("Processes start")
    peers_m.start()
    pieces_m.start()
    cefore_m.start()
    logger.debug("Peers Manager PID: {}".format(peers_m.pid))
    logger.debug("Pieces Manager PID: {}".format(pieces_m.pid))
    logger.debug("Cefore Manager PID: {}".format(cefore_m.pid))

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
    main()

