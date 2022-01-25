from block import State
import time
import peers_manager
import pieces_manager
import tracker
import logging
import message
from multiprocessing import Process, Queue
from threading import Thread


BITFIELD = 0
PIECES = 1


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

    def queue_manager(self):
        while True:
            if self.request_q.empty():
                continue

            index = self.request_q.get()
            if index in self.request:
                continue
            else:
                self.request.append(index)


    def run(self):
        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        q_thread = Thread(target=self.queue_manager)
        q_thread.start()

        while True:
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                continue

            for index in self.request:
                if self.pieces_manager.pieces[index].is_full:
                    piece = [index, self.pieces_manager.pieces[index].raw_data]
                    self.piece_q.put(piece)
                    self.request.remove(index)
                    del self.pieces_manager.pieces[index].raw_data
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

            time.sleep(0.00001)

    def display_progression(self):
        new_progression = 0

        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j].state == State.FULL:
                    new_progression += len(self.pieces_manager.pieces[i].blocks[j].data)

        if new_progression == self.percentage_completed:
            return

        self.percentage_completed = new_progression