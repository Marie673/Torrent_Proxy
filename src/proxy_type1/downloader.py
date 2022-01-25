from block import State
import time
import peers_manager
import pieces_manager
import tracker
import logging
import message
from multiprocessing import Process, Queue
import cefpyco

BITFIELD = 0
PIECES = 1

CHUNK_SIZE = 1024 * 4


class Run(Process):
    percentage_completed = -1

    def __init__(self, torrent, queue):
        Process.__init__(self)
        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()

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

    def send_data(self, piece):
        index, payload = piece
        name = 'ccnx:/BitTorrent/' + self.torrent.info_hash_str + '/' + str(index)
        cache_time = 360000
        end_chunk_num = len(payload) // CHUNK_SIZE

        while payload:
            chunk = payload[:CHUNK_SIZE]
            self.handle.send_data(name=name, payload=payload,
                    chunk_num=chunk, end_chunk_num=end_chunk_num, cache_time=cache_time)
            payload = payload[CHUNK_SIZE:payload]


    def run(self):
        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        while True:
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                continue

            if not self.request_q.empty():
                request_index = self.request_q.get()
                if request_index not in self.request:
                    self.request.append(request_index)
                    print("get new request: {}".format(request_index))

            for index in self.request:
                if self.pieces_manager.pieces[index].is_full:
                    piece = [index, self.pieces_manager.pieces[index].raw_data]
                    self.send_data(piece)
                    self.request.remove(index)
                    del self.pieces_manager.pieces[index].raw_data
                    print("complete piece: {}".format(index))
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
                if piece_index == 0:
                    print("download piece: {}".format(piece_index))
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