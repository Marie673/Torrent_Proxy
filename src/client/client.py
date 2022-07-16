#!/usr/bin/env python3.9
import torrent
import pieces_manager
import cefapp

import os
import sys
import time
import logging
import numpy

PROTOCOL = 'ccnx:/BitTorrent'


class Run(object):
    percentage_completed = -1
    last_log_line = ""

    def __init__(self, torrent_file_path):
        self.torrent = torrent.Torrent().load_from_path(torrent_file_path)
        self.info_hash = str(self.torrent.info_hash.hex())
        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)

        self.req_flg = numpy.zeros(self.torrent.number_of_pieces)
        self.default_port = 9896
        logging.info('Cefore Manager Started')
        logging.info("PiecesManager Started")

    def start(self):
        start_time = time.time()
        # logging.debug('start request pieces')

        consumer = cefapp.CefAppConsumer(self.pieces_manager)
        consumer.run()

        logging.info("File(s) downloaded successfully.")
        end_time = time.time() - start_time
        print("time: {0}".format(end_time) + "[sec]")

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line


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
