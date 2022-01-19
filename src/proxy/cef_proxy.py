import logging
import sys

import cefore_manager


class Run(object):
    def __init__(self):
        self.torrent = None

        self.cef_manager = cefore_manager.CefManager()
        self.handle = self.cef_manager.cef.handle

    def start(self):
        self.cef_manager.run()


def main():
    run = Run()
    try:
        run.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
