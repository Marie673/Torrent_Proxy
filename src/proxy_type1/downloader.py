from block import State
import time
import peers_manager
import pieces_manager
from piece import Piece
import tracker
import logging
import message
from multiprocessing import Process, Queue
import os


class Run(Process):
    percentage_completed = -1

    def __init__(self, torrent, queue):
        Process.__init__(self)
        self.torrent = torrent
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.request_q: Queue = queue[0]
        self.piece_q: Queue = queue[1]

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
                tmp_path = '/'.join(["tmp", self.torrent.info_hash_str, str(request_index)])
                if os.path.exists(tmp_path):
                    if request_index in self.request:
                        self.request.remove(request_index)
                    continue
                if request_index in self.request:
                    continue
                self.request.append(request_index)

            for index in self.request:
                # print(self.request)
                tmp_path = '/'.join(["tmp", self.torrent.info_hash_str, str(index)])
                if os.path.exists(tmp_path):
                    self.request.remove(index)
                    continue

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

            time.sleep(0.01)

    def display_progression(self):
        new_progression = 0

        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j].state == State.FULL:
                    new_progression += len(self.pieces_manager.pieces[i].blocks[j].data)

        if new_progression == self.percentage_completed:
            return

        self.percentage_completed = new_progression