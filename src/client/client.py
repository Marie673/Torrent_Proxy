#!/usr/bin/env python3.9
import torrent
import pieces_manager
import cefapp

import os
import sys
import time
import logging
from multiprocessing import Process
import numpy

PROTOCOL = 'ccnx:/BitTorrent'
MAX_PROCESS = 5


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
        process = []
        works = self.torrent.number_of_pieces // MAX_PROCESS

        for process_index in range(MAX_PROCESS):
            interests = []
            pieces = []
            for index in range(process_index*works, works):
                interest = '/'.join([PROTOCOL, self.info_hash, str(index+0)])
                interests.append(interest)
                pieces.append(self.pieces_manager.pieces[index])
            time.sleep(1)

            app = cefapp.CefAppConsumer(interests, pieces)
            app.start()
            process.append(app)

        for runner in process:
            runner.join()
            runner.close()

        logging.info("File(s) downloaded successfully.")
        end_time = time.time() - start_time
        self.display_progression()
        print("time: {0}".format(end_time) + "[sec]")

        self._exit_threads()

    def display_progression(self):

        current_log_line = "{}/{} pieces" \
            .format(self.pieces_manager.complete_pieces,
                    self.pieces_manager.number_of_pieces)
        if current_log_line != self.last_log_line:
            print(current_log_line)

        self.last_log_line = current_log_line

    def _exit_threads(self):
        exit(0)

    def get_empty_port(self):
        for i in range(MAX_PIECE):
            port = i + self.default_port
            if port not in self.process:
                return port

        return None

    def wait_empty_port(self):
        while True:
            for i in range(MAX_PIECE):
                port = i + self.default_port
                process: Process = self.process[port]
                if process.is_alive():
                    continue
                else:
                    self.process[port].join()
                    # self.process[port].close()
                    del self.process[port]
                    return port
            time.sleep(0.1)


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
