import sys
import time
import logging
import os
from multiprocessing import Queue

from block import State
import peers_manager
import pieces_manager
import torrent
import tracker
import message

sys.setcheckinterval(10)


class Run(object):
    percentage_completed = -1
    last_log_line = ""

    def __init__(self, path):
        self.path = path
        self.torrent = torrent.Torrent().load_from_path(self.path)
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.peers_manager.start()
        logging.info("PeersManager Started")
        logging.info("PiecesManager Started")

    def start(self):
        start_time = prog_time = time.time()
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        while not self.pieces_manager.all_pieces_completed():
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                logging.info("No unchocked peers")
                continue

            for index in range(self.pieces_manager.number_of_pieces):
                piece = self.pieces_manager.pieces[index]

                if self.pieces_manager.pieces[index].is_full:
                    continue

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
                    time.sleep(0.0001)

                    now_time = time.time()
                    if (now_time - prog_time) > 1:
                        text = "------------------------------------------------------------\n" + \
                               str(now_time - start_time) + "[sec]\n" + \
                               str(self.pieces_manager.bitfield[:10000]) + '\n' + \
                               "------------------------------------------------------------\n"
                        print(text)
                        prog_time = now_time

        logging.info("File(s) downloaded successfully.")
        self.display_progression()
        end_time = time.time() - start_time
        print("time: {0}".format(end_time) + "[sec]")

        self._exit_threads()

    def display_progression(self):
        new_progression = 0

        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j].state == State.FULL:
                    new_progression += len(self.pieces_manager.pieces[i].blocks[j].data)

        if new_progression == self.percentage_completed:
            return

        number_of_peers = self.peers_manager.unchoked_peers_count()
        percentage_completed = float((float(new_progression) / self.torrent.total_length) * 100)

        current_log_line = "Connected peers: {} - {}% completed | {}/{} pieces" \
            .format(number_of_peers,
                    round(percentage_completed, 2),
                    self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line
        self.percentage_completed = new_progression

    def _exit_threads(self):
        self.peers_manager.is_active = False
        os._exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    args = sys.argv
    path = args[1]
    path = os.path.abspath(path)

    run = Run(path)
    run.start()
