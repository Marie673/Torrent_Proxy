from block import State
import time
import peers_manager
import pieces_manager
import torrent
import tracker
import logging
import os
import message
from multiprocessing import Process, managers


PATH = ["/home/marie/Torrent_Proxy/test/1M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/100M.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/1G.dummy.torrent",
        "/home/marie/Torrent_Proxy/test/10G.dummy.torrent"]
BITFIELD = 0
PIECES = 1


class Run(Process):
    percentage_completed = -1
    last_log_line = ""


    def __init__(self, m_list, jikken):
        Process.__init__(self)
        self.torrent = torrent.Torrent().load_from_path(PATH[jikken])
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.m_list = m_list
        bitfield = [False for _ in range(self.pieces_manager.number_of_pieces)]
        self.m_list[0] = bitfield

        logging.info("PiecesManager Started")

    def run(self):
        self.peers_manager.start()
        logging.info("PeersManager Started")
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        start_time = time.time()

        while not self.pieces_manager.all_pieces_completed():
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                logging.info("No unchocked peers")
                continue

            for piece in self.pieces_manager.pieces:
                index = piece.piece_index

                if self.pieces_manager.pieces[index].is_full:
                    bitfield = self.m_list[BITFIELD]
                    if not bitfield[index]:
                        bitfield[index] = True
                        self.m_list[BITFIELD] = bitfield
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

            self.display_progression()

            time.sleep(0.1)

        bitfield = [True for _ in range(self.pieces_manager.number_of_pieces)]
        for index in range(self.pieces_manager.number_of_pieces):
            if not self.m_list[BITFIELD][index]:
                self.m_list[BITFIELD] = bitfield
                pieces = self.m_list[PIECES]
                pieces[index] = self.pieces_manager.pieces[index].raw_data
                self.m_list[PIECES] = pieces

        logging.info("File(s) downloaded successfully.")
        end_time = time.time() - start_time
        print("time: {0}".format(end_time) + "[sec]")
        self.display_progression()
        time.sleep(300)
        # self._exit_threads()

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

