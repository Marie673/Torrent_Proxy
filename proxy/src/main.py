import os
import sys
sys.path.append(os.pardir)
from lib import peers_manager, pieces_manager, cefore_manager
from multiprocessing import Event, Queue, Lock


def main():
    peers_m = peers_manager.PeersManager()
    pieces_m = pieces_manager.PiecesManager()
    cefore_m = cefore_manager.CeforeManager()

    peers_m.start()
    pieces_m.start()
    cefore_m.start()

    try:
        input('Enterキーを押したら終了します。\n')
        peers_m.shutdown()
        pieces_m.shutdown()
        cefore_m.shutdown()

        peers_m.join()
        pieces_m.join()
        cefore_m.join()

        return

    except KeyboardInterrupt:
        peers_m.shutdown()
        pieces_m.shutdown()
        cefore_m.shutdown()

        peers_m.join()
        pieces_m.join()
        cefore_m.join()

        exit(0)


if __name__ == '__main__':
    main()
