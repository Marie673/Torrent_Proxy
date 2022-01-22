from block import State
import time
import peers_manager
import pieces_manager
import torrent
import tracker
import logging
import message
from multiprocessing import Process, Queue


PATH = ["/home/marie/Torrent_Proxy/test/1M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/100M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/1G.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10G.dummy.torrent"]
BITFIELD = 0
PIECES = 1


class Run(Process):
    percentage_completed = -1

    def __init__(self, queue, jikken):
        Process.__init__(self)
        self.torrent = torrent.Torrent().load_from_path(PATH[jikken])
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.request_q: Queue = queue[0]
        self.piece_q: Queue = queue[1]

        logging.info("PiecesManager Started")

    def run(self):
        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        while True:
            if self.request_q.empty():
                continue
            else:
                index = self.request_q.get()

            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                continue

            if self.pieces_manager.pieces[index].is_full:
                piece = [index, self.pieces_manager.pieces[index].raw_data]
                self.piece_q.put(piece)
                continue

            while not self.pieces_manager.pieces[index].is_full:
                peer = self.peers_manager.get_random_peer_having_piece(index)
                if not peer:
                    time.sleep(1)
                    continue

                self.pieces_manager.pieces[index].update_block_status()
                data = self.pieces_manager.pieces[index].get_empty_block()
                if not data:
                    continue
                piece_index, block_offset, block_length = data
                piece_data = message.Request(piece_index, block_offset, block_length).to_bytes()
                peer.send_to_peer(piece_data)

            piece = [index, self.pieces_manager.pieces[index].raw_data]
            self.piece_q.put(piece)
