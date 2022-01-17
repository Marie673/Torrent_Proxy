import time
import torrent
import tracker
import peers_manager
import pieces_manager
import message
import block
import logging

DEFAULT_TORRENT_FILE = "/home/marie673/Project/Torrent_proxy/test/ubuntu-20.04.3-desktop-amd64.iso.torrent"


class Run(object):
    percentage_completed = -1
    last_log_line = ""

    def __init__(self, torrent_file=DEFAULT_TORRENT_FILE):
        self.torrent = torrent.Torrent().load_from_path(torrent_file)
        self.tracker = tracker.Tracker(self.torrent)

        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.peers_manager.start()

    def start(self):
        peers_dict = self.tracker.get_peers_from_trackers()
        self.peers_manager.add_peers(peers_dict.values())

        while True:
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(1)
                logging.info("No unchoked peers")
                continue
            # index 0　のピースを取得
            piece = self.pieces_manager.pieces[0]
            index = piece.piece_index

            if self.pieces_manager.pieces[index].is_full:
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
            print(piece_data)
            peer.send_to_peer(piece_data)

        self.display_progression()
        time.sleep(0.1)

        logging.info("successfully")
        self._exit_threads()

    def display_progression(self):
        new_progression = 0

        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j].state == block.State.FULL:
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
        exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    run = Run()
    run.start()
