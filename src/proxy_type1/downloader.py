import time
import logging
from multiprocessing import Process, Queue
import os

import peers_manager
import pieces_manager
import tracker
import message



CHUNK_SIZE = 1024 * 4
MAX_PIECE = 50


class Run(Process):
    percentage_completed = -1

    def __init__(self, torrent, request_q):
        Process.__init__(self)
        self.torrent = torrent
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.request_q: Queue = request_q
        self.request = []

        logging.info("PiecesManager Started")

    def run(self):
        os.makedirs("tmp/" + self.torrent.info_hash_str, exist_ok=True)

        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        while True:
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                continue

            while not self.request_q.empty():
                request_index = self.request_q.get()
                if request_index in self.request:
                    continue
                self.request.append(request_index)

            for index in self.request[:MAX_PIECE]:
                # print(self.request)
                piece = self.pieces_manager.pieces[index]
                if piece.is_full:
                    self.request.remove(index)

                for i in range(piece.number_of_blocks):
                    peer = self.peers_manager.get_random_peer_having_piece(index)
                    if not peer:
                        continue

                    self.pieces_manager.pieces[index].update_block_status()

                    data = self.pieces_manager.pieces[index].get_empty_block()
                    if not data:
                        continue
                    piece_index, block_offset, block_length = data
                    piece_data = message.Request(piece_index, block_offset, block_length).to_bytes()
                    peer.send_to_peer(piece_data)

                time.sleep(0.02)
