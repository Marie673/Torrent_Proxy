#!/usr/bin/env python3.9
import torrent
import pieces_manager
import cefpyco
import cefapp

import os
import sys
import time
import logging


PROTOCOL = 'ccnx:/BitTorrent'
MAX_PIECE = 10


class Run(object):
    percentage_completed = -1
    last_log_line = ""

    def __init__(self, torrent_file_path):
        self.torrent = torrent.Torrent().load_from_path(torrent_file_path)
        self.info_hash = str(self.torrent.info_hash.hex())
        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)

        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()

        logging.info('Cefore Manager Started')
        logging.info("PiecesManager Started")

    def start(self):
        start_time = time.time()
        while not self.pieces_manager.all_pieces_completed():
            # logging.debug('start request pieces')
            for piece in self.pieces_manager.pieces:
                index = piece.piece_index

                if self.pieces_manager.pieces[index].is_full:
                    continue

                self.pieces_manager.pieces[index].update_block_status()

                self.pieces_manager.pieces[index].update_block_status()

                interest = '/'.join([PROTOCOL, self.info_hash, str(index)])
                app = cefapp.CefAppConsumer(self.handle)
                state = app.run(interest)
                self.display_progression()
                """
                if not self.req_piece_flg[index]:
                    interest = '/'.join([PROTOCOL, self.info_hash, str(index)])
                    cef = cefapp.CefAppConsumer(self.handle)
                    thread = Thread(target=cef.run, args=interest)
                    thread.start()
                    self.req_piece_flg[index] = True
                """

            if self.pieces_manager.all_pieces_completed():
                break
            self.display_progression()

            #time.sleep(3)

        logging.info("File(s) downloaded successfully.")
        end_time = time.time() - start_time
        self.display_progression()
        print("time: {0}".format(end_time) + "[sec]")

        self._exit_threads()

    def display_progression(self):
        """
        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j].state == State.FULL:
                    new_progression += len(self.pieces_manager.pieces[i].blocks[j].data)
        if new_progression == self.percentage_completed:
            return"""

        # percentage_completed = float((float(new_progression) / self.torrent.total_length) * 100)

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line

    def _exit_threads(self):
        exit(0)


def main():
    args = sys.argv
    if len(args) != 2:
        print('Usage: {} torrent_file'.format(args[0]))
        exit(1)

    path = args[1]
    if not os.path.isfile(path):
        print('{} is not found.'.format(path))
        exit(1)

    path = os.path.abspath(path)

    run = Run(path)
    try:
        run.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
