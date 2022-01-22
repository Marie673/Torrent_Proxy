import logging
import os.path
import sys

import cefore_manager


class Run(object):
    def __init__(self, jikken):

        self.cef_manager = cefore_manager.CefManager(jikken)
        self.handle = self.cef_manager.cef.handle

    def start(self):
        self.cef_manager.run()


def main():
    args = sys.argv
    jikken = int(args[1])

    run = Run(jikken)
    try:
        run.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
