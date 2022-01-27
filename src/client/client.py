#!/usr/bin/env python3.9
import torrent
import pieces_manager
from block import State
import cefore_manager
import cefpyco
import cefapp

import os
import sys
import time
import logging
from threading import Thread, Event
from multiprocessing import Process


PROTOCOL = 'ccnx:/BitTorrent'
MAX_PIECE = 3


class Run(object):
    percentage_completed = -1
    last_log_line = ""

    def __init__(self, torrent_file_path):
        self.torrent = torrent.Torrent().load_from_path(torrent_file_path)
        self.info_hash = str(self.torrent.info_hash.hex())
        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)

        self.handle = cefpyco.CefpycoHandle()
        self.handle.begin()
        listener = Process(target=self.listener)
        listener.start()

        self.thread = {}

        logging.info('Cefore Manager Started')
        logging.info("PiecesManager Started")

    def listener(self):
        packet  = self.handle.receive()
        index = int(packet.name.split('/')[-1])
        self.thread[index].packet = packet
        self.thread[index].event.clear()

    def start(self):
        try:
            start_time = time.time()
            while not self.pieces_manager.all_pieces_completed():
                # logging.debug('start request pieces')
                for piece in self.pieces_manager.pieces:
                    index = piece.piece_index

                    if self.pieces_manager.pieces[index].is_full:
                        continue

                    if index in self.thread:
                        thread: Thread = self.thread[index]
                        if thread.is_alive():
                            continue
                        else:
                            del self.thread[index]

                    if len(self.thread) > MAX_PIECE:
                        continue
                    interest = '/'.join([PROTOCOL, self.info_hash, str(index)])
                    event = Event()
                    app = cefapp.CefAppConsumer(self.handle, interest, event)
                    self.thread[index] = app
                    app.start()
                    print(interest)

                if self.pieces_manager.all_pieces_completed():
                    break
                self.display_progression()

                #time.sleep(3)

            logging.info("File(s) downloaded successfully.")
            end_time = time.time() - start_time
            self.display_progression()
            print("time: {0}".format(end_time) + "[sec]")

            self._exit_threads()

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
            print("Stopping threads")
            for index in self.thread:
                self.thread[index].active = False
                self.thread[index].join()

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
    run.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
