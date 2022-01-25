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
