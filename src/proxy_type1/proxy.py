import logging
import os.path
import sys

import cefore_manager
import torrent

class Run(object):
    def __init__(self, path):
        self.torrent = torrent.Torrent().load_from_path(path)

        self.cef_manager = cefore_manager.CefManager(torrent)
        self.handle = self.cef_manager.cef.handle

    def start(self):
        self.cef_manager.run()


def main():

    path = os.path.abspath(path)
    run = Run(path)
    try:
        run.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
