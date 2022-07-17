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

    def __init__(self, torrent):
        Process.__init__(self)
        self.torrent = torrent
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        logging.info("PiecesManager Started")

    def run(self):
        os.makedirs("tmp/" + self.torrent.info_hash_str, exist_ok=True)

        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        prog_time = time.time()
        while True:
            if not self.peers_manager.has_unchoked_peers():
                # self.peers_manager.add_peers(peers_dict.values())
                time.sleep(1)
                continue

            """"
            while not self.request_q.empty():
                request_index = self.request_q.get()
                if request_index in self.request:
                    continue
                self.request.append(request_index)
            """

            for piece in self.pieces_manager.pieces:
                # print(self.request)
                if piece.is_full:
                    continue

                for i in range(piece.number_of_blocks):
                    peer = self.peers_manager.get_random_peer_having_piece(piece.piece_index)
                    if not peer:
                        continue

                    piece.update_block_status()

                    data = piece.get_empty_block()
                    if not data:
                        continue
                    piece_index, block_offset, block_length = data
                    piece_data = message.Request(piece_index, block_offset, block_length).to_bytes()
                    peer.send_to_peer(piece_data)
                    time.sleep(0.001)
                    now_time = time.time()
                    if (now_time - prog_time) > 1:
                        text = "--------------------------------------------------------------------------\n" + \
                               self.pieces_manager.str_bitfield() + '\n' + \
                               "------------------------------------------------------------------------------"
                        print(text)
                        prog_time = now_time
