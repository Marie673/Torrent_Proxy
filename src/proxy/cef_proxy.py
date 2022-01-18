import cefore_manager


class Run(object):
    def __init__(self):
        self.torrent = None

        self.cef_manager = cefore_manager.CefManager()
        self.handle = self.cef_manager.cef.handle
        self.pieces_manager = {}

    def start(self):
        self.cef_manager.start()


def main():
    run = Run()
    run.start()


if __name__ == '__main__':
    main()
